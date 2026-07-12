"""
reports.py
----------
Reports module. Displays daily sales, monthly sales, total revenue,
number of bills and top selling products.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from utils import COLORS, FONTS, center_window, format_currency, current_date_str, show_error


class ReportsWindow:
    """Toplevel window showing business reports and analytics."""

    def __init__(self, parent, db):
        self.parent = parent
        self.db = db

        self.win = tk.Toplevel(parent)
        self.win.title("Smart Billing System - Reports")
        self.win.configure(bg=COLORS["bg"])
        center_window(self.win, 950, 650)
        self.win.transient(parent)
        self.win.grab_set()

        self.build_ui()
        self.load_overall_summary()
        self.load_top_products()

    # =====================================================
    # UI BUILDING
    # =====================================================
    def build_ui(self):
        header = tk.Frame(self.win, bg=COLORS["primary"], height=55)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header, text="  Reports & Analytics", font=FONTS["heading"],
            bg=COLORS["primary"], fg=COLORS["text_light"]
        ).pack(side="left", padx=10, pady=10)

        body = tk.Frame(self.win, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=15, pady=15)

        self.build_summary_cards(body)
        self.build_daily_report(body)
        self.build_monthly_report(body)
        self.build_top_products(body)

    def build_summary_cards(self, parent):
        frame = tk.Frame(parent, bg=COLORS["bg"])
        frame.pack(fill="x", pady=(0, 15))

        self.total_bills_var = tk.StringVar(value="0")
        self.total_revenue_var = tk.StringVar(value=format_currency(0))

        for i, (title, var, color) in enumerate([
            ("Total Number of Bills", self.total_bills_var, COLORS["accent"]),
            ("Total Revenue", self.total_revenue_var, COLORS["success"]),
        ]):
            card = tk.Frame(frame, bg=COLORS["card_bg"], highlightbackground=COLORS["border"],
                             highlightthickness=1)
            card.grid(row=0, column=i, padx=10, sticky="nsew")
            frame.grid_columnconfigure(i, weight=1)

            tk.Label(
                card, text=title, font=FONTS["label_bold"], bg=COLORS["card_bg"],
                fg=COLORS["text_muted"]
            ).pack(pady=(15, 5))
            tk.Label(
                card, textvariable=var, font=("Segoe UI", 18, "bold"),
                bg=COLORS["card_bg"], fg=color
            ).pack(pady=(0, 15))

    def build_daily_report(self, parent):
        card = tk.Frame(parent, bg=COLORS["card_bg"], highlightbackground=COLORS["border"],
                         highlightthickness=1)
        card.pack(fill="x", pady=(0, 10))

        tk.Label(
            card, text="Daily Sales Report", font=FONTS["subheading"],
            bg=COLORS["card_bg"], fg=COLORS["text_dark"]
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=15, pady=(10, 5))

        tk.Label(
            card, text="Date (YYYY-MM-DD):", font=FONTS["label"], bg=COLORS["card_bg"]
        ).grid(row=1, column=0, sticky="w", padx=15, pady=(0, 10))

        self.daily_date_var = tk.StringVar(value=current_date_str())
        tk.Entry(
            card, textvariable=self.daily_date_var, font=FONTS["label"], width=15
        ).grid(row=1, column=1, sticky="w", pady=(0, 10))

        tk.Button(
            card, text="Get Report", font=FONTS["button"], bg=COLORS["accent"],
            fg=COLORS["text_light"], relief="flat", cursor="hand2",
            command=self.load_daily_report
        ).grid(row=1, column=2, padx=10, pady=(0, 10))

        self.daily_result_var = tk.StringVar(value="Bills: 0   |   Sales: Rs. 0.00")
        tk.Label(
            card, textvariable=self.daily_result_var, font=FONTS["label_bold"],
            bg=COLORS["card_bg"], fg=COLORS["success"]
        ).grid(row=1, column=3, sticky="w", padx=15, pady=(0, 10))

    def build_monthly_report(self, parent):
        card = tk.Frame(parent, bg=COLORS["card_bg"], highlightbackground=COLORS["border"],
                         highlightthickness=1)
        card.pack(fill="x", pady=(0, 10))

        tk.Label(
            card, text="Monthly Sales Report", font=FONTS["subheading"],
            bg=COLORS["card_bg"], fg=COLORS["text_dark"]
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=15, pady=(10, 5))

        tk.Label(
            card, text="Month (YYYY-MM):", font=FONTS["label"], bg=COLORS["card_bg"]
        ).grid(row=1, column=0, sticky="w", padx=15, pady=(0, 10))

        self.monthly_var = tk.StringVar(value=datetime.now().strftime("%Y-%m"))
        tk.Entry(
            card, textvariable=self.monthly_var, font=FONTS["label"], width=15
        ).grid(row=1, column=1, sticky="w", pady=(0, 10))

        tk.Button(
            card, text="Get Report", font=FONTS["button"], bg=COLORS["accent"],
            fg=COLORS["text_light"], relief="flat", cursor="hand2",
            command=self.load_monthly_report
        ).grid(row=1, column=2, padx=10, pady=(0, 10))

        self.monthly_result_var = tk.StringVar(value="Bills: 0   |   Sales: Rs. 0.00")
        tk.Label(
            card, textvariable=self.monthly_result_var, font=FONTS["label_bold"],
            bg=COLORS["card_bg"], fg=COLORS["success"]
        ).grid(row=1, column=3, sticky="w", padx=15, pady=(0, 10))

    def build_top_products(self, parent):
        card = tk.Frame(parent, bg=COLORS["card_bg"], highlightbackground=COLORS["border"],
                         highlightthickness=1)
        card.pack(fill="both", expand=True)

        tk.Label(
            card, text="Top Selling Products", font=FONTS["subheading"],
            bg=COLORS["card_bg"], fg=COLORS["text_dark"]
        ).pack(anchor="w", padx=15, pady=(10, 5))

        tree_frame = tk.Frame(card, bg=COLORS["card_bg"])
        tree_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        columns = ("rank", "name", "qty", "amount")
        self.top_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)
        headings = {"rank": "Rank", "name": "Product Name", "qty": "Total Qty Sold", "amount": "Total Amount"}
        widths = {"rank": 60, "name": 250, "qty": 150, "amount": 150}
        for col in columns:
            self.top_tree.heading(col, text=headings[col])
            self.top_tree.column(col, width=widths[col], anchor="center")

        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.top_tree.yview)
        self.top_tree.configure(yscrollcommand=v_scroll.set)
        self.top_tree.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")

    # =====================================================
    # DATA LOADING
    # =====================================================
    def load_overall_summary(self):
        count, revenue = self.db.all_sales_summary()
        self.total_bills_var.set(str(count))
        self.total_revenue_var.set(format_currency(revenue))

    def load_daily_report(self):
        date_str = self.daily_date_var.get().strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            show_error("Invalid Date", "Please enter date in YYYY-MM-DD format.")
            return
        count, sales = self.db.daily_sales(date_str)
        self.daily_result_var.set(f"Bills: {count}   |   Sales: {format_currency(sales)}")

    def load_monthly_report(self):
        month_str = self.monthly_var.get().strip()
        try:
            datetime.strptime(month_str, "%Y-%m")
        except ValueError:
            show_error("Invalid Month", "Please enter month in YYYY-MM format.")
            return
        count, sales = self.db.monthly_sales(month_str)
        self.monthly_result_var.set(f"Bills: {count}   |   Sales: {format_currency(sales)}")

    def load_top_products(self):
        for row in self.top_tree.get_children():
            self.top_tree.delete(row)
        products = self.db.top_selling_products(limit=10)
        for i, (name, qty, amount) in enumerate(products, start=1):
            self.top_tree.insert("", "end", values=(i, name, qty, format_currency(amount)))
