# -*- coding: utf-8 -*-
import os, time
from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error

DB_CFG = {
    "host": os.environ.get("DB_HOST", "db"),
    "port": int(os.environ.get("DB_PORT", "3306")),
    "database": os.environ.get("DB_NAME", "teste"),
    "user": os.environ.get("DB_USER", "app"),
    "password": os.environ.get("DB_PASSWORD", "app123"),
}

app = Flask(__name__)

def get_conn(retries=10, delay=2):
    last_err = None
    for _ in range(retries):
        try:
            return mysql.connector.connect(**DB_CFG)
        except Error as e:
            last_err = e
            time.sleep(delay)
    raise last_err

@app.get("/health")
def health():
    try:
        conn = get_conn(1); conn.close()
        return {"ok": True}, 200
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500

@app.get("/users")
def list_users():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT user_id, user_name, user_username FROM tbl_user ORDER BY user_id")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(rows)

@app.post("/users")
def create_user():
    data = request.get_json(force=True)
    name, username, password = data.get("name"), data.get("username"), data.get("password")
    if not all([name, username, password]):
        return {"error": "name, username e password sao obrigatorios"}, 400
    conn = get_conn(); cur = conn.cursor()
    cur.callproc("sp_createUser", [name, username, password])
    msg = "OK"
    for result in cur.stored_results():
        msg = result.fetchall()[0][0]
    conn.commit(); cur.close(); conn.close()
    return {"message": msg}, (201 if msg == "User Created" else 409)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
