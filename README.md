# Smart Billing System

A complete, professional desktop billing / invoicing application built with
**Python 3, Tkinter, SQLite3 and ReportLab**. Designed as a Final Year
College Project with clean, modular, object-oriented code.

## Features

- **Login System** — Admin authentication (username/password) with logout
- **Dashboard** — Total products, total bills, today's sales, total revenue, quick navigation
- **Product Management** — Add / Update / Delete / Search products, auto-generated product codes, live stock status, Treeview table
- **Customer Details** — Name, mobile, email (optional), address (optional)
- **Billing Section** — Product dropdown auto-loaded from DB, auto-filled price, add/remove/edit cart items, multiple products per bill
- **GST Calculation** — 5% / 12% / 18% GST options, discount, subtotal & grand total
- **Bill Generation** — Auto bill number, date & time, full invoice details, thank-you message
- **Search Bill** — Search by bill number, view and reprint previous bills
- **Save Bill** — Saved to SQLite database, exported as PDF and as a plain text file
- **Print Bill** — Professional ReportLab-generated PDF invoice layout
- **Reports** — Daily sales, monthly sales, total revenue, bill count, top-selling products
- **Validation** — Empty field checks, numeric validation, mobile number validation, clear error/success messages

## Project Structure

```
Billing_System/
│── main.py          # Application entry point
│── login.py         # Login window & authentication
│── dashboard.py      # Main dashboard with stats & navigation
│── products.py       # Product management (CRUD)
│── billing.py         # Billing, cart, GST, PDF/TXT invoice generation, bill search
│── reports.py         # Sales reports & analytics
│── database.py        # SQLite3 database layer (auto-creates all tables)
│── utils.py           # Shared constants, validation & formatting helpers
│── requirements.txt   # Python dependencies
│── billing.db          # SQLite database (created automatically on first run)
│── bills/              # Generated PDF & TXT invoices
│── images/             # Icons / images (optional)
```

## Setup & Run

1. Make sure you have **Python 3.8+** installed.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   > Tkinter and sqlite3 ship with standard Python installations. On some
   > Linux distributions you may need to install Tkinter separately:
   > `sudo apt-get install python3-tk`
3. Run the application:
   ```
   python main.py
   ```

## Default Login

```
Username: admin
Password: admin123
```

The database (`billing.db`) and the default admin account are created
automatically the first time the application is run.

## Database Schema

- **products**: id, product_code, name, category, price, quantity
- **bills**: id, bill_no, customer_name, mobile, email, address, subtotal, gst_percent, gst_amount, discount, grand_total, bill_date
- **bill_items**: id, bill_no, product_name, quantity, price, total
- **users**: id, username, password (hashed), role

## Notes

- Invoices are saved automatically to the `bills/` folder in both `.pdf`
  and `.txt` formats, named after the bill number (e.g. `BILL0001.pdf`).
- Product stock is automatically reduced when a bill is generated.
- All monetary values are displayed in Indian Rupees (Rs.).
