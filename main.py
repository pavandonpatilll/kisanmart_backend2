from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sqlite3
import shutil
import json
import os
from datetime import datetime

date = datetime.now().strftime("%Y-%m-%d")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists("images"):
    os.makedirs("images")

app.mount("/images", StaticFiles(directory="images"), name="images")

# ---------------- DB CONNECTION ----------------

def get_conn():
    return sqlite3.connect("kisan_mart.db", timeout=10, check_same_thread=False)

# ---------------- INIT DB ----------------

def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")

    # PRODUCTS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER,
        category TEXT,
        image TEXT
    )
    """)

    # ORDERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        mobile TEXT,
        location TEXT,
        items TEXT,
        status TEXT
    )
    """)

    # ✅ ADD DATE COLUMN
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN created_at TEXT")
    except:
        pass

    conn.commit()
    conn.close()

init_db()

# ---------------- IMAGE UPLOAD ----------------

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        path = f"images/{file.filename}"
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"image": f"http://127.0.0.1:8000/{path}"}
    except Exception as e:
        return {"error": str(e)}

# ---------------- GET PRODUCTS ----------------

@app.get("/products")
def get_products():
    try:
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM products ORDER BY id DESC")
        rows = cursor.fetchall()

        products = []
        for r in rows:
            products.append({
                "id": r[0],
                "name": r[1],
                "price": r[2],
                "category": r[3],
                "image": r[4]
            })

        conn.close()
        return products

    except Exception as e:
        return {"error": str(e)}

# ---------------- ADD PRODUCT ----------------

@app.post("/add-product")
def add_product(data: dict):
    try:
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO products (name,price,category,image) VALUES (?,?,?,?)",
            (data.get("name"), data.get("price"), data.get("category"), data.get("image"))
        )

        conn.commit()
        conn.close()

        return {"message": "Product added"}

    except Exception as e:
        return {"error": str(e)}

# ---------------- DELETE PRODUCT ----------------

@app.delete("/delete-product/{id}")
def delete_product(id: int):
    try:
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM products WHERE id=?", (id,))
        conn.commit()
        conn.close()

        return {"message": "Deleted"}

    except Exception as e:
        return {"error": str(e)}

# ---------------- PLACE ORDER ----------------

@app.post("/order")
def place_order(data: dict):
    try:
        conn = get_conn()
        cursor = conn.cursor()

        name = data["farmer"]["name"]
        mobile = data["farmer"]["mobile"]
        location = data["farmer"]["location"]

        items = json.dumps(data["items"])

        # ✅ DATE SAVE
        created_at = datetime.now().strftime("%Y-%m-%d")

        cursor.execute(
            "INSERT INTO orders (name,mobile,location,items,status,created_at) VALUES (?,?,?,?,?,?)",
            (name, mobile, location, items, "Pending", created_at)
        )

        conn.commit()
        conn.close()

        return {"message": "Order placed"}

    except Exception as e:
        return {"error": str(e)}

# ---------------- GET ORDERS ----------------

@app.get("/orders")
def get_orders():
    try:
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM orders ORDER BY id DESC")
        rows = cursor.fetchall()

        orders = []
        for r in rows:
            orders.append({
                "id": r[0],
                "name": r[1],
                "mobile": r[2],
                "location": r[3],
                "items": json.loads(r[4]),
                "status": r[5],
                "date": r[6] if len(r) > 6 else ""
            })

        conn.close()
        return orders

    except Exception as e:
        return {"error": str(e)}

# ---------------- UPDATE ORDER ----------------

@app.put("/update-order/{id}")
def update_order(id: int, data: dict):
    try:
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE orders SET status=? WHERE id=?",
            (data.get("status"), id)
        )

        conn.commit()
        conn.close()

        return {"message": "Updated"}

    except Exception as e:
        return {"error": str(e)}

# ---------------- TRACK ORDER ----------------

@app.get("/track/{mobile}")
def track(mobile: str):
    try:
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT status FROM orders WHERE mobile=? ORDER BY id DESC LIMIT 1",
            (mobile,)
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return {"status": row[0]}
        else:
            return {"status": "No order found"}

    except Exception as e:
        return {"error": str(e)}