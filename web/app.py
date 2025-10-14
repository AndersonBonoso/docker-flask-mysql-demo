import os
import re
from datetime import timedelta
from functools import wraps
from pathlib import Path
from typing import Optional

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
    jsonify,
)
import mysql.connector
from mysql.connector import errorcode, IntegrityError
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

# ----------------------------
# Config
# ----------------------------
DB_CFG = {
    "host": os.environ.get("DB_HOST", "db"),
    "port": int(os.environ.get("DB_PORT", "3306")),
    "database": os.environ.get("DB_NAME", "teste"),
    "user": os.environ.get("DB_USER", "app"),
    "password": os.environ.get("DB_PASSWORD", "app123"),
    "autocommit": True,
}

SECRET_KEY = os.environ.get("SECRET_KEY", "troque-isto")

BASE_DIR = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)
app.secret_key = SECRET_KEY
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

# Segurança de sessão e no-cache para evitar histórico em páginas protegidas
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    # Em produção/HTTPS ative:
    # SESSION_COOKIE_SECURE=True,
)


@app.after_request
def add_no_cache_headers(response):
    """
    Evita que páginas fiquem em cache no histórico do navegador.
    Assim, após logout, o botão Voltar não mostra conteúdo protegido.
    """
    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, max-age=0"
    )
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ----------------------------
# DB helpers
# ----------------------------


def get_conn():
    """Retorna uma conexão com o MySQL."""
    return mysql.connector.connect(**DB_CFG)


def init_db():
    """Cria a tabela users se não existir (InnoDB, utf8mb4)."""
    ddl = """
    CREATE TABLE IF NOT EXISTS users (
        id BIGINT NOT NULL AUTO_INCREMENT,
        full_name VARCHAR(120) NOT NULL,
        username VARCHAR(50) NOT NULL,
        email VARCHAR(120) NOT NULL,
        phone_e164 VARCHAR(20) NULL,
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        UNIQUE KEY uq_users_username (username),
        UNIQUE KEY uq_users_email (email)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
      COLLATE=utf8mb4_unicode_ci;
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(ddl)
    finally:
        conn.close()

# ----------------------------
# Validadores / Normalização
# ----------------------------


EMAIL_RE = re.compile(
    r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"
)


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match((email or "").strip()))


def password_policy_ok(pw: str) -> bool:
    """
    Política:
    - mínimo 8
    - 1 maiúscula, 1 minúscula, 1 dígito, 1 especial
    """
    if not pw or len(pw) < 8:
        return False
    if not re.search(r"[A-Z]", pw):
        return False
    if not re.search(r"[a-z]", pw):
        return False
    if not re.search(r"\d", pw):
        return False
    if not re.search(r"[^\w\s]", pw):
        return False
    return True


def normalize_phone_e164(phone_raw: str) -> Optional[str]:
    """
    Normaliza para E.164 sem libs externas.

    Regras:
      - remove tudo que não for dígito
      - se começar com '00', vira '+'
      - se começar com '0', remove o 0
      - prefixa '+' se não tiver
      - valida tamanho 8..15 dígitos
    """
    if not phone_raw:
        return None

    digits = re.sub(r"\D", "", phone_raw)

    if digits.startswith("00"):
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = digits[1:]

    if not (8 <= len(digits) <= 15):
        return None
    return f"+{digits}"

# ----------------------------
# Autenticação
# ----------------------------


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Faça login para continuar.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)

    return wrapper

# ----------------------------
# Rotas
# ----------------------------


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    full_name = (request.form.get("full_name") or "").strip()
    username = (request.form.get("username") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    phone = (request.form.get("phone") or "").strip()
    password = request.form.get("password") or ""
    confirm = request.form.get("confirm_password") or ""

    errors = []
    if not full_name:
        errors.append("Nome completo é obrigatório.")
    if not username:
        errors.append("Username é obrigatório.")
    if not is_valid_email(email):
        errors.append("E-mail inválido.")
    if password != confirm:
        errors.append("Confirmação de senha não confere.")
    if not password_policy_ok(password):
        errors.append(
            "Senha não atende à política "
            "(mín. 8, 1 maiúscula, 1 minúscula, 1 dígito, 1 especial)."
        )

    phone_e164 = normalize_phone_e164(phone) if phone else None
    if phone and phone_e164 is None:
        errors.append(
            "Telefone inválido. Informe DDI+DDD e número "
            "(ex.: +5511912345678)."
        )

    if errors:
        for e in errors:
            flash(e, "danger")
        return render_template(
            "signup.html",
            full_name=full_name,
            username=username,
            email=email,
            phone=phone,
        )

    pw_hash = generate_password_hash(password)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            sql = (
                "INSERT INTO users "
                "(full_name, username, email, phone_e164, password_hash) "
                "VALUES (%s, %s, %s, %s, %s)"
            )
            cur.execute(sql, (full_name, username, email, phone_e164, pw_hash))
        flash("Conta criada com sucesso! Faça login.", "success")
        return redirect(url_for("login"))
    except IntegrityError as ex:
        if getattr(ex, "errno", None) == errorcode.ER_DUP_ENTRY:
            msg = str(ex.msg).lower()
            if (
                "uq_users_username" in msg
                or "for key 'uq_users_username'" in msg
                or "username" in msg
            ):
                flash("Este username já está em uso.", "danger")
            elif (
                "uq_users_email" in msg
                or "for key 'uq_users_email'" in msg
                or "email" in msg
            ):
                flash("Este e-mail já está em uso.", "danger")
            else:
                flash("Registro duplicado.", "danger")
            return render_template(
                "signup.html",
                full_name=full_name,
                username=username,
                email=email,
                phone=phone,
            )
        flash("Erro ao criar conta.", "danger")
        return render_template(
            "signup.html",
            full_name=full_name,
            username=username,
            email=email,
            phone=phone,
        )
    finally:
        conn.close()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    user_or_email = (request.form.get("user_or_email") or "").strip().lower()
    password = request.form.get("password") or ""

    if not user_or_email or not password:
        flash("Informe usuário/e-mail e senha.", "danger")
        return render_template("login.html", user_or_email=user_or_email)

    conn = get_conn()
    try:
        with conn.cursor(dictionary=True) as cur:
            sql = (
                "SELECT id, full_name, username, email, password_hash "
                "FROM users "
                "WHERE email = %s OR username = %s "
                "LIMIT 1"
            )
            cur.execute(sql, (user_or_email, user_or_email))
            row = cur.fetchone()

        if not row or not check_password_hash(row["password_hash"], password):
            flash("Credenciais inválidas.", "danger")
            return render_template("login.html", user_or_email=user_or_email)

        session.clear()
        session.permanent = True
        session["user_id"] = row["id"]
        session["username"] = row["username"]
        session["full_name"] = row["full_name"]
        flash("Login realizado com sucesso.", "success")
        return redirect(url_for("dashboard"))
    finally:
        conn.close()


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        full_name=session.get("full_name"),
        username=session.get("username"),
    )


@app.route("/logout")
def logout():
    session.clear()
    flash("Sessão encerrada.", "info")
    return redirect(url_for("index"))

# ----------------------------
# API auxiliar: checar username
# ----------------------------


@app.get("/api/check-username")
def api_check_username():
    """
    Exemplo: /api/check-username?u=anderson
    Retorno: {"available": true/false,
                "suggestion": "anderson1234" (opcional)}
    """
    username = (request.args.get("u") or "").strip()
    if not username:
        return jsonify({"available": False, "error": "username vazio"}), 400

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM users WHERE username=%s LIMIT 1", (username,)
            )
            exists = cur.fetchone() is not None

            if not exists:
                return jsonify({"available": True})

            # gera sugestão com 4 dígitos (primeira livre)
            for num in range(1000, 10000):
                sug = f"{username}{num}"
                cur.execute(
                    "SELECT 1 FROM users WHERE username=%s LIMIT 1", (sug,)
                )
                if cur.fetchone() is None:
                    return jsonify(
                        {"available": False, "suggestion": sug}
                    )
            return jsonify({"available": False})
    finally:
        conn.close()

# ----------------------------
# Inicialização (Flask 3)
# ----------------------------


def _init_on_import() -> None:
    """
    Inicializa a tabela users ao importar o módulo.
    Inclui tentativas para aguardar o MySQL (containers).
    """
    import sys
    import time

    attempts = 8
    delay_seconds = 2
    for i in range(attempts):
        try:
            init_db()
            print("DB inicializado (ou já existia).")
            return
        except Exception as exc:
            msg = (
                f"Tentativa {i + 1}/{attempts} aguardando DB... "
                f"({exc})"
            )
            print(msg, file=sys.stderr)
            time.sleep(delay_seconds)

    print(
        "Aviso: não foi possível inicializar a tabela após várias "
        "tentativas.",
        file=sys.stderr,
    )


_init_on_import()

if __name__ == "__main__":
    # Para rodar local (fora do Docker): python app.py
    app.run(host="0.0.0.0", port=5050)
