"""
dashboard.py
------------
Main dashboard window shown after successful login.
Displays key statistics and provides navigation to all modules.
"""

import tkinter as tk
from tkinter import ttk
from utils import COLORS, FONTS, center_window, format_currency, ask_confirm


class Dashboard:
    """Main application dashboard with statistics and navigation."""

    def __init__(self, root, db, username, on_logout):
        self.root = root
        self.db = db
        self.username = username
        self.on_logout = on_logout

        self.root.title("Smart Billing System - Dashboard")
        self.root.configure(bg=COLORS["bg"])
        center_window(self.root, 1150, 680)
        self.root.resizable(True, True)

        # Clear any previous bindings from login screen
        self.root.unbind("<Return>")

        self.stat_labels = {}
        self.build_ui()
        self.refresh_stats()

    # =====================================================
    # UI BUILDING
    # =====================================================
    def build_ui(self):
        self.main_frame = tk.Frame(self.root, bg=COLORS["bg"])
        self.main_frame.pack(fill="both", expand=True)

        self.build_topbar()
        self.build_stat_cards()
        self.build_nav_buttons()
        self.build_footer()

    def build_topbar(self):
        topbar = tk.Frame(self.main_frame, bg=COLORS["primary"], height=70)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        tk.Label(
            topbar, text="  SMART BILLING SYSTEM", font=FONTS["heading"],
            bg=COLORS["primary"], fg=COLORS["text_light"]
        ).pack(side="left", padx=10)

        logout_btn = tk.Button(
            topbar, text="Logout", font=FONTS["button"], bg=COLORS["danger"],
            fg=COLORS["text_light"], relief="flat", cursor="hand2", padx=15,
            command=self.handle_logout
        )
        logout_btn.pack(side="right", padx=20, pady=15)

        tk.Label(
            topbar, text=f"Welcome, {self.username.title()}", font=FONTS["label_bold"],
            bg=COLORS["primary"], fg=COLORS["text_muted"]
        ).pack(side="right", padx=20)

    def build_stat_cards(self):
        stats_frame = tk.Frame(self.main_frame, bg=COLORS["bg"])
        stats_frame.pack(fill="x", padx=30, pady=25)

        card_info = [
            ("Total Products", "total_products", COLORS["accent"]),
            ("Total Bills", "total_bills", COLORS["success"]),
            ("Today's Sales", "today_sales", COLORS["warning"]),
            ("Total Revenue", "total_revenue", COLORS["primary"]),
        ]

        for i, (title, key, color) in enumerate(card_info):
            card = tk.Frame(stats_frame, bg=COLORS["card_bg"], highlightbackground=COLORS["border"],
                             highlightthickness=1)
            card.grid(row=0, column=i, padx=10, sticky="nsew")
            stats_frame.grid_columnconfigure(i, weight=1)

            color_bar = tk.Frame(card, bg=color, height=5)
            color_bar.pack(fill="x", side="top")

            tk.Label(
                card, text=title, font=FONTS["label_bold"], bg=COLORS["card_bg"],
                fg=COLORS["text_muted"]
            ).pack(pady=(15, 5))

            value_label = tk.Label(
                card, text="0", font=("Segoe UI", 20, "bold"),
                bg=COLORS["card_bg"], fg=COLORS["text_dark"]
            )
            value_label.pack(pady=(0, 20))
            self.stat_labels[key] = value_label

    def build_nav_buttons(self):
        nav_frame = tk.Frame(self.main_frame, bg=COLORS["bg"])
        nav_frame.pack(fill="both", expand=True, padx=30, pady=10)

        tk.Label(
            nav_frame, text="Quick Navigation", font=FONTS["heading"],
            bg=COLORS["bg"], fg=COLORS["text_dark"]
        ).pack(anchor="w", pady=(0, 15))

        btn_frame = tk.Frame(nav_frame, bg=COLORS["bg"])
        btn_frame.pack(fill="x")

        buttons = [
            ("Manage Products", COLORS["accent"], self.open_products),
            ("New Billing", COLORS["success"], self.open_billing),
            ("View Reports", COLORS["warning"], self.open_reports),
            ("Refresh Dashboard", COLORS["primary"], self.refresh_stats),
        ]

        for i, (text, color, command) in enumerate(buttons):
            btn = tk.Button(
                btn_frame, text=text, font=("Segoe UI", 13, "bold"), bg=color,
                fg=COLORS["text_light"], activebackground=color, relief="flat",
                cursor="hand2", command=command, width=20, height=4
            )
            btn.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            btn_frame.grid_columnconfigure(i, weight=1)

    def build_footer(self):
        footer = tk.Label(
            self.main_frame, text="Smart Billing System v1.0  |  Built with Python, Tkinter & SQLite3",
            font=("Segoe UI", 8), bg=COLORS["bg"], fg=COLORS["text_muted"]
        )
        footer.pack(side="bottom", pady=10)

    # =====================================================
    # DATA REFRESH
    # =====================================================
    def refresh_stats(self):
        self.stat_labels["total_products"].config(text=str(self.db.total_products()))
        self.stat_labels["total_bills"].config(text=str(self.db.total_bills()))
        self.stat_labels["today_sales"].config(text=format_currency(self.db.today_sales()))
        self.stat_labels["total_revenue"].config(text=format_currency(self.db.total_revenue()))

    # =====================================================
    # NAVIGATION
    # =====================================================
    def open_products(self):
        from products import ProductWindow
        ProductWindow(self.root, self.db, on_close=self.refresh_stats)

    def open_billing(self):
        from billing import BillingWindow
        BillingWindow(self.root, self.db, on_close=self.refresh_stats)

    def open_reports(self):
        from reports import ReportsWindow
        ReportsWindow(self.root, self.db)

    def handle_logout(self):
        if ask_confirm("Logout", "Are you sure you want to logout?"):
            self.main_frame.destroy()
            self.on_logout()
