"""
database.py
-----------
Handles all SQLite3 database operations for the Smart Billing System.
Creates all required tables automatically if they do not exist and
provides CRUD + reporting methods used by every other module.
"""

import sqlite3
import os
from datetime import datetime
from utils import hash_password, current_date_str


DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "billing.db")


class Database:
    """Central database handler for the Smart Billing System."""

    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.seed_default_admin()

    # =====================================================
    # TABLE CREATION
    # =====================================================
    def create_tables(self):
        """Creates all required tables if they do not already exist."""

        # Users table (for login system)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'admin'
            )
        """)

        # Products table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category TEXT,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL
            )
        """)

        # Bills table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_no TEXT UNIQUE NOT NULL,
                customer_name TEXT NOT NULL,
                mobile TEXT NOT NULL,
                email TEXT,
                address TEXT,
                subtotal REAL NOT NULL,
                gst_percent REAL NOT NULL,
                gst_amount REAL NOT NULL,
                discount REAL NOT NULL,
                grand_total REAL NOT NULL,
                bill_date TEXT NOT NULL
            )
        """)

        # Bill Items table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS bill_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_no TEXT NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                total REAL NOT NULL,
                FOREIGN KEY (bill_no) REFERENCES bills (bill_no)
            )
        """)

        self.conn.commit()

    def seed_default_admin(self):
        """Creates a default admin account (admin / admin123) if no users exist."""
        self.cursor.execute("SELECT COUNT(*) FROM users")
        count = self.cursor.fetchone()[0]
        if count == 0:
            self.cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ("admin", hash_password("admin123"), "admin"),
            )
            self.conn.commit()

    # =====================================================
    # LOGIN
    # =====================================================
    def verify_login(self, username, password_hash):
        self.cursor.execute(
            "SELECT id, username, role FROM users WHERE username=? AND password=?",
            (username, password_hash),
        )
        return self.cursor.fetchone()

    # =====================================================
    # PRODUCT CRUD
    # =====================================================
    def generate_product_code(self):
        """Auto generates a unique product code like P0001, P0002 ..."""
        self.cursor.execute("SELECT COUNT(*) FROM products")
        count = self.cursor.fetchone()[0]
        return f"P{count + 1:04d}"

    def add_product(self, name, category, price, quantity):
        code = self.generate_product_code()
        # Ensure uniqueness even if products were deleted earlier
        while self.get_product_by_code(code):
            num = int(code[1:]) + 1
            code = f"P{num:04d}"
        self.cursor.execute(
            "INSERT INTO products (product_code, name, category, price, quantity) "
            "VALUES (?, ?, ?, ?, ?)",
            (code, name, category, price, quantity),
        )
        self.conn.commit()
        return code

    def update_product(self, product_id, name, category, price, quantity):
        self.cursor.execute(
            "UPDATE products SET name=?, category=?, price=?, quantity=? WHERE id=?",
            (name, category, price, quantity, product_id),
        )
        self.conn.commit()

    def delete_product(self, product_id):
        self.cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
        self.conn.commit()

    def get_all_products(self):
        self.cursor.execute("SELECT * FROM products ORDER BY id DESC")
        return self.cursor.fetchall()

    def get_product_by_id(self, product_id):
        self.cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
        return self.cursor.fetchone()

    def get_product_by_code(self, code):
        self.cursor.execute("SELECT * FROM products WHERE product_code=?", (code,))
        return self.cursor.fetchone()

    def get_product_by_name(self, name):
        self.cursor.execute("SELECT * FROM products WHERE name=?", (name,))
        return self.cursor.fetchone()

    def search_products(self, keyword):
        keyword = f"%{keyword}%"
        self.cursor.execute(
            "SELECT * FROM products WHERE name LIKE ? OR category LIKE ? "
            "OR product_code LIKE ? ORDER BY id DESC",
            (keyword, keyword, keyword),
        )
        return self.cursor.fetchall()

    def reduce_stock(self, name, quantity):
        self.cursor.execute(
            "UPDATE products SET quantity = quantity - ? WHERE name=?",
            (quantity, name),
        )
        self.conn.commit()

    # =====================================================
    # BILL / BILL ITEMS
    # =====================================================
    def generate_bill_no(self):
        """Auto generates a unique bill number like BILL0001."""
        self.cursor.execute("SELECT COUNT(*) FROM bills")
        count = self.cursor.fetchone()[0]
        bill_no = f"BILL{count + 1:04d}"
        while self.get_bill_by_no(bill_no):
            count += 1
            bill_no = f"BILL{count + 1:04d}"
        return bill_no

    def add_bill(self, bill_no, customer_name, mobile, email, address,
                 subtotal, gst_percent, gst_amount, discount, grand_total, bill_date=None):
        if bill_date is None:
            bill_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            """INSERT INTO bills
               (bill_no, customer_name, mobile, email, address, subtotal,
                gst_percent, gst_amount, discount, grand_total, bill_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (bill_no, customer_name, mobile, email, address, subtotal,
             gst_percent, gst_amount, discount, grand_total, bill_date),
        )
        self.conn.commit()

    def add_bill_item(self, bill_no, product_name, quantity, price, total):
        self.cursor.execute(
            "INSERT INTO bill_items (bill_no, product_name, quantity, price, total) "
            "VALUES (?, ?, ?, ?, ?)",
            (bill_no, product_name, quantity, price, total),
        )
        self.conn.commit()

    def get_bill_by_no(self, bill_no):
        self.cursor.execute("SELECT * FROM bills WHERE bill_no=?", (bill_no,))
        return self.cursor.fetchone()

    def get_items_by_bill(self, bill_no):
        self.cursor.execute("SELECT * FROM bill_items WHERE bill_no=?", (bill_no,))
        return self.cursor.fetchall()

    def get_all_bills(self):
        self.cursor.execute("SELECT * FROM bills ORDER BY id DESC")
        return self.cursor.fetchall()

    # =====================================================
    # DASHBOARD STATISTICS
    # =====================================================
    def total_products(self):
        self.cursor.execute("SELECT COUNT(*) FROM products")
        return self.cursor.fetchone()[0]

    def total_bills(self):
        self.cursor.execute("SELECT COUNT(*) FROM bills")
        return self.cursor.fetchone()[0]

    def today_sales(self):
        today = current_date_str()
        self.cursor.execute(
            "SELECT COALESCE(SUM(grand_total), 0) FROM bills WHERE bill_date LIKE ?",
            (f"{today}%",),
        )
        return self.cursor.fetchone()[0]

    def total_revenue(self):
        self.cursor.execute("SELECT COALESCE(SUM(grand_total), 0) FROM bills")
        return self.cursor.fetchone()[0]

    # =====================================================
    # REPORTS
    # =====================================================
    def daily_sales(self, date_str):
        """date_str format: YYYY-MM-DD"""
        self.cursor.execute(
            "SELECT COUNT(*), COALESCE(SUM(grand_total), 0) FROM bills WHERE bill_date LIKE ?",
            (f"{date_str}%",),
        )
        return self.cursor.fetchone()

    def monthly_sales(self, year_month):
        """year_month format: YYYY-MM"""
        self.cursor.execute(
            "SELECT COUNT(*), COALESCE(SUM(grand_total), 0) FROM bills WHERE bill_date LIKE ?",
            (f"{year_month}%",),
        )
        return self.cursor.fetchone()

    def top_selling_products(self, limit=5):
        self.cursor.execute(
            """SELECT product_name, SUM(quantity) as total_qty, SUM(total) as total_amount
               FROM bill_items
               GROUP BY product_name
               ORDER BY total_qty DESC
               LIMIT ?""",
            (limit,),
        )
        return self.cursor.fetchall()

    def all_sales_summary(self):
        self.cursor.execute(
            "SELECT COUNT(*), COALESCE(SUM(grand_total), 0) FROM bills"
        )
        return self.cursor.fetchone()

    # =====================================================
    # CLEANUP
    # =====================================================
    def close(self):
        self.conn.close()
