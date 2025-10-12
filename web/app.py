import os
from flask import Flask, request, jsonify
import mysql.connector

DB_CFG = {
    "host": os.environ.get("DB_HOST", "db"),
    "port": int(os.environ.get("DB_PORT", "3306")),
    "database": os.environ.get("DB_NAME", "teste"),
    "user": os.environ.get("DB_USER", "app"),
    "password": os.environ.get("DB_PASSWORD", "app123"),
}

app = Flask(__name__)

def get_conn():
    return mysql.connector.connect(
        host=DB_CFG["host"],
        port=DB_CFG["port"],
        database=DB_CFG["database"],
        user=DB_CFG["user"],
        password=DB_CFG["password"],
    )

@app.get("/health")
def health():
    return jsonify(ok=True), 200

@app.get("/users")
def list_users():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT user_id, user_name, user_username FROM tbl_user ORDER BY user_id")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(rows), 200

@app.post("/users")
def create_user():
    data = request.get_json(force=True)
    if not data or not data.get("name") or not data.get("username") or not data.get("password"):
        return {"error": "name, username and password are required"}, 400
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM tbl_user WHERE user_username=%s", (data["username"],))
    if cur.fetchone():
        cur.close(); conn.close()
        return {"message": "Username Exists !!"}, 409
    cur.execute(
        "INSERT INTO tbl_user (user_name, user_username, user_password) VALUES (%s, %s, %s)",
        (data["name"], data["username"], data["password"]),
    )
    conn.commit()
    cur.close(); conn.close()
    return {"message": "User Created"}, 201

# -------- rotas por ID --------
@app.get("/users/<int:user_id>")
def get_user(user_id):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT user_id, user_name, user_username FROM tbl_user WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if not row:
        return {"error": "User not found"}, 404
    return jsonify(row), 200

@app.put("/users/<int:user_id>")
def update_user(user_id):
    data = request.get_json(force=True) or {}
    if not any(k in data for k in ("name", "username", "password")):
        return {"error": "nothing to update"}, 400
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_name, user_username, user_password FROM tbl_user WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    if not row:
        cur.close(); conn.close()
        return {"error": "User not found"}, 404
    curr_name, curr_username, curr_password = row
    new_name = data.get("name", curr_name)
    new_username = data.get("username", curr_username)
    new_password = data.get("password", curr_password)
    cur.execute("SELECT 1 FROM tbl_user WHERE user_username=%s AND user_id<>%s", (new_username, user_id))
    if cur.fetchone():
        cur.close(); conn.close()
        return {"message": "Username Exists !!"}, 409
    cur.execute(
        "UPDATE tbl_user SET user_name=%s, user_username=%s, user_password=%s WHERE user_id=%s",
        (new_name, new_username, new_password, user_id),
    )
    conn.commit()
    cur.close(); conn.close()
    return {"message": "User Updated"}, 200

@app.delete("/users/<int:user_id>")
def delete_user(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM tbl_user WHERE user_id=%s", (user_id,))
    deleted = cur.rowcount
    conn.commit()
    cur.close(); conn.close()
    if deleted == 0:
        return {"error": "User not found"}, 404
    return "", 204

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
