"""
billing.py
----------
Billing module. Handles customer details entry, product cart management,
GST & discount calculation, bill generation (DB + PDF + TXT), and
bill search / reprint functionality.
"""

import os
import tkinter as tk
from tkinter import ttk, simpledialog

from utils import (
    COLORS, FONTS, center_window, show_error, show_success, ask_confirm,
    validate_not_empty, validate_numeric, validate_mobile, validate_email,
    format_currency, current_datetime_str,
)

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as rl_colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


BILLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bills")
os.makedirs(BILLS_DIR, exist_ok=True)


class BillingWindow:
    """Toplevel window for creating and managing bills/invoices."""

    def __init__(self, parent, db, on_close=None):
        self.parent = parent
        self.db = db
        self.on_close_callback = on_close

        self.cart = []          # list of dicts: name, price, qty, total
        self.product_map = {}   # name -> product row

        self.win = tk.Toplevel(parent)
        self.win.title("Smart Billing System - Billing")
        self.win.configure(bg=COLORS["bg"])
        center_window(self.win, 1150, 720)
        self.win.transient(parent)
        self.win.grab_set()
        self.win.protocol("WM_DELETE_WINDOW", self.close_window)

        self.build_ui()
        self.load_products_dropdown()
        self.generate_new_bill_no()

    # =====================================================
    # UI BUILDING
    # =====================================================
    def build_ui(self):
        header = tk.Frame(self.win, bg=COLORS["primary"], height=55)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header, text="  Billing Section", font=FONTS["heading"],
            bg=COLORS["primary"], fg=COLORS["text_light"]
        ).pack(side="left", padx=10, pady=10)

        tk.Button(
            header, text="Search Bill", font=FONTS["button"], bg=COLORS["accent"],
            fg=COLORS["text_light"], relief="flat", cursor="hand2",
            command=self.open_search_bill
        ).pack(side="right", padx=15, pady=10)

        body = tk.Frame(self.win, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=15, pady=15)

        self.build_customer_section(body)
        self.build_product_section(body)
        self.build_cart_table(body)
        self.build_totals_section(body)

    # ---------------- Customer Section ----------------
    def build_customer_section(self, parent):
        card = tk.Frame(parent, bg=COLORS["card_bg"], highlightbackground=COLORS["border"],
                         highlightthickness=1)
        card.pack(fill="x", pady=(0, 10))

        tk.Label(
            card, text="Customer Details", font=FONTS["subheading"],
            bg=COLORS["card_bg"], fg=COLORS["text_dark"]
        ).grid(row=0, column=0, columnspan=6, sticky="w", padx=15, pady=(10, 5))

        self.customer_name_var = tk.StringVar()
        self.mobile_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.bill_no_var = tk.StringVar()

        fields = [
            ("Customer Name*", self.customer_name_var, 1, 0),
            ("Mobile Number*", self.mobile_var, 1, 2),
            ("Email (Optional)", self.email_var, 1, 4),
            ("Address (Optional)", self.address_var, 2, 0),
        ]
        for label_text, var, r, c in fields:
            tk.Label(
                card, text=label_text, font=FONTS["label"], bg=COLORS["card_bg"],
                fg=COLORS["text_dark"]
            ).grid(row=r, column=c, sticky="w", padx=(15, 5), pady=5)
            entry = tk.Entry(card, textvariable=var, font=FONTS["label"], width=25)
            entry.grid(row=r, column=c + 1, sticky="w", padx=(0, 15), pady=5, ipady=3)

        tk.Label(
            card, text="Bill No:", font=FONTS["label_bold"], bg=COLORS["card_bg"],
            fg=COLORS["text_dark"]
        ).grid(row=2, column=4, sticky="w", padx=(15, 5), pady=5)
        tk.Label(
            card, textvariable=self.bill_no_var, font=FONTS["label_bold"],
            bg=COLORS["card_bg"], fg=COLORS["accent"]
        ).grid(row=2, column=5, sticky="w", pady=5)

    # ---------------- Product Selection Section ----------------
    def build_product_section(self, parent):
        card = tk.Frame(parent, bg=COLORS["card_bg"], highlightbackground=COLORS["border"],
                         highlightthickness=1)
        card.pack(fill="x", pady=(0, 10))

        tk.Label(
            card, text="Add Product", font=FONTS["subheading"],
            bg=COLORS["card_bg"], fg=COLORS["text_dark"]
        ).grid(row=0, column=0, columnspan=6, sticky="w", padx=15, pady=(10, 5))

        tk.Label(
            card, text="Product:", font=FONTS["label"], bg=COLORS["card_bg"]
        ).grid(row=1, column=0, sticky="w", padx=(15, 5), pady=(0, 10))

        self.product_var = tk.StringVar()
        self.product_combo = ttk.Combobox(
            card, textvariable=self.product_var, font=FONTS["label"],
            width=28, state="readonly"
        )
        self.product_combo.grid(row=1, column=1, sticky="w", pady=(0, 10))
        self.product_combo.bind("<<ComboboxSelected>>", self.autofill_price)

        tk.Label(
            card, text="Price:", font=FONTS["label"], bg=COLORS["card_bg"]
        ).grid(row=1, column=2, sticky="w", padx=(15, 5), pady=(0, 10))
        self.price_var = tk.StringVar()
        tk.Entry(
            card, textvariable=self.price_var, font=FONTS["label"], width=10, state="readonly"
        ).grid(row=1, column=3, sticky="w", pady=(0, 10))

        tk.Label(
            card, text="Quantity:", font=FONTS["label"], bg=COLORS["card_bg"]
        ).grid(row=1, column=4, sticky="w", padx=(15, 5), pady=(0, 10))
        self.qty_var = tk.StringVar(value="1")
        tk.Entry(
            card, textvariable=self.qty_var, font=FONTS["label"], width=8
        ).grid(row=1, column=5, sticky="w", pady=(0, 10))

        btn_frame = tk.Frame(card, bg=COLORS["card_bg"])
        btn_frame.grid(row=1, column=6, padx=15, pady=(0, 10))

        tk.Button(
            btn_frame, text="Add Item", font=FONTS["button"], bg=COLORS["success"],
            fg=COLORS["text_light"], relief="flat", cursor="hand2", padx=10,
            command=self.add_item_to_cart
        ).pack(side="left", padx=3)

        tk.Button(
            btn_frame, text="Remove Item", font=FONTS["button"], bg=COLORS["danger"],
            fg=COLORS["text_light"], relief="flat", cursor="hand2", padx=10,
            command=self.remove_item_from_cart
        ).pack(side="left", padx=3)

        tk.Button(
            btn_frame, text="Edit Qty", font=FONTS["button"], bg=COLORS["warning"],
            fg=COLORS["text_light"], relief="flat", cursor="hand2", padx=10,
            command=self.edit_item_quantity
        ).pack(side="left", padx=3)

    # ---------------- Cart Table ----------------
    def build_cart_table(self, parent):
        card = tk.Frame(parent, bg=COLORS["card_bg"], highlightbackground=COLORS["border"],
                         highlightthickness=1)
        card.pack(fill="both", expand=True, pady=(0, 10))

        tk.Label(
            card, text="Bill Items", font=FONTS["subheading"],
            bg=COLORS["card_bg"], fg=COLORS["text_dark"]
        ).pack(anchor="w", padx=15, pady=(10, 5))

        tree_frame = tk.Frame(card, bg=COLORS["card_bg"])
        tree_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        columns = ("name", "price", "qty", "total")
        self.cart_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)
        headings = {"name": "Product Name", "price": "Price", "qty": "Quantity", "total": "Total"}
        widths = {"name": 300, "price": 120, "qty": 100, "total": 150}
        for col in columns:
            self.cart_tree.heading(col, text=headings[col])
            self.cart_tree.column(col, width=widths[col], anchor="center")

        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=v_scroll.set)
        self.cart_tree.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")

    # ---------------- Totals / GST Section ----------------
    def build_totals_section(self, parent):
        card = tk.Frame(parent, bg=COLORS["card_bg"], highlightbackground=COLORS["border"],
                         highlightthickness=1)
        card.pack(fill="x")

        left = tk.Frame(card, bg=COLORS["card_bg"])
        left.pack(side="left", fill="y", padx=15, pady=15)

        tk.Label(
            left, text="GST %:", font=FONTS["label_bold"], bg=COLORS["card_bg"]
        ).grid(row=0, column=0, sticky="w", pady=5)

        self.gst_var = tk.StringVar(value="5")
        for i, val in enumerate(["5", "12", "18"]):
            tk.Radiobutton(
                left, text=f"{val}%", variable=self.gst_var, value=val,
                bg=COLORS["card_bg"], font=FONTS["label"], command=self.calculate_totals
            ).grid(row=0, column=i + 1, padx=5)

        tk.Label(
            left, text="Discount (Rs.):", font=FONTS["label_bold"], bg=COLORS["card_bg"]
        ).grid(row=1, column=0, sticky="w", pady=5)
        self.discount_var = tk.StringVar(value="0")
        discount_entry = tk.Entry(left, textvariable=self.discount_var, font=FONTS["label"], width=12)
        discount_entry.grid(row=1, column=1, columnspan=2, sticky="w")
        discount_entry.bind("<KeyRelease>", lambda e: self.calculate_totals())

        tk.Button(
            left, text="Recalculate", font=FONTS["label"], bg=COLORS["bg"],
            relief="flat", cursor="hand2", command=self.calculate_totals
        ).grid(row=1, column=3, padx=10)

        right = tk.Frame(card, bg=COLORS["card_bg"])
        right.pack(side="right", fill="y", padx=20, pady=15)

        self.subtotal_var = tk.StringVar(value=format_currency(0))
        self.gst_amount_var = tk.StringVar(value=format_currency(0))
        self.grand_total_var = tk.StringVar(value=format_currency(0))

        self._totals_row(right, "Subtotal:", self.subtotal_var, 0)
        self._totals_row(right, "GST Amount:", self.gst_amount_var, 1)
        self._totals_row(right, "Grand Total:", self.grand_total_var, 2, bold=True)

        action_frame = tk.Frame(card, bg=COLORS["card_bg"])
        action_frame.pack(side="right", fill="y", padx=10, pady=15)

        tk.Button(
            action_frame, text="Generate Bill", font=("Segoe UI", 12, "bold"),
            bg=COLORS["success"], fg=COLORS["text_light"], relief="flat", cursor="hand2",
            padx=20, pady=10, command=self.generate_bill
        ).pack(pady=5)

        tk.Button(
            action_frame, text="Clear / New Bill", font=FONTS["button"],
            bg=COLORS["text_muted"], fg=COLORS["text_light"], relief="flat", cursor="hand2",
            padx=20, command=self.reset_billing_form
        ).pack(pady=5)

    def _totals_row(self, parent, label_text, var, row, bold=False):
        font = ("Segoe UI", 13, "bold") if bold else FONTS["label_bold"]
        color = COLORS["success"] if bold else COLORS["text_dark"]
        tk.Label(parent, text=label_text, font=font, bg=COLORS["card_bg"], fg=color).grid(
            row=row, column=0, sticky="w", pady=3
        )
        tk.Label(parent, textvariable=var, font=font, bg=COLORS["card_bg"], fg=color).grid(
            row=row, column=1, sticky="e", padx=(20, 0), pady=3
        )

    # =====================================================
    # DATA LOADING
    # =====================================================
    def load_products_dropdown(self):
        products = self.db.get_all_products()
        self.product_map = {p[2]: p for p in products}  # name -> row (id, code, name, category, price, qty)
        self.product_combo["values"] = list(self.product_map.keys())

    def generate_new_bill_no(self):
        self.bill_no_var.set(self.db.generate_bill_no())

    def autofill_price(self, event=None):
        name = self.product_var.get()
        product = self.product_map.get(name)
        if product:
            price = product[4]
            self.price_var.set(f"{price:.2f}")

    # =====================================================
    # CART OPERATIONS
    # =====================================================
    def add_item_to_cart(self):
        name = self.product_var.get()
        if not validate_not_empty(name):
            show_error("Validation Error", "Please select a product.")
            return
        if not validate_numeric(self.qty_var.get(), allow_decimal=False):
            show_error("Validation Error", "Quantity must be a valid whole number.")
            return

        qty = int(self.qty_var.get())
        if qty <= 0:
            show_error("Validation Error", "Quantity must be greater than zero.")
            return

        product = self.product_map.get(name)
        if not product:
            show_error("Error", "Selected product not found in database.")
            return

        available_stock = product[5]
        # account for quantity already in cart for this product
        already_in_cart = sum(item["qty"] for item in self.cart if item["name"] == name)
        if qty + already_in_cart > available_stock:
            show_error(
                "Insufficient Stock",
                f"Only {available_stock - already_in_cart} unit(s) of '{name}' available in stock."
            )
            return

        price = product[4]
        total = round(price * qty, 2)

        # Merge with existing cart entry if same product added again
        for item in self.cart:
            if item["name"] == name:
                item["qty"] += qty
                item["total"] = round(item["qty"] * item["price"], 2)
                self.refresh_cart_table()
                self.calculate_totals()
                return

        self.cart.append({"name": name, "price": price, "qty": qty, "total": total})
        self.refresh_cart_table()
        self.calculate_totals()
        self.qty_var.set("1")

    def remove_item_from_cart(self):
        selected = self.cart_tree.focus()
        if not selected:
            show_error("No Selection", "Please select an item in the bill to remove.")
            return
        values = self.cart_tree.item(selected, "values")
        name = values[0]
        self.cart = [item for item in self.cart if item["name"] != name]
        self.refresh_cart_table()
        self.calculate_totals()

    def edit_item_quantity(self):
        selected = self.cart_tree.focus()
        if not selected:
            show_error("No Selection", "Please select an item in the bill to edit.")
            return
        values = self.cart_tree.item(selected, "values")
        name = values[0]

        new_qty = simpledialog.askinteger(
            "Edit Quantity", f"Enter new quantity for '{name}':", minvalue=1, parent=self.win
        )
        if new_qty is None:
            return

        product = self.product_map.get(name)
        if product and new_qty > product[5]:
            show_error("Insufficient Stock", f"Only {product[5]} unit(s) of '{name}' available.")
            return

        for item in self.cart:
            if item["name"] == name:
                item["qty"] = new_qty
                item["total"] = round(item["qty"] * item["price"], 2)
                break

        self.refresh_cart_table()
        self.calculate_totals()

    def refresh_cart_table(self):
        for row in self.cart_tree.get_children():
            self.cart_tree.delete(row)
        for item in self.cart:
            self.cart_tree.insert(
                "", "end",
                values=(item["name"], f"{item['price']:.2f}", item["qty"], f"{item['total']:.2f}")
            )

    # =====================================================
    # CALCULATIONS
    # =====================================================
    def calculate_totals(self):
        subtotal = sum(item["total"] for item in self.cart)

        discount_str = self.discount_var.get().strip() or "0"
        discount = float(discount_str) if validate_numeric(discount_str) else 0.0

        gst_percent = float(self.gst_var.get())
        gst_amount = round((subtotal - discount) * gst_percent / 100, 2) if subtotal > discount else 0.0
        grand_total = round(subtotal - discount + gst_amount, 2)
        if grand_total < 0:
            grand_total = 0.0

        self.subtotal_var.set(format_currency(subtotal))
        self.gst_amount_var.set(format_currency(gst_amount))
        self.grand_total_var.set(format_currency(grand_total))

        return subtotal, gst_percent, gst_amount, discount, grand_total

    # =====================================================
    # BILL GENERATION
    # =====================================================
    def generate_bill(self):
        if not validate_not_empty(self.customer_name_var.get()):
            show_error("Validation Error", "Customer name is required.")
            return
        if not validate_mobile(self.mobile_var.get()):
            show_error("Validation Error", "Enter a valid 10-digit mobile number.")
            return
        if not validate_email(self.email_var.get()):
            show_error("Validation Error", "Enter a valid email address or leave it blank.")
            return
        if not self.cart:
            show_error("Validation Error", "Please add at least one product to the bill.")
            return

        subtotal, gst_percent, gst_amount, discount, grand_total = self.calculate_totals()
        bill_no = self.bill_no_var.get()
        bill_date = current_datetime_str()

        customer_name = self.customer_name_var.get().strip()
        mobile = self.mobile_var.get().strip()
        email = self.email_var.get().strip()
        address = self.address_var.get().strip()

        # Save to database
        self.db.add_bill(
            bill_no, customer_name, mobile, email, address,
            subtotal, gst_percent, gst_amount, discount, grand_total, bill_date
        )
        for item in self.cart:
            self.db.add_bill_item(bill_no, item["name"], item["qty"], item["price"], item["total"])
            self.db.reduce_stock(item["name"], item["qty"])

        bill_data = {
            "bill_no": bill_no, "customer_name": customer_name, "mobile": mobile,
            "email": email, "address": address, "subtotal": subtotal,
            "gst_percent": gst_percent, "gst_amount": gst_amount, "discount": discount,
            "grand_total": grand_total, "bill_date": bill_date, "items": list(self.cart),
        }

        pdf_path = self.save_bill_pdf(bill_data)
        txt_path = self.save_bill_txt(bill_data)

        show_success(
            "Bill Generated",
            f"Bill '{bill_no}' generated successfully!\n\n"
            f"Grand Total: {format_currency(grand_total)}\n\n"
            f"PDF saved to:\n{pdf_path}\n\nText file saved to:\n{txt_path}"
        )

        self.load_products_dropdown()  # refresh stock quantities
        self.reset_billing_form()
        if self.on_close_callback:
            self.on_close_callback()

    def reset_billing_form(self):
        self.cart = []
        self.refresh_cart_table()
        self.customer_name_var.set("")
        self.mobile_var.set("")
        self.email_var.set("")
        self.address_var.set("")
        self.discount_var.set("0")
        self.gst_var.set("5")
        self.qty_var.set("1")
        self.product_var.set("")
        self.price_var.set("")
        self.calculate_totals()
        self.generate_new_bill_no()

    # =====================================================
    # PDF / TXT EXPORT
    # =====================================================
    def save_bill_pdf(self, bill_data):
        file_path = os.path.join(BILLS_DIR, f"{bill_data['bill_no']}.pdf")
        doc = SimpleDocTemplate(file_path, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "TitleStyle", parent=styles["Title"], fontSize=20, textColor=rl_colors.HexColor("#1F2A44")
        )
        center_style = ParagraphStyle("CenterStyle", parent=styles["Normal"], alignment=TA_CENTER)
        normal_style = styles["Normal"]

        elements = []
        elements.append(Paragraph("SMART BILLING SYSTEM", title_style))
        elements.append(Paragraph("Final Year College Project Invoice", center_style))
        elements.append(Spacer(1, 12))

        info_table_data = [
            ["Bill No:", bill_data["bill_no"], "Date:", bill_data["bill_date"]],
            ["Customer:", bill_data["customer_name"], "Mobile:", bill_data["mobile"]],
            ["Email:", bill_data["email"] or "-", "Address:", bill_data["address"] or "-"],
        ]
        info_table = Table(info_table_data, colWidths=[60, 170, 60, 170])
        info_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 15))

        item_data = [["#", "Product Name", "Qty", "Price (Rs.)", "Total (Rs.)"]]
        for i, item in enumerate(bill_data["items"], start=1):
            item_data.append([
                str(i), item["name"], str(item["qty"]),
                f"{item['price']:.2f}", f"{item['total']:.2f}"
            ])

        item_table = Table(item_data, colWidths=[30, 220, 60, 90, 90])
        item_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor("#1F2A44")),
            ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, rl_colors.HexColor("#D5DBE3")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [rl_colors.white, rl_colors.HexColor("#F4F6F9")]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(item_table)
        elements.append(Spacer(1, 15))

        totals_data = [
            ["Subtotal:", f"Rs. {bill_data['subtotal']:.2f}"],
            [f"GST ({bill_data['gst_percent']}%):", f"Rs. {bill_data['gst_amount']:.2f}"],
            ["Discount:", f"Rs. {bill_data['discount']:.2f}"],
            ["Grand Total:", f"Rs. {bill_data['grand_total']:.2f}"],
        ]
        totals_table = Table(totals_data, colWidths=[400, 90])
        totals_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, -1), (-1, -1), 13),
            ("TEXTCOLOR", (0, -1), (-1, -1), rl_colors.HexColor("#27AE60")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("LINEABOVE", (0, -1), (-1, -1), 1, rl_colors.HexColor("#1F2A44")),
        ]))
        elements.append(totals_table)
        elements.append(Spacer(1, 30))

        thank_you_style = ParagraphStyle(
            "ThankYou", parent=styles["Normal"], alignment=TA_CENTER,
            fontSize=12, textColor=rl_colors.HexColor("#1F2A44")
        )
        elements.append(Paragraph("Thank you for shopping with us!", thank_you_style))
        elements.append(Paragraph("Visit Again", center_style))

        doc.build(elements)
        return file_path

    def save_bill_txt(self, bill_data):
        file_path = os.path.join(BILLS_DIR, f"{bill_data['bill_no']}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("=" * 50 + "\n")
            f.write("           SMART BILLING SYSTEM\n")
            f.write("=" * 50 + "\n")
            f.write(f"Bill No   : {bill_data['bill_no']}\n")
            f.write(f"Date      : {bill_data['bill_date']}\n")
            f.write(f"Customer  : {bill_data['customer_name']}\n")
            f.write(f"Mobile    : {bill_data['mobile']}\n")
            f.write(f"Email     : {bill_data['email'] or '-'}\n")
            f.write(f"Address   : {bill_data['address'] or '-'}\n")
            f.write("-" * 50 + "\n")
            f.write(f"{'Product':<20}{'Qty':<6}{'Price':<10}{'Total':<10}\n")
            f.write("-" * 50 + "\n")
            for item in bill_data["items"]:
                f.write(
                    f"{item['name']:<20}{item['qty']:<6}{item['price']:<10.2f}{item['total']:<10.2f}\n"
                )
            f.write("-" * 50 + "\n")
            f.write(f"Subtotal            : Rs. {bill_data['subtotal']:.2f}\n")
            f.write(f"GST ({bill_data['gst_percent']}%)          : Rs. {bill_data['gst_amount']:.2f}\n")
            f.write(f"Discount            : Rs. {bill_data['discount']:.2f}\n")
            f.write(f"Grand Total         : Rs. {bill_data['grand_total']:.2f}\n")
            f.write("=" * 50 + "\n")
            f.write("     Thank you for shopping with us!\n")
            f.write("=" * 50 + "\n")
        return file_path

    # =====================================================
    # SEARCH / REPRINT BILL
    # =====================================================
    def open_search_bill(self):
        SearchBillWindow(self.win, self.db, self.save_bill_pdf, self.save_bill_txt)

    def close_window(self):
        if self.on_close_callback:
            self.on_close_callback()
        self.win.destroy()


class SearchBillWindow:
    """Toplevel window to search a previous bill by bill number and reprint it."""

    def __init__(self, parent, db, pdf_saver, txt_saver):
        self.parent = parent
        self.db = db
        self.pdf_saver = pdf_saver
        self.txt_saver = txt_saver

        self.win = tk.Toplevel(parent)
        self.win.title("Search Bill")
        self.win.configure(bg=COLORS["bg"])
        center_window(self.win, 700, 550)
        self.win.transient(parent)
        self.win.grab_set()

        self.build_ui()

    def build_ui(self):
        top = tk.Frame(self.win, bg=COLORS["bg"])
        top.pack(fill="x", padx=15, pady=15)

        tk.Label(
            top, text="Enter Bill No:", font=FONTS["label_bold"], bg=COLORS["bg"]
        ).pack(side="left")

        self.bill_no_entry = tk.Entry(top, font=FONTS["label"], width=25)
        self.bill_no_entry.pack(side="left", padx=10, ipady=4)

        tk.Button(
            top, text="Search", font=FONTS["button"], bg=COLORS["accent"],
            fg=COLORS["text_light"], relief="flat", cursor="hand2",
            command=self.search_bill
        ).pack(side="left", padx=5)

        self.result_frame = tk.Frame(self.win, bg=COLORS["card_bg"], highlightbackground=COLORS["border"],
                                      highlightthickness=1)
        self.result_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.info_label = tk.Label(
            self.result_frame, text="Search for a bill to view details.",
            font=FONTS["label"], bg=COLORS["card_bg"], fg=COLORS["text_muted"], justify="left"
        )
        self.info_label.pack(anchor="w", padx=15, pady=10)

        columns = ("name", "qty", "price", "total")
        self.item_tree = ttk.Treeview(self.result_frame, columns=columns, show="headings", height=8)
        for col, text in zip(columns, ["Product", "Qty", "Price", "Total"]):
            self.item_tree.heading(col, text=text)
            self.item_tree.column(col, anchor="center", width=120)
        self.item_tree.pack(fill="both", expand=True, padx=15, pady=10)

        self.reprint_btn = tk.Button(
            self.result_frame, text="Reprint Bill (Regenerate PDF & TXT)", font=FONTS["button"],
            bg=COLORS["success"], fg=COLORS["text_light"], relief="flat", cursor="hand2",
            command=self.reprint_bill, state="disabled"
        )
        self.reprint_btn.pack(pady=10)

        self.current_bill = None

    def search_bill(self):
        bill_no = self.bill_no_entry.get().strip()
        if not validate_not_empty(bill_no):
            show_error("Validation Error", "Please enter a bill number.")
            return

        bill = self.db.get_bill_by_no(bill_no)
        if not bill:
            show_error("Not Found", f"No bill found with number '{bill_no}'.")
            self.reprint_btn.config(state="disabled")
            return

        items = self.db.get_items_by_bill(bill_no)

        (_id, b_no, cust_name, mobile, email, address, subtotal,
         gst_percent, gst_amount, discount, grand_total, bill_date) = bill

        self.info_label.config(
            text=(
                f"Bill No: {b_no}   |   Date: {bill_date}\n"
                f"Customer: {cust_name}   |   Mobile: {mobile}\n"
                f"Subtotal: {format_currency(subtotal)}   |   "
                f"GST ({gst_percent}%): {format_currency(gst_amount)}   |   "
                f"Discount: {format_currency(discount)}   |   "
                f"Grand Total: {format_currency(grand_total)}"
            )
        )

        for row in self.item_tree.get_children():
            self.item_tree.delete(row)
        for item in items:
            _iid, i_bill_no, p_name, qty, price, total = item
            self.item_tree.insert("", "end", values=(p_name, qty, f"{price:.2f}", f"{total:.2f}"))

        self.current_bill = {
            "bill_no": b_no, "customer_name": cust_name, "mobile": mobile,
            "email": email, "address": address, "subtotal": subtotal,
            "gst_percent": gst_percent, "gst_amount": gst_amount, "discount": discount,
            "grand_total": grand_total, "bill_date": bill_date,
            "items": [
                {"name": i[2], "qty": i[3], "price": i[4], "total": i[5]} for i in items
            ],
        }
        self.reprint_btn.config(state="normal")

    def reprint_bill(self):
        if not self.current_bill:
            return
        pdf_path = self.pdf_saver(self.current_bill)
        txt_path = self.txt_saver(self.current_bill)
        show_success("Reprint Successful", f"Bill regenerated:\n{pdf_path}\n{txt_path}")
