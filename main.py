"""
main.py
-------
Entry point for the Smart Billing System application.
Initializes the database, shows the login screen, and on
successful login launches the main dashboard.

Run with:
    python main.py
"""

import tkinter as tk
from database import Database
from login import LoginWindow
from dashboard import Dashboard


class SmartBillingApp:
    """Top-level application controller that manages screen transitions."""

    def __init__(self):
        self.db = Database()
        self.root = tk.Tk()
        self.show_login()

    def show_login(self):
        """Clears the root window and displays the login screen."""
        for widget in self.root.winfo_children():
            widget.destroy()
        LoginWindow(self.root, self.db, on_success=self.show_dashboard)

    def show_dashboard(self, username):
        """Clears the root window and displays the main dashboard."""
        for widget in self.root.winfo_children():
            widget.destroy()
        Dashboard(self.root, self.db, username, on_logout=self.show_login)

    def run(self):
        self.root.mainloop()
        self.db.close()


if __name__ == "__main__":
    app = SmartBillingApp()
    app.run()
