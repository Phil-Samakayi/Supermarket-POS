"""UserRole: the three actors this project's use cases are written
against.

Matches the book's own NextGen POS actor list exactly: Cashier
(Process Sale, Handle Returns — Register), Manager/Owner (Reporting,
Manage Inventory — InventoryManager), and "System administrator:
manage users, manage security, manage system tables" (Manage Users —
UserManager, this package).
"""
from __future__ import annotations

from enum import Enum


class UserRole(Enum):
    CASHIER = "cashier"
    MANAGER = "manager"
    ADMINISTRATOR = "administrator"
