import os, sqlite3, datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

DB_PATH = "catalog.db"
API_KEY = os.environ.get("API_KEY", "devkey")  # ponla en Render

app = Flask(__name__)
CORS(app)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL CHECK(price >= 0),
            stock INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        """)
init_db()

def require_key(func):
    # Decorador simple de API key
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-KEY")
        if key != API_KEY:
            return jsonify({"error":"unauthorized"}), 401
        return func(*args, **kwargs)
    return wrapper

@app.get("/health")
def health():
    return jsonify({"status":"ok","time":datetime.datetime.utcnow().isoformat()+"Z"})

@app.get("/metrics")
def metrics():
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) c FROM products").fetchone()["c"]
    return jsonify({"products": count})

@app.get("/products")
@require_key
def list_products():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.post("/products")
@require_key
def create_product():
    data = request.get_json(force=True)
    name  = (data.get("name") or "").strip()
    price = float(data.get("price", 0))
    stock = int(data.get("stock", 0))
    if not name or price < 0 or stock < 0:
        return jsonify({"error":"invalid-payload"}), 400
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO products(name, price, stock, created_at) VALUES(?,?,?,?)",
            (name, price, stock, datetime.datetime.utcnow().isoformat()+"Z")
        )
        pid = cur.lastrowid
        row = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    return jsonify(dict(row)), 201

@app.get("/products/<int:pid>")
@require_key
def get_product(pid):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    if not row: return jsonify({"error":"not-found"}), 404
    return jsonify(dict(row))

@app.put("/products/<int:pid>")
@require_key
def update_product(pid):
    data = request.get_json(force=True)
    with get_db() as conn:
        row = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        if not row: return jsonify({"error":"not-found"}), 404
        name  = (data.get("name") or row["name"]).strip()
        price = float(data.get("price", row["price"]))
        stock = int(data.get("stock", row["stock"]))
        if not name or price < 0 or stock < 0:
            return jsonify({"error":"invalid-payload"}), 400
        conn.execute("UPDATE products SET name=?, price=?, stock=? WHERE id=?",
                     (name, price, stock, pid))
        row = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    return jsonify(dict(row))

@app.delete("/products/<int:pid>")
@require_key
def delete_product(pid):
    with get_db() as conn:
        cur = conn.execute("DELETE FROM products WHERE id=?", (pid,))
        if cur.rowcount == 0:
            return jsonify({"error":"not-found"}), 404
    return jsonify({"deleted": pid})

if __name__ == "__main__":
    # Render asigna el puerto en $PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
