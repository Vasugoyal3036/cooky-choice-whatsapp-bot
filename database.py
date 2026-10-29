import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import DATABASE_PATH

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        cooking_tips TEXT,
        is_active INTEGER DEFAULT 1
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS variants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        pack_size TEXT NOT NULL,
        retail_price REAL NOT NULL,
        in_stock INTEGER DEFAULT 1,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wholesale_rates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        moq TEXT NOT NULL,
        rate_per_unit REAL NOT NULL,
        unit TEXT NOT NULL,
        note TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        phone_number TEXT PRIMARY KEY,
        customer_name TEXT,
        current_state TEXT DEFAULT 'MAIN_MENU',
        cart TEXT DEFAULT '[]',
        temp_data TEXT DEFAULT '{}',
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_code TEXT UNIQUE NOT NULL,
        order_type TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        customer_name TEXT,
        summary TEXT NOT NULL,
        total_amount REAL DEFAULT 0.0,
        address_or_location TEXT,
        status TEXT DEFAULT 'RECEIVED',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faqs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        question TEXT,
        keywords TEXT,
        answer TEXT
    );
    """)

    conn.commit()
    conn.close()

def get_active_products() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE is_active = 1 ORDER BY id ASC")
    rows = cursor.fetchall()
    products = []
    for row in rows:
        p = dict(row)
        cursor.execute("SELECT * FROM variants WHERE product_id = ? AND in_stock = 1 ORDER BY retail_price ASC", (p["id"],))
        p["variants"] = [dict(v) for v in cursor.fetchall()]
        products.append(p)
    conn.close()
    return products

def get_product(product_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    p = dict(row)
    cursor.execute("SELECT * FROM variants WHERE product_id = ? AND in_stock = 1 ORDER BY retail_price ASC", (product_id,))
    p["variants"] = [dict(v) for v in cursor.fetchall()]
    conn.close()
    return p

def get_wholesale_rates() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT w.*, p.name as product_name, p.category 
        FROM wholesale_rates w
        JOIN products p ON w.product_id = p.id
        WHERE p.is_active = 1
        ORDER BY p.id ASC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def update_wholesale_rate(product_id: int, rate_per_unit: float, moq: str = None, unit: str = None, note: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM wholesale_rates WHERE product_id = ?", (product_id,))
    existing = cursor.fetchone()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if existing:
        updates = ["rate_per_unit = ?", "updated_at = ?"]
        params = [rate_per_unit, now_str]
        if moq:
            updates.append("moq = ?")
            params.append(moq)
        if unit:
            updates.append("unit = ?")
            params.append(unit)
        if note is not None:
            updates.append("note = ?")
            params.append(note)
        params.append(product_id)
        cursor.execute(f"UPDATE wholesale_rates SET {', '.join(updates)} WHERE product_id = ?", params)
    else:
        cursor.execute("""
            INSERT INTO wholesale_rates (product_id, moq, rate_per_unit, unit, note, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (product_id, moq or "10 Bags", rate_per_unit, unit or "per Bag", note or "", now_str))
    conn.commit()
    conn.close()

def get_or_create_session(phone_number: str, customer_name: Optional[str] = None) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE phone_number = ?", (phone_number,))
    row = cursor.fetchone()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if row:
        session = dict(row)
        session["cart"] = json.loads(session["cart"] or "[]")
        session["temp_data"] = json.loads(session["temp_data"] or "{}")
        if customer_name and not session.get("customer_name"):
            cursor.execute("UPDATE sessions SET customer_name = ?, last_active = ? WHERE phone_number = ?", 
                           (customer_name, now_str, phone_number))
            session["customer_name"] = customer_name
            conn.commit()
    else:
        session = {
            "phone_number": phone_number,
            "customer_name": customer_name or "",
            "current_state": "MAIN_MENU",
            "cart": [],
            "temp_data": {},
            "last_active": now_str
        }
        cursor.execute("""
            INSERT INTO sessions (phone_number, customer_name, current_state, cart, temp_data, last_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (phone_number, customer_name or "", "MAIN_MENU", "[]", "{}", now_str))
        conn.commit()
    conn.close()
    return session

def update_session(phone_number: str, state: Optional[str] = None, cart: Optional[list] = None, 
                   temp_data: Optional[dict] = None, customer_name: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updates = ["last_active = ?"]
    params: List[Any] = [now_str]

    if state is not None:
        updates.append("current_state = ?")
        params.append(state)
    if cart is not None:
        updates.append("cart = ?")
        params.append(json.dumps(cart))
    if temp_data is not None:
        updates.append("temp_data = ?")
        params.append(json.dumps(temp_data))
    if customer_name is not None:
        updates.append("customer_name = ?")
        params.append(customer_name)

    params.append(phone_number)
    cursor.execute(f"UPDATE sessions SET {', '.join(updates)} WHERE phone_number = ?", params)
    conn.commit()
    conn.close()

def reset_session(phone_number: str):
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        UPDATE sessions 
        SET current_state = 'MAIN_MENU', cart = '[]', temp_data = '{}', last_active = ?
        WHERE phone_number = ?
    """, (now_str, phone_number))
    conn.commit()
    conn.close()

def create_order(order_type: str, phone_number: str, customer_name: str, summary: str, 
                 total_amount: float, address_or_location: str) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now()
    prefix = "RET" if order_type == "RETAIL" else "WHL"
    order_code = f"{prefix}-{now.strftime('%y%m%d')}-{cursor.execute('SELECT COUNT(*) FROM orders').fetchone()[0] + 101}"

    cursor.execute("""
        INSERT INTO orders (order_code, order_type, phone_number, customer_name, summary, total_amount, address_or_location, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'RECEIVED', ?)
    """, (order_code, order_type, phone_number, customer_name, summary, total_amount, address_or_location, now.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return order_code

def get_all_orders(limit: int = 100) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def update_order_status(order_id: int, status: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()

def add_product(name: str, category: str, description: str, cooking_tips: str, 
                variants: List[Dict[str, Any]], wholesale: Optional[Dict[str, Any]] = None) -> int:
    """
    Adds a new rice product with packaging variants and optional wholesale rate.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (name, category, description, cooking_tips, is_active)
        VALUES (?, ?, ?, ?, 1)
    """, (name, category, description, cooking_tips))
    product_id = cursor.lastrowid

    for v in variants:
        pack_size = v.get("pack_size", "1 kg")
        price = float(v.get("retail_price", 0.0))
        cursor.execute("""
            INSERT INTO variants (product_id, pack_size, retail_price, in_stock)
            VALUES (?, ?, ?, 1)
        """, (product_id, pack_size, price))

    if wholesale:
        moq = wholesale.get("moq", "10 Bags")
        rate = float(wholesale.get("rate", 0.0))
        unit = wholesale.get("unit", "per Bag")
        note = wholesale.get("note", "")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO wholesale_rates (product_id, moq, rate_per_unit, unit, note, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (product_id, moq, rate, unit, note, now_str))

    conn.commit()
    conn.close()
    return product_id

def delete_product(product_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM variants WHERE product_id = ?", (product_id,))
    cursor.execute("DELETE FROM wholesale_rates WHERE product_id = ?", (product_id,))
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

def toggle_product_status(product_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_active FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    new_status = 0
    if row:
        new_status = 0 if row["is_active"] == 1 else 1
        cursor.execute("UPDATE products SET is_active = ? WHERE id = ?", (new_status, product_id))
        conn.commit()
    conn.close()
    return new_status

def update_variant_price(variant_id: int, new_price: float) -> bool:
    """
    Instantly updates the retail price of a specific pack size.
    Immediately changes what WhatsApp bot quotes to customers!
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE variants SET retail_price = ? WHERE id = ?", (new_price, variant_id))
    conn.commit()
    conn.close()
    return True

def get_product_full(product_id: int) -> Optional[Dict[str, Any]]:
    """
    Returns complete product information including variants and wholesale rate for editing.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    p = dict(row)
    cursor.execute("SELECT * FROM variants WHERE product_id = ? ORDER BY id ASC", (product_id,))
    p["variants"] = [dict(v) for v in cursor.fetchall()]

    cursor.execute("SELECT * FROM wholesale_rates WHERE product_id = ?", (product_id,))
    w = cursor.fetchone()
    p["wholesale"] = dict(w) if w else None
    conn.close()
    return p

def update_product_full(product_id: int, name: str, category: str, description: str, 
                        cooking_tips: str, variants: List[Dict[str, Any]], 
                        wholesale: Optional[Dict[str, Any]] = None):
    """
    Updates all fields of an existing rice variety, its pack sizes, and wholesale pricing.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE products 
        SET name = ?, category = ?, description = ?, cooking_tips = ?
        WHERE id = ?
    """, (name, category, description, cooking_tips, product_id))

    # Update or insert variants
    cursor.execute("DELETE FROM variants WHERE product_id = ?", (product_id,))
    for v in variants:
        pack_size = v.get("pack_size", "1 kg")
        price = float(v.get("retail_price", 0.0))
        cursor.execute("""
            INSERT INTO variants (product_id, pack_size, retail_price, in_stock)
            VALUES (?, ?, ?, 1)
        """, (product_id, pack_size, price))

    # Update wholesale
    if wholesale:
        moq = wholesale.get("moq", "10 Bags")
        rate = float(wholesale.get("rate", 0.0))
        unit = wholesale.get("unit", "per Bag")
        note = wholesale.get("note", "")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("SELECT id FROM wholesale_rates WHERE product_id = ?", (product_id,))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE wholesale_rates 
                SET moq = ?, rate_per_unit = ?, unit = ?, note = ?, updated_at = ?
                WHERE product_id = ?
            """, (moq, rate, unit, note, now_str, product_id))
        else:
            cursor.execute("""
                INSERT INTO wholesale_rates (product_id, moq, rate_per_unit, unit, note, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (product_id, moq, rate, unit, note, now_str))

    conn.commit()
    conn.close()

def generate_meta_catalog_csv() -> str:
    """
    Generates Meta / WhatsApp Commerce Manager compliant CSV.
    Allows brand owner to upload directly to WhatsApp Business Catalog!
    """
    import csv
    import io
    from config import BRAND_NAME

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "title", "description", "availability", "condition", 
        "price", "link", "image_link", "brand", "google_product_category"
    ])

    products = get_active_products()
    for p in products:
        for v in p.get("variants", []):
            item_id = f"RICE_{p['id']}_{v['id']}"
            title = f"{p['name']} - {v['pack_size']}"
            desc = f"{p['description']} | Cooking Advice: {p['cooking_tips']}"
            price_str = f"{v['retail_price']:.2f} INR"
            # Default placeholder image and site link
            link = f"https://wa.me/?text=I+want+to+order+{p['name']}+{v['pack_size']}"
            image_link = "https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=600&q=80"
            writer.writerow([
                item_id, title, desc, "in stock", "new",
                price_str, link, image_link, BRAND_NAME, "Food, Beverages & Tobacco > Food Items > Grains & Rice"
            ])

    return output.getvalue()

