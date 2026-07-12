"""
products.py
-----------
Product Management module.
Allows adding, updating, deleting and searching products,
displayed in a Treeview table with live stock status.
"""

import tkinter as tk
from tkinter import ttk
from utils import (
    COLORS, FONTS, center_window, show_error, show_success, ask_confirm,
    validate_not_empty, validate_numeric,
)


class ProductWindow:
    """Toplevel window for full product management (CRUD)."""

    def __init__(self, parent, db, on_close=None):
        self.parent = parent
        self.db = db
        self.on_close_callback = on_close
        self.selected_product_id = None

        self.win = tk.Toplevel(parent)
        self.win.title("Smart Billing System - Product Management")
        self.win.configure(bg=COLORS["bg"])
        center_window(self.win, 1000, 650)
        self.win.transient(parent)
        self.win.grab_set()
        self.win.protocol("WM_DELETE_WINDOW", self.close_window)

        self.build_ui()
        self.load_products()

    # =====================================================
    # UI BUILDING
    # =====================================================
    def build_ui(self):
        # Header
        header = tk.Frame(self.win, bg=COLORS["primary"], height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header, text="  Product Management", font=FONTS["heading"],
            bg=COLORS["primary"], fg=COLORS["text_light"]
        ).pack(side="left", padx=10, pady=10)

        body = tk.Frame(self.win, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=15, pady=15)

        # ---------------- Form Frame (left) ----------------
        form_card = tk.Frame(body, bg=COLORS["card_bg"], highlightbackground=COLORS["border"],
                              highlightthickness=1, width=300)
        form_card.pack(side="left", fill="y", padx=(0, 15))
        form_card.pack_propagate(False)

        tk.Label(
            form_card, text="Product Details", font=FONTS["subheading"],
            bg=COLORS["card_bg"], fg=COLORS["text_dark"]
        ).pack(anchor="w", padx=15, pady=(15, 10))

        self.name_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.quantity_var = tk.StringVar()

        self._make_field(form_card, "Product Name", self.name_var)
        self._make_field(form_card, "Category", self.category_var)
        self._make_field(form_card, "Price (Rs.)", self.price_var)
        self._make_field(form_card, "Quantity", self.quantity_var)

        btn_frame = tk.Frame(form_card, bg=COLORS["card_bg"])
        btn_frame.pack(fill="x", padx=15, pady=20)

        tk.Button(
            btn_frame, text="Add Product", font=FONTS["button"], bg=COLORS["success"],
            fg=COLORS["text_light"], relief="flat", cursor="hand2",
            command=self.add_product
        ).pack(fill="x", pady=4, ipady=6)

        tk.Button(
            btn_frame, text="Update Product", font=FONTS["button"], bg=COLORS["accent"],
            fg=COLORS["text_light"], relief="flat", cursor="hand2",
            command=self.update_product
        ).pack(fill="x", pady=4, ipady=6)

        tk.Button(
            btn_frame, text="Delete Product", font=FONTS["button"], bg=COLORS["danger"],
            fg=COLORS["text_light"], relief="flat", cursor="hand2",
            command=self.delete_product
        ).pack(fill="x", pady=4, ipady=6)

        tk.Button(
            btn_frame, text="Clear Form", font=FONTS["button"], bg=COLORS["text_muted"],
            fg=COLORS["text_light"], relief="flat", cursor="hand2",
            command=self.clear_form
        ).pack(fill="x", pady=4, ipady=6)

        # ---------------- Table Frame (right) ----------------
        table_card = tk.Frame(body, bg=COLORS["card_bg"], highlightbackground=COLORS["border"],
                               highlightthickness=1)
        table_card.pack(side="right", fill="both", expand=True)

        # Search bar
        search_frame = tk.Frame(table_card, bg=COLORS["card_bg"])
        search_frame.pack(fill="x", padx=15, pady=(15, 5))

        tk.Label(
            search_frame, text="Search:", font=FONTS["label_bold"],
            bg=COLORS["card_bg"], fg=COLORS["text_dark"]
        ).pack(side="left")

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=FONTS["label"], width=30)
        search_entry.pack(side="left", padx=10, ipady=4)
        search_entry.bind("<KeyRelease>", lambda e: self.load_products())

        tk.Button(
            search_frame, text="Clear Search", font=FONTS["label"], bg=COLORS["bg"],
            relief="flat", cursor="hand2", command=self.clear_search
        ).pack(side="left")

        # Treeview
        tree_frame = tk.Frame(table_card, bg=COLORS["card_bg"])
        tree_frame.pack(fill="both", expand=True, padx=15, pady=10)

        columns = ("id", "code", "name", "category", "price", "quantity", "status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)

        headings = {
            "id": "ID", "code": "Code", "name": "Name", "category": "Category",
            "price": "Price", "quantity": "Qty", "status": "Stock Status"
        }
        widths = {"id": 40, "code": 70, "name": 150, "category": 100, "price": 80, "quantity": 60, "status": 100}

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")

        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select_row)

        style = ttk.Style()
        style.configure("Treeview", font=FONTS["table"], rowheight=28)
        style.configure("Treeview.Heading", font=FONTS["table_header"])

    def _make_field(self, parent, label_text, var):
        tk.Label(
            parent, text=label_text, font=FONTS["label_bold"],
            bg=COLORS["card_bg"], fg=COLORS["text_dark"]
        ).pack(anchor="w", padx=15, pady=(8, 2))
        entry = tk.Entry(parent, textvariable=var, font=FONTS["label"], relief="solid", bd=1)
        entry.pack(fill="x", padx=15, ipady=5)
        return entry

    # =====================================================
    # DATA OPERATIONS
    # =====================================================
    def load_products(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        keyword = self.search_var.get().strip()
        products = self.db.search_products(keyword) if keyword else self.db.get_all_products()

        for p in products:
            pid, code, name, category, price, quantity = p
            status = self._stock_status(quantity)
            self.tree.insert(
                "", "end",
                values=(pid, code, name, category or "-", f"{price:.2f}", quantity, status)
            )

    def _stock_status(self, quantity):
        if quantity <= 0:
            return "Out of Stock"
        elif quantity <= 5:
            return "Low Stock"
        return "In Stock"

    def clear_search(self):
        self.search_var.set("")
        self.load_products()

    def on_select_row(self, event):
        selected = self.tree.focus()
        if not selected:
            return
        values = self.tree.item(selected, "values")
        self.selected_product_id = values[0]
        self.name_var.set(values[2])
        self.category_var.set(values[3] if values[3] != "-" else "")
        self.price_var.set(values[4])
        self.quantity_var.set(values[5])

    def clear_form(self):
        self.selected_product_id = None
        self.name_var.set("")
        self.category_var.set("")
        self.price_var.set("")
        self.quantity_var.set("")
        self.tree.selection_remove(self.tree.selection())

    def _validate_form(self):
        if not validate_not_empty(self.name_var.get()):
            show_error("Validation Error", "Product Name cannot be empty.")
            return False
        if not validate_numeric(self.price_var.get()):
            show_error("Validation Error", "Price must be a valid number.")
            return False
        if not validate_numeric(self.quantity_var.get(), allow_decimal=False):
            show_error("Validation Error", "Quantity must be a valid whole number.")
            return False
        return True

    def add_product(self):
        if not self._validate_form():
            return
        code = self.db.add_product(
            self.name_var.get().strip(),
            self.category_var.get().strip(),
            float(self.price_var.get()),
            int(self.quantity_var.get()),
        )
        show_success("Success", f"Product added successfully with code: {code}")
        self.clear_form()
        self.load_products()

    def update_product(self):
        if self.selected_product_id is None:
            show_error("No Selection", "Please select a product from the table to update.")
            return
        if not self._validate_form():
            return
        self.db.update_product(
            self.selected_product_id,
            self.name_var.get().strip(),
            self.category_var.get().strip(),
            float(self.price_var.get()),
            int(self.quantity_var.get()),
        )
        show_success("Success", "Product updated successfully.")
        self.clear_form()
        self.load_products()

    def delete_product(self):
        if self.selected_product_id is None:
            show_error("No Selection", "Please select a product from the table to delete.")
            return
        if ask_confirm("Confirm Delete", "Are you sure you want to delete this product?"):
            self.db.delete_product(self.selected_product_id)
            show_success("Success", "Product deleted successfully.")
            self.clear_form()
            self.load_products()

    # =====================================================
    # CLOSE
    # =====================================================
    def close_window(self):
        if self.on_close_callback:
            self.on_close_callback()
        self.win.destroy()
