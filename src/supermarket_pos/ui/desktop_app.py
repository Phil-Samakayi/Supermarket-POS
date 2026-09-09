"""
Desktop POS application (Tkinter)
Features:
- Login screen (Taurai / Sally)
- Process Sale (with product dropdown + remove item)
- Receive Stock
- Improved Sales Report
- Stock Report
- Printable receipt after payment
- New Item ID format: SKU-01-001
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
from datetime import datetime
from typing import Optional

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.payment_declined_error import PaymentDeclinedError
from supermarket_pos.domain.product.exceptions import ProductNotFoundError
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.store import Store
from supermarket_pos.domain.users.user import User


class DesktopPOSApp:
    def __init__(self, store: Store) -> None:
        self.store = store
        self.register = store.register
        self.current_user: Optional[User] = None

        self.root = tk.Tk()
        self.root.title(f"{store.name} — Desktop POS")
        self.root.geometry("1100x720")
        self.root.minsize(1000, 650)

        # First show login
        self.root.withdraw()
        if not self._show_login():
            self.root.destroy()
            return

        self.root.deiconify()
        self._build_ui()
        self._new_sale()

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def _show_login(self) -> bool:
        """Returns True if login succeeded."""
        login = tk.Toplevel()
        login.title("Login — Supermarket POS")
        login.geometry("360x220")
        login.resizable(False, False)
        login.grab_set()

        # Center the window
        login.update_idletasks()
        x = (login.winfo_screenwidth() // 2) - 180
        y = (login.winfo_screenheight() // 2) - 110
        login.geometry(f"+{x}+{y}")

        ttk.Label(login, text="Supermarket POS Login", font=("Segoe UI", 14, "bold")).pack(pady=(20, 15))

        form = ttk.Frame(login, padding=10)
        form.pack()

        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky="e", pady=6, padx=5)
        username_var = tk.StringVar(value="Taurai")
        username_entry = ttk.Entry(form, textvariable=username_var, width=22)
        username_entry.grid(row=0, column=1, pady=6)

        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky="e", pady=6, padx=5)
        password_var = tk.StringVar(value="Sally")
        password_entry = ttk.Entry(form, textvariable=password_var, show="*", width=22)
        password_entry.grid(row=1, column=1, pady=6)

        result = {"ok": False}

        def try_login(event=None):
            username = username_var.get().strip()
            password = password_var.get()
            try:
                user = self.store.authenticate(username, password)
                self.current_user = user
                result["ok"] = True
                login.destroy()
            except Exception as e:
                messagebox.showerror("Login failed", str(e), parent=login)

        ttk.Button(form, text="Login", command=try_login).grid(row=2, column=0, columnspan=2, pady=15)
        password_entry.bind("<Return>", try_login)
        username_entry.focus_set()

        # Create the administrator if no users exist yet
        try:
            self.store.users.bootstrap_administrator("Taurai", "Sally")
        except Exception:
            pass  # already exists

        login.wait_window()
        return result["ok"]

    # ------------------------------------------------------------------
    # Main UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # Top bar with logged-in user
        top = ttk.Frame(self.root, padding=(10, 6))
        top.pack(fill=tk.X)
        ttk.Label(top, text=self.store.name, font=("Segoe UI", 13, "bold")).pack(side=tk.LEFT)
        ttk.Label(top, text=f"Logged in as: {self.current_user.username}").pack(side=tk.RIGHT)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self.checkout_frame = ttk.Frame(self.notebook)
        self.receive_frame = ttk.Frame(self.notebook)
        self.sales_report_frame = ttk.Frame(self.notebook)
        self.stock_report_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.checkout_frame, text="  Checkout  ")
        self.notebook.add(self.receive_frame, text="  Receive Stock  ")
        self.notebook.add(self.sales_report_frame, text="  Sales Report  ")
        self.notebook.add(self.stock_report_frame, text="  Stock Report  ")

        self._build_checkout_tab()
        self._build_receive_tab()
        self._build_sales_report_tab()
        self._build_stock_report_tab()

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    # ------------------------------------------------------------------
    # Checkout Tab
    # ------------------------------------------------------------------

    def _build_checkout_tab(self) -> None:
        main = ttk.Frame(self.checkout_frame, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(main)
        header.pack(fill=tk.X, pady=(0, 8))
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(header, textvariable=self.status_var).pack(side=tk.LEFT)

        body = ttk.Frame(main)
        body.pack(fill=tk.BOTH, expand=True)

        # Left
        left = ttk.Frame(body)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        entry_frame = ttk.LabelFrame(left, text="Add Item", padding=8)
        entry_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(entry_frame, text="Item:").grid(row=0, column=0, sticky="w")

        product_options = []
        self._product_map = {}
        for desc in self.store.catalog.all_products():
            display = f"{desc.item_id}  —  {desc.description}  (K {desc.price})"
            product_options.append(display)
            self._product_map[display] = desc.item_id

        self.item_var = tk.StringVar()
        self.item_combo = ttk.Combobox(
            entry_frame, textvariable=self.item_var,
            values=product_options, width=48, state="normal"
        )
        self.item_combo.grid(row=0, column=1, padx=4, sticky="ew")
        self.item_combo.bind("<Return>", lambda e: self._add_item())
        self.item_combo.bind("<<ComboboxSelected>>", lambda e: self._add_item())

        ttk.Label(entry_frame, text="Qty:").grid(row=0, column=2, padx=(10, 0))
        self.qty_var = tk.StringVar(value="1")
        qty_entry = ttk.Entry(entry_frame, textvariable=self.qty_var, width=6)
        qty_entry.grid(row=0, column=3, padx=4)
        qty_entry.bind("<Return>", lambda e: self._add_item())

        ttk.Button(entry_frame, text="Add Item", command=self._add_item).grid(row=0, column=4, padx=6)
        entry_frame.columnconfigure(1, weight=1)

        # Cart
        cart_frame = ttk.LabelFrame(left, text="Cart", padding=8)
        cart_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("sku", "description", "qty", "price", "subtotal")
        self.tree = ttk.Treeview(cart_frame, columns=cols, show="headings", height=14)
        for col, text, w, anchor in [
            ("sku", "SKU", 110, "w"),
            ("description", "Description", 220, "w"),
            ("qty", "Qty", 50, "center"),
            ("price", "Unit Price", 90, "e"),
            ("subtotal", "Subtotal", 90, "e"),
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor=anchor)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(cart_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Remove button
        ttk.Button(left, text="Remove Selected Item", command=self._remove_selected_item).pack(pady=6, anchor="w")

        # Right panel
        right = ttk.Frame(body, width=280)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        right.pack_propagate(False)

        totals = ttk.LabelFrame(right, text="Totals", padding=10)
        totals.pack(fill=tk.X, pady=(0, 10))

        self.items_var = tk.StringVar(value="0 items")
        self.subtotal_var = tk.StringVar(value="K 0.00")
        self.total_var = tk.StringVar(value="K 0.00")

        ttk.Label(totals, text="Items:").grid(row=0, column=0, sticky="w")
        ttk.Label(totals, textvariable=self.items_var).grid(row=0, column=1, sticky="e")
        ttk.Label(totals, text="Subtotal:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Label(totals, textvariable=self.subtotal_var).grid(row=1, column=1, sticky="e")
        ttk.Separator(totals, orient="horizontal").grid(row=2, column=0, columnspan=2, sticky="ew", pady=6)
        ttk.Label(totals, text="TOTAL:", font=("Segoe UI", 12, "bold")).grid(row=3, column=0, sticky="w")
        ttk.Label(totals, textvariable=self.total_var, font=("Segoe UI", 14, "bold")).grid(row=3, column=1, sticky="e")
        totals.columnconfigure(1, weight=1)

        pay = ttk.LabelFrame(right, text="Payment", padding=10)
        pay.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(pay, text="Amount tendered:").pack(anchor="w")
        self.tendered_var = tk.StringVar()
        ttk.Entry(pay, textvariable=self.tendered_var).pack(fill=tk.X, pady=4)

        ttk.Button(pay, text="Pay Cash", command=self._pay_cash).pack(fill=tk.X, pady=3)
        ttk.Button(pay, text="Pay MTN MoMo", command=lambda: self._pay_mobile("mtn")).pack(fill=tk.X, pady=3)
        ttk.Button(pay, text="Pay Airtel Money", command=lambda: self._pay_mobile("airtel")).pack(fill=tk.X, pady=3)
        ttk.Button(pay, text="Pay Card", command=self._pay_card).pack(fill=tk.X, pady=3)

        actions = ttk.Frame(right)
        actions.pack(fill=tk.X)
        ttk.Button(actions, text="End Sale", command=self._end_sale).pack(fill=tk.X, pady=3)
        ttk.Button(actions, text="New Sale / Clear", command=self._new_sale).pack(fill=tk.X, pady=3)

        self.item_combo.focus_set()

    # ------------------------------------------------------------------
    # Receive Stock Tab
    # ------------------------------------------------------------------

    def _build_receive_tab(self) -> None:
        frame = ttk.Frame(self.receive_frame, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Receive Stock", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 12))

        form = ttk.LabelFrame(frame, text="New Delivery", padding=12)
        form.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(form, text="Item:").grid(row=0, column=0, sticky="w", pady=4)
        product_options = [f"{d.item_id} — {d.description}" for d in self.store.catalog.all_products()]
        self.receive_item_var = tk.StringVar()
        self.receive_combo = ttk.Combobox(form, textvariable=self.receive_item_var, values=product_options, width=45)
        self.receive_combo.grid(row=0, column=1, padx=8, pady=4, sticky="ew")

        ttk.Label(form, text="Quantity received:").grid(row=1, column=0, sticky="w", pady=4)
        self.receive_qty_var = tk.StringVar(value="10")
        ttk.Entry(form, textvariable=self.receive_qty_var, width=12).grid(row=1, column=1, sticky="w", padx=8, pady=4)

        ttk.Button(form, text="Receive Stock", command=self._receive_stock).grid(row=2, column=1, sticky="w", padx=8, pady=10)

        ttk.Label(frame, text="Current Stock Levels", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 6))
        cols = ("sku", "description", "qty")
        self.receive_tree = ttk.Treeview(frame, columns=cols, show="headings", height=12)
        self.receive_tree.heading("sku", text="SKU")
        self.receive_tree.heading("description", text="Description")
        self.receive_tree.heading("qty", text="On Hand")
        self.receive_tree.column("sku", width=120)
        self.receive_tree.column("description", width=300)
        self.receive_tree.column("qty", width=100, anchor="center")
        self.receive_tree.pack(fill=tk.BOTH, expand=True)

    def _receive_stock(self) -> None:
        selected = self.receive_item_var.get().strip()
        if not selected:
            messagebox.showwarning("Missing", "Please select an item.")
            return
        item_id = selected.split("—")[0].strip()
        try:
            qty = int(self.receive_qty_var.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid", "Quantity must be a positive number.")
            return

        try:
            new_qty = self.store.inventory.receive_stock(item_id, qty)
            messagebox.showinfo("Success", f"Received {qty} units of {item_id}.\nNew stock level: {new_qty}")
            self._refresh_receive_stock_list()
            self.receive_qty_var.set("10")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _refresh_receive_stock_list(self) -> None:
        for row in self.receive_tree.get_children():
            self.receive_tree.delete(row)
        for desc in self.store.catalog.all_products():
            qty = self.store.inventory.get_stock_level(desc.item_id)
            self.receive_tree.insert("", "end", values=(desc.item_id, desc.description, qty))

    # ------------------------------------------------------------------
    # Sales Report Tab
    # ------------------------------------------------------------------

    def _build_sales_report_tab(self) -> None:
        frame = ttk.Frame(self.sales_report_frame, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(frame)
        header.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(header, text="Sales Report", font=("Segoe UI", 13, "bold")).pack(side=tk.LEFT)
        ttk.Button(header, text="Refresh", command=self._load_sales_report).pack(side=tk.RIGHT)

        self.sales_text = tk.Text(frame, height=28, wrap="word", font=("Consolas", 10), bg="#fafafa")
        self.sales_text.pack(fill=tk.BOTH, expand=True)

    def _load_sales_report(self) -> None:
        report = self.store.sales_summary_report()
        top_items = self.store.top_selling_items(limit=10)

        self.sales_text.delete("1.0", tk.END)

        lines = [
            "╔══════════════════════════════════════════════════╗",
            "║               SALES SUMMARY REPORT               ║",
            "╚══════════════════════════════════════════════════╝",
            "",
            f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"  Branch   : {self.store.name}",
            "",
            "────────────────────────────────────────────────────",
            f"  Total Sales Value     :  {report.total_sales}",
            f"  Total Returns Value   :  {report.total_returns}",
            f"  Net Revenue           :  {report.net_revenue}",
            f"  Number of Sales       :  {report.number_of_sales}",
            f"  Number of Returns     :  {report.number_of_returns}",
            "────────────────────────────────────────────────────",
            "",
            "  TOP SELLING ITEMS",
            "  ─────────────────",
        ]

        if not top_items:
            lines.append("  (no sales recorded yet)")
        else:
            for i, item in enumerate(top_items, 1):
                lines.append(
                    f"  {i:2}. {item.item_id:<12}  qty: {item.quantity_sold:<5}  revenue: {item.revenue}"
                )

        lines.append("")
        lines.append("════════════════════════════════════════════════════")

        self.sales_text.insert(tk.END, "\n".join(lines))

    # ------------------------------------------------------------------
    # Stock Report Tab
    # ------------------------------------------------------------------

    def _build_stock_report_tab(self) -> None:
        frame = ttk.Frame(self.stock_report_frame, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(frame)
        header.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(header, text="Stock Levels", font=("Segoe UI", 13, "bold")).pack(side=tk.LEFT)
        ttk.Button(header, text="Refresh", command=self._load_stock_report).pack(side=tk.RIGHT)

        cols = ("sku", "description", "qty", "status")
        self.stock_tree = ttk.Treeview(frame, columns=cols, show="headings", height=22)
        self.stock_tree.heading("sku", text="SKU")
        self.stock_tree.heading("description", text="Description")
        self.stock_tree.heading("qty", text="On Hand")
        self.stock_tree.heading("status", text="Status")
        self.stock_tree.column("sku", width=120)
        self.stock_tree.column("description", width=280)
        self.stock_tree.column("qty", width=90, anchor="center")
        self.stock_tree.column("status", width=100, anchor="center")
        self.stock_tree.pack(fill=tk.BOTH, expand=True)

    def _load_stock_report(self) -> None:
        for row in self.stock_tree.get_children():
            self.stock_tree.delete(row)

        report = self.store.stock_summary_report(low_stock_threshold=10)
        for row in report.rows:
            status = "LOW STOCK" if row.is_low_stock else "OK"
            self.stock_tree.insert("", "end", values=(
                row.item_id, row.description, row.quantity_on_hand, status
            ))

    # ------------------------------------------------------------------
    # Checkout logic
    # ------------------------------------------------------------------

    def _new_sale(self) -> None:
        self.register.make_new_sale()
        self._refresh_cart()
        self.status_var.set("New sale started")
        self.item_var.set("")
        self.qty_var.set("1")
        self.tendered_var.set("")
        self.item_combo.focus_set()

    def _add_item(self) -> None:
        selected = self.item_var.get().strip()
        if not selected:
            return

        item_id = self._product_map.get(selected)
        if item_id is None:
            item_id = selected.split("—")[0].strip() if "—" in selected else selected

        try:
            qty = int(self.qty_var.get() or "1")
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid quantity", "Quantity must be a positive number.")
            return

        try:
            self.register.enter_item(item_id, qty)
            self.item_var.set("")
            self.qty_var.set("1")
            self.status_var.set(f"Added {item_id} × {qty}")
            self._refresh_cart()
            self.item_combo.focus_set()
        except ProductNotFoundError:
            messagebox.showerror("Not found", f"No product with ID '{item_id}'")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _remove_selected_item(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select an item in the cart to remove.")
            return

        sale = self.register.current_sale
        if sale is None or sale.is_complete():
            messagebox.showwarning("Cannot remove", "You can only remove items before ending the sale.")
            return

        index = self.tree.index(selected[0])
        lines = list(sale.line_items)
        if index >= len(lines):
            return

        # Rebuild sale without the selected item
        self.register.make_new_sale()
        for i, line in enumerate(lines):
            if i != index:
                self.register.enter_item(line.description.item_id, line.quantity)

        self.status_var.set("Item removed")
        self._refresh_cart()

    def _end_sale(self) -> None:
        sale = self.register.current_sale
        if not sale or not sale.line_items:
            messagebox.showwarning("Empty", "Add items first.")
            return
        if not sale.is_complete():
            total = self.register.end_sale()
            self.status_var.set(f"Sale complete — Total: {total}")
        self._refresh_cart()

    def _require_complete(self) -> bool:
        sale = self.register.current_sale
        if not sale or not sale.line_items:
            messagebox.showwarning("No sale", "Start a sale and add items first.")
            return False
        if not sale.is_complete():
            self.register.end_sale()
        return True

    def _show_receipt(self, payment_method: str, amount: Money, change: Optional[Money] = None) -> None:
        sale = self.register.current_sale
        if not sale:
            return

        receipt = tk.Toplevel(self.root)
        receipt.title("Receipt")
        receipt.geometry("380x520")
        receipt.resizable(False, False)

        text = tk.Text(receipt, font=("Consolas", 10), wrap="word", bg="white")
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        lines = [
            "========================================",
            f"       {self.store.name}",
            f"       {self.store.address}",
            "========================================",
            f"Date   : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Cashier: {self.current_user.username if self.current_user else 'N/A'}",
            "----------------------------------------",
        ]

        for line in sale.line_items:
            lines.append(f"{line.description.description[:22]:<22} {line.quantity:>3} x {line.description.price}")
            lines.append(f"{'':>30}{line.get_subtotal():>10}")

        lines += [
            "----------------------------------------",
            f"{'TOTAL':<30}{sale.get_total():>10}",
            f"Payment : {payment_method}",
            f"Tendered: {amount}",
        ]
        if change is not None:
            lines.append(f"Change  : {change}")

        lines += [
            "========================================",
            "          Thank you for shopping!",
            "========================================",
        ]

        text.insert(tk.END, "\n".join(lines))
        text.config(state="disabled")

        ttk.Button(receipt, text="Close", command=receipt.destroy).pack(pady=8)

    def _pay_cash(self) -> None:
        if not self._require_complete():
            return
        tendered = self.tendered_var.get().strip()
        if not tendered:
            tendered = str(self.register.current_sale.get_total().amount)
        try:
            change = self.register.make_cash_payment(Money(tendered))
            self._show_receipt("Cash", Money(tendered), change)
            self.status_var.set(f"Paid. Change: {change}")
            self._new_sale()
        except Exception as e:
            messagebox.showerror("Payment failed", str(e))

    def _pay_mobile(self, provider: str) -> None:
        if not self._require_complete():
            return
        phone = simpledialog.askstring("Mobile Money", "Customer phone number:", initialvalue="0977123456")
        if not phone:
            return
        total = self.register.current_sale.get_total()
        try:
            self.register.make_mobile_money_payment(provider, phone, total)
            self._show_receipt(f"{provider.upper()} Mobile Money", total)
            self.status_var.set(f"{provider.upper()} payment accepted")
            self._new_sale()
        except PaymentDeclinedError as e:
            messagebox.showerror("Declined", str(e))
        except Exception as e:
            messagebox.showerror("Failed", str(e))

    def _pay_card(self) -> None:
        if not self._require_complete():
            return
        ref = simpledialog.askstring("Card", "Card reference:", initialvalue="4111111111111111")
        if not ref:
            return
        total = self.register.current_sale.get_total()
        try:
            self.register.make_card_payment(ref, total)
            self._show_receipt("Card", total)
            self.status_var.set("Card payment accepted")
            self._new_sale()
        except PaymentDeclinedError as e:
            messagebox.showerror("Declined", str(e))
        except Exception as e:
            messagebox.showerror("Failed", str(e))

    def _refresh_cart(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)

        sale = self.register.current_sale
        if not sale:
            self.items_var.set("0 items")
            self.subtotal_var.set("K 0.00")
            self.total_var.set("K 0.00")
            return

        total_qty = 0
        for line in sale.line_items:
            total_qty += line.quantity
            self.tree.insert("", "end", values=(
                line.description.item_id,
                line.description.description,
                line.quantity,
                str(line.description.price),
                str(line.get_subtotal()),
            ))

        self.items_var.set(f"{total_qty} item{'s' if total_qty != 1 else ''}")
        self.subtotal_var.set(str(sale.get_subtotal()))
        self.total_var.set(str(sale.get_total()))

    def _on_tab_changed(self, event=None) -> None:
        tab = self.notebook.tab(self.notebook.select(), "text").strip()
        if tab == "Sales Report":
            self._load_sales_report()
        elif tab == "Stock Report":
            self._load_stock_report()
        elif tab == "Receive Stock":
            self._refresh_receive_stock_list()

    def run(self) -> None:
        self.root.mainloop()


def create_demo_store() -> Store:
    store = Store("Pick n Pay POS — Demo Branch", "Lusaka, Zambia")

    products = [
        # Category 01 - Mealie Meal & Staples
        ("SKU-01-001", "2kg Mealie Meal", "85.00"),
        ("SKU-01-002", "5kg Mealie Meal", "195.00"),
        ("SKU-01-003", "10kg Mealie Meal", "370.00"),

        # Category 02 - Cooking Oil
        ("SKU-02-001", "1L Cooking Oil", "65.50"),
        ("SKU-02-002", "2L Cooking Oil", "120.00"),

        # Category 03 - Bread & Bakery
        ("SKU-03-001", "Loaf of Bread", "18.00"),
        ("SKU-03-002", "Bread Rolls (6pk)", "25.00"),

        # Category 04 - Sugar
        ("SKU-04-001", "500g Sugar", "32.00"),
        ("SKU-04-002", "1kg Sugar", "58.00"),

        # Category 05 - Dairy
        ("SKU-05-001", "1L Fresh Milk", "22.50"),
        ("SKU-05-002", "500ml Yoghurt", "19.00"),

        # Category 06 - Other
        ("SKU-06-001", "Bar of Soap", "15.00"),
        ("SKU-06-002", "Pack of Eggs (12)", "45.00"),
        ("SKU-06-003", "2L Soft Drink", "28.00"),
    ]

    for item_id, desc, price in products:
        store.catalog.add_product(ProductDescription(item_id, desc, Money(price)))
        store.inventory.receive_stock(item_id, 50)   # starting stock of 50 each

    return store


def main() -> None:
    store = create_demo_store()
    app = DesktopPOSApp(store)
    app.run()


if __name__ == "__main__":
    main()