"""
utils.py
--------
Common utility functions, style constants and validation helpers
used across the Smart Billing System application.
"""

import re
import hashlib
from datetime import datetime
from tkinter import messagebox


# =========================================================
# COLOR PALETTE / STYLE CONSTANTS (Modern, Professional UI)
# =========================================================
COLORS = {
    "primary": "#1F2A44",       # Dark navy blue - headers / sidebar
    "primary_light": "#2E3F66",
    "accent": "#2E86DE",        # Bright blue - buttons / highlights
    "accent_hover": "#1B6FC9",
    "success": "#27AE60",       # Green - success actions
    "danger": "#E74C3C",        # Red - delete / errors
    "warning": "#F39C12",       # Orange - warnings / low stock
    "bg": "#F4F6F9",            # Light grey background
    "card_bg": "#FFFFFF",
    "text_dark": "#1F2A44",
    "text_light": "#FFFFFF",
    "text_muted": "#7F8C9A",
    "border": "#D5DBE3",
}

FONTS = {
    "title": ("Segoe UI", 22, "bold"),
    "heading": ("Segoe UI", 16, "bold"),
    "subheading": ("Segoe UI", 12, "bold"),
    "label": ("Segoe UI", 10),
    "label_bold": ("Segoe UI", 10, "bold"),
    "button": ("Segoe UI", 10, "bold"),
    "table": ("Segoe UI", 10),
    "table_header": ("Segoe UI", 10, "bold"),
}


# =========================================================
# WINDOW HELPERS
# =========================================================
def center_window(win, width, height):
    """Centers a Tkinter window on the screen."""
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))
    win.geometry(f"{width}x{height}+{x}+{y}")


# =========================================================
# MESSAGE HELPERS
# =========================================================
def show_error(title, message):
    messagebox.showerror(title, message)


def show_success(title, message):
    messagebox.showinfo(title, message)


def show_warning(title, message):
    messagebox.showwarning(title, message)


def ask_confirm(title, message):
    return messagebox.askyesno(title, message)


# =========================================================
# VALIDATION HELPERS
# =========================================================
def validate_not_empty(value):
    """Returns True if the value is not empty after stripping spaces."""
    return value is not None and str(value).strip() != ""


def validate_numeric(value, allow_decimal=True):
    """Validates that a value is a valid positive number."""
    if not validate_not_empty(value):
        return False
    pattern = r"^\d+(\.\d+)?$" if allow_decimal else r"^\d+$"
    return re.match(pattern, str(value).strip()) is not None


def validate_mobile(value):
    """Validates a 10-digit Indian mobile number."""
    if not validate_not_empty(value):
        return False
    return re.match(r"^[6-9]\d{9}$", str(value).strip()) is not None


def validate_email(value):
    """Validates email format. Empty string is allowed (optional field)."""
    if not validate_not_empty(value):
        return True  # optional field
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, str(value).strip()) is not None


# =========================================================
# FORMATTING HELPERS
# =========================================================
def format_currency(amount):
    """Formats a number as currency string with 2 decimal places."""
    try:
        return f"Rs. {float(amount):,.2f}"
    except (ValueError, TypeError):
        return "Rs. 0.00"


def current_datetime_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def current_date_str():
    return datetime.now().strftime("%Y-%m-%d")


# =========================================================
# SECURITY HELPERS
# =========================================================
def hash_password(password):
    """Returns a SHA-256 hash of the given password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password, hashed):
    """Verifies a plain password against a stored hash."""
    return hash_password(password) == hashed
