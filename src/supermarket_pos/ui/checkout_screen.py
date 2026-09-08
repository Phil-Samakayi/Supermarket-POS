"""Tkinter Process Sale checkout screen.

Implements ISaleObserver so the display refreshes automatically when
the Sale changes. Domain layer stays completely unaware of Tkinter.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.payment_declined_error import PaymentDeclinedError
from supermarket_pos.domain.product.exceptions import ProductNotFoundError
from supermarket_pos.domain.sales.sale import Sale
from supermarket_pos.domain.sales.sale_observer import ISaleObserver
from supermarket_pos.domain.store import Store


class CheckoutScreen(ISaleObserver):
    """Main cashier-facing Process Sale window."""

    def __init__(self, store: Store, root: Optional[tk.Tk] = None) -> None:
        self._store = store
        self._register = store.register
        self._owns_root = root is None
        self._root = root or tk.Tk()
        self._root.title(f"{store.name} — Checkout")
        self._root.geometry("900x620")
        self._root.minsize(800, 560)

        self._build_ui()
        self._new_sale()

    def _build_ui(self) -> None:
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Total.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Action.TButton", font=("Segoe UI", 11), padding=6)

        main = ttk.Frame(self._root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        # Header
        header = ttk.Frame(main)
        header.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(header, text=self._store.name, style="Title.TLabel").pack(side=tk.LEFT)
        self._status_var = tk.StringVar(value="Ready — start a new sale")
        ttk.Label(header, textvariable=self._status_var).pack(side=tk.RIGHT)

        # Body
        body = ttk.Frame(main)
        body.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(body)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Item entry
        entry_frame = ttk.LabelFrame(left, text="Scan / Enter Item", padding=8)
        entry_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(entry_frame, text="Item ID:").grid(row=0, column=0, sticky=tk.W)
        self._item_id_var = tk.StringVar()
        self._item_entry = ttk.Entry(entry_frame, textvariable=self._item_id_var, width=18)
        self._item_entry.grid(row=0, column=1, padx=4)
        self._item_entry.bind("<Return>", lambda e: self._on_add_item())

        ttk.Label(entry_frame, text="Qty:").grid(row=0, column=2, sticky=tk.W, padx=(8, 0))
        self._qty_var = tk.StringVar(value="1")
        qty_entry = ttk.Entry(entry_frame, textvariable=self._qty_var, width=6)
        qty_entry.grid(row=0, column=3, padx=4)
        qty_entry.bind("<Return>", lambda e: self._on_add_item())

        ttk.Button(
            entry_frame, text="Add Item", style="Action.TButton", command=self._on_add_item
        ).grid(row=0, column=4, padx=6)

        # Cart
        cart_frame = ttk.LabelFrame(left, text="Cart", padding=8)
        cart_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("item_id", "description", "qty", "price", "subtotal")
        self._tree = ttk.Treeview(cart_frame, columns=cols, show="headings", height=14)
        self._tree.heading("item_id", text="SKU")
        self._tree.heading("description", text="Description")
        self._tree.heading("qty", text="Qty")
        self._tree.heading("price", text="Unit Price")
        self._tree.heading("subtotal", text="Subtotal")
        self._tree.column("item_id", width=90)
        self._tree.column("description", width=220)
        self._tree.column("qty", width=50, anchor=tk.CENTER)
        self._tree.column("price", width=90, anchor=tk.E)
        self._tree.column("subtotal", width=90, anchor=tk.E)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(cart_frame, orient=tk.VERTICAL, command=self._tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.configure(yscrollcommand=scroll.set)

        # Right panel
        right = ttk.Frame(body, width=280)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        right.pack_propagate(False)

        total_frame = ttk.LabelFrame(right, text="Totals", padding=10)
        total_frame.pack(fill=tk.X, pady=(0, 10))

        self._subtotal_var = tk.StringVar(value="K 0.00")
        self._total_var = tk.StringVar(value="K 0.00")
        self._items_var = tk.StringVar(value="0 items")

        ttk.Label(total_frame, text="Items:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(total_frame, textvariable=self._items_var).grid(row=0, column=1, sticky=tk.E)
        ttk.Label(total_frame, text="Subtotal:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(total_frame, textvariable=self._subtotal_var).grid(row=1, column=1, sticky=tk.E)
        ttk.Separator(total_frame, orient=tk.HORIZONTAL).grid(
            row=2, column=0, columnspan=2, sticky=tk.EW, pady=6
        )
        ttk.Label(total_frame, text="TOTAL:", style="Total.TLabel").grid(row=3, column=0, sticky=tk.W)
        ttk.Label(total_frame, textvariable=self._total_var, style="Total.TLabel").grid(
            row=3, column=1, sticky=tk.E
        )
        total_frame.columnconfigure(1, weight=1)

        # Payment
        pay_frame = ttk.LabelFrame(right, text="Payment", padding=10)
        pay_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(pay_frame, text="Amount tendered:").pack(anchor=tk.W)
        self._tendered_var = tk.StringVar()
        self._tendered_entry = ttk.Entry(pay_frame, textvariable=self._tendered_var, width=18)
        self._tendered_entry.pack(fill=tk.X, pady=4)

        ttk.Button(pay_frame, text="Pay Cash", style="Action.TButton", command=self._on_pay_cash).pack(
            fill=tk.X, pady=3
        )
        ttk.Button(
            pay_frame, text="Pay Mobile Money (MTN)", style="Action.TButton",
            command=lambda: self._on_pay_mobile("mtn")
        ).pack(fill=tk.X, pady=3)
        ttk.Button(
            pay_frame, text="Pay Mobile Money (Airtel)", style="Action.TButton",
            command=lambda: self._on_pay_mobile("airtel")
        ).pack(fill=tk.X, pady=3)
        ttk.Button(pay_frame, text="Pay Card", style="Action.TButton", command=self._on_pay_card).pack(
            fill=tk.X, pady=3
        )

        # Actions
        action_frame = ttk.Frame(right)
        action_frame.pack(fill=tk.X)
        ttk.Button(
            action_frame, text="End Sale / Ready for Payment", style="Action.TButton",
            command=self._on_end_sale
        ).pack(fill=tk.X, pady=3)
        ttk.Button(action_frame, text="New Sale", style="Action.TButton", command=self._new_sale).pack(
            fill=tk.X, pady=3
        )
        ttk.Button(action_frame, text="Cancel / Void Sale", command=self._new_sale).pack(
            fill=tk.X, pady=3
        )

        self._item_entry.focus_set()

    def _new_sale(self) -> None:
        if self._register.current_sale is not None:
            self._register.current_sale.remove_observer(self)
        self._register.make_new_sale()
        self._register.current_sale.add_observer(self)
        self._refresh_display()
        self._status_var.set("New sale started — scan or enter items")
        self._item_id_var.set("")
        self._qty_var.set("1")
        self._tendered_var.set("")
        self._item_entry.focus_set()

    def _on_add_item(self) -> None:
        item_id = self._item_id_var.get().strip()
        if not item_id:
            return
        try:
            qty = int(self._qty_var.get().strip() or "1")
            if qty <= 0:
                raise ValueError("Quantity must be positive")
        except ValueError:
            messagebox.showerror("Invalid quantity", "Please enter a positive whole number.")
            return

        try:
            self._register.enter_item(item_id, qty)
            self._item_id_var.set("")
            self._qty_var.set("1")
            self._item_entry.focus_set()
            self._status_var.set(f"Added {item_id} × {qty}")
        except ProductNotFoundError:
            messagebox.showerror("Item not found", f"No product with ID '{item_id}'.")
        except ValueError as exc:
            messagebox.showerror("Cannot add item", str(exc))

    def _on_end_sale(self) -> None:
        sale = self._register.current_sale
        if sale is None or not sale.line_items:
            messagebox.showwarning("Empty sale", "Add at least one item first.")
            return
        if sale.is_complete():
            self._status_var.set("Sale already complete — choose a payment method")
            return
        total = self._register.end_sale()
        self._status_var.set(f"Sale complete — total {total}. Choose payment.")
        self._tendered_entry.focus_set()

    def _require_complete_sale(self) -> bool:
        sale = self._register.current_sale
        if sale is None or not sale.line_items:
            messagebox.showwarning("No sale", "Start a sale and add items first.")
            return False
        if not sale.is_complete():
            self._register.end_sale()
        return True

    def _on_pay_cash(self) -> None:
        if not self._require_complete_sale():
            return
        tendered_str = self._tendered_var.get().strip()
        if not tendered_str:
            tendered_str = str(self._register.current_sale.get_total().amount)
        try:
            tendered = Money(tendered_str)
            change = self._register.make_cash_payment(tendered)
            messagebox.showinfo(
                "Payment successful",
                f"Cash payment recorded.\n\nTendered: {tendered}\nChange due: {change}",
            )
            self._status_var.set(f"Cash paid. Change: {change}. Ready for next customer.")
            self._new_sale()
        except Exception as exc:
            messagebox.showerror("Payment failed", str(exc))

    def _on_pay_mobile(self, provider: str) -> None:
        if not self._require_complete_sale():
            return
        phone = self._ask_phone()
        if not phone:
            return
        total = self._register.current_sale.get_total()
        try:
            self._register.make_mobile_money_payment(provider, phone, total)
            messagebox.showinfo(
                "Payment successful",
                f"{provider.upper()} Mobile Money payment approved.\n\nAmount: {total}",
            )
            self._status_var.set(f"{provider.upper()} payment accepted. Ready for next customer.")
            self._new_sale()
        except PaymentDeclinedError as exc:
            messagebox.showerror("Payment declined", str(exc))
        except Exception as exc:
            messagebox.showerror("Payment failed", str(exc))

    def _on_pay_card(self) -> None:
        if not self._require_complete_sale():
            return
        card_ref = self._ask_card_ref()
        if not card_ref:
            return
        total = self._register.current_sale.get_total()
        try:
            self._register.make_card_payment(card_ref, total)
            messagebox.showinfo(
                "Payment successful",
                f"Card payment approved.\n\nAmount: {total}",
            )
            self._status_var.set("Card payment accepted. Ready for next customer.")
            self._new_sale()
        except PaymentDeclinedError as exc:
            messagebox.showerror("Payment declined", str(exc))
        except Exception as exc:
            messagebox.showerror("Payment failed", str(exc))

    def _ask_phone(self) -> Optional[str]:
        dialog = tk.Toplevel(self._root)
        dialog.title("Mobile Money Phone Number")
        dialog.geometry("320x140")
        dialog.transient(self._root)
        dialog.grab_set()
        ttk.Label(dialog, text="Customer phone number:").pack(pady=(16, 4))
        var = tk.StringVar(value="0977123456")
        entry = ttk.Entry(dialog, textvariable=var, width=22)
        entry.pack(pady=4)
        entry.focus_set()
        result: list[Optional[str]] = [None]

        def ok() -> None:
            result[0] = var.get().strip()
            dialog.destroy()

        def cancel() -> None:
            dialog.destroy()

        btn = ttk.Frame(dialog)
        btn.pack(pady=10)
        ttk.Button(btn, text="OK", command=ok).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn, text="Cancel", command=cancel).pack(side=tk.LEFT)
        entry.bind("<Return>", lambda e: ok())
        self._root.wait_window(dialog)
        return result[0]

    def _ask_card_ref(self) -> Optional[str]:
        dialog = tk.Toplevel(self._root)
        dialog.title("Card Reference")
        dialog.geometry("320x140")
        dialog.transient(self._root)
        dialog.grab_set()
        ttk.Label(dialog, text="Card / reference number:").pack(pady=(16, 4))
        var = tk.StringVar(value="4111111111111111")
        entry = ttk.Entry(dialog, textvariable=var, width=22)
        entry.pack(pady=4)
        entry.focus_set()
        result: list[Optional[str]] = [None]

        def ok() -> None:
            result[0] = var.get().strip()
            dialog.destroy()

        def cancel() -> None:
            dialog.destroy()

        btn = ttk.Frame(dialog)
        btn.pack(pady=10)
        ttk.Button(btn, text="OK", command=ok).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn, text="Cancel", command=cancel).pack(side=tk.LEFT)
        entry.bind("<Return>", lambda e: ok())
        self._root.wait_window(dialog)
        return result[0]

    def sale_updated(self, sale: Sale) -> None:
        self._refresh_display()

    def _refresh_display(self) -> None:
        for row in self._tree.get_children():
            self._tree.delete(row)

        sale = self._register.current_sale
        if sale is None:
            self._subtotal_var.set("K 0.00")
            self._total_var.set("K 0.00")
            self._items_var.set("0 items")
            return

        total_qty = 0
        for line in sale.line_items:
            total_qty += line.quantity
            self._tree.insert(
                "",
                tk.END,
                values=(
                    line.description.item_id,
                    line.description.description,
                    line.quantity,
                    str(line.description.price),
                    str(line.get_subtotal()),
                ),
            )

        self._subtotal_var.set(str(sale.get_subtotal()))
        self._total_var.set(str(sale.get_total()))
        self._items_var.set(f"{total_qty} item{'s' if total_qty != 1 else ''}")

    def run(self) -> None:
        self._root.mainloop()