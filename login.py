"""
login.py
--------
Login window for the Smart Billing System.
Verifies admin credentials against the SQLite users table.
"""

import tkinter as tk
from tkinter import ttk
from utils import (
    COLORS, FONTS, center_window, show_error,
    validate_not_empty, hash_password,
)


class LoginWindow:
    """Displays the login screen and validates admin credentials."""

    def __init__(self, root, db, on_success):
        """
        root       : the main Tk root window
        db         : Database instance
        on_success : callback function called with the logged-in username
        """
        self.root = root
        self.db = db
        self.on_success = on_success

        self.root.title("Smart Billing System - Login")
        self.root.configure(bg=COLORS["bg"])
        center_window(self.root, 950, 550)
        self.root.resizable(False, False)

        self.build_ui()

    # =====================================================
    # UI BUILDING
    # =====================================================
    def build_ui(self):
        # Left branding panel
        left_panel = tk.Frame(self.root, bg=COLORS["primary"], width=450, height=550)
        left_panel.pack(side="left", fill="both")
        left_panel.pack_propagate(False)

        tk.Label(
            left_panel, text="SMART", font=("Segoe UI", 32, "bold"),
            bg=COLORS["primary"], fg=COLORS["text_light"]
        ).pack(pady=(180, 0))
        tk.Label(
            left_panel, text="BILLING SYSTEM", font=("Segoe UI", 20, "bold"),
            bg=COLORS["primary"], fg=COLORS["accent"]
        ).pack(pady=(0, 20))
        tk.Label(
            left_panel, text="Final Year College Project\nManage Products | Billing | Reports",
            font=FONTS["label"], bg=COLORS["primary"], fg=COLORS["text_muted"],
            justify="center"
        ).pack()

        # Right login form panel
        right_panel = tk.Frame(self.root, bg=COLORS["bg"], width=500, height=550)
        right_panel.pack(side="right", fill="both", expand=True)

        form_frame = tk.Frame(right_panel, bg=COLORS["bg"])
        form_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            form_frame, text="Admin Login", font=FONTS["title"],
            bg=COLORS["bg"], fg=COLORS["text_dark"]
        ).grid(row=0, column=0, columnspan=2, pady=(0, 30))

        # Username
        tk.Label(
            form_frame, text="Username", font=FONTS["label_bold"],
            bg=COLORS["bg"], fg=COLORS["text_dark"]
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 2))
        self.username_entry = tk.Entry(
            form_frame, font=FONTS["label"], width=30, relief="solid",
            bd=1, highlightthickness=1, highlightbackground=COLORS["border"]
        )
        self.username_entry.grid(row=2, column=0, columnspan=2, ipady=6, pady=(0, 15))

        # Password
        tk.Label(
            form_frame, text="Password", font=FONTS["label_bold"],
            bg=COLORS["bg"], fg=COLORS["text_dark"]
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(5, 2))
        self.password_entry = tk.Entry(
            form_frame, font=FONTS["label"], width=30, show="*", relief="solid",
            bd=1, highlightthickness=1, highlightbackground=COLORS["border"]
        )
        self.password_entry.grid(row=4, column=0, columnspan=2, ipady=6, pady=(0, 5))

        # Show password checkbox
        self.show_pw_var = tk.BooleanVar(value=False)
        show_pw_check = tk.Checkbutton(
            form_frame, text="Show Password", variable=self.show_pw_var,
            command=self.toggle_password, bg=COLORS["bg"], font=FONTS["label"]
        )
        show_pw_check.grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 20))

        # Login button
        login_btn = tk.Button(
            form_frame, text="LOGIN", font=FONTS["button"], bg=COLORS["accent"],
            fg=COLORS["text_light"], activebackground=COLORS["accent_hover"],
            relief="flat", cursor="hand2", command=self.handle_login
        )
        login_btn.grid(row=6, column=0, columnspan=2, sticky="ew", ipady=8)

        # Hint label
        tk.Label(
            form_frame, text="Default Login -> Username: admin | Password: admin123",
            font=("Segoe UI", 8), bg=COLORS["bg"], fg=COLORS["text_muted"]
        ).grid(row=7, column=0, columnspan=2, pady=(15, 0))

        self.username_entry.focus()
        self.root.bind("<Return>", lambda event: self.handle_login())

    def toggle_password(self):
        self.password_entry.config(show="" if self.show_pw_var.get() else "*")

    # =====================================================
    # LOGIN LOGIC
    # =====================================================
    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not validate_not_empty(username) or not validate_not_empty(password):
            show_error("Login Failed", "Username and Password cannot be empty.")
            return

        hashed = hash_password(password)
        user = self.db.verify_login(username, hashed)

        if user:
            self.root.unbind("<Return>")
            self.on_success(username)
        else:
            show_error("Login Failed", "Invalid Username or Password.")
            self.password_entry.delete(0, tk.END)
