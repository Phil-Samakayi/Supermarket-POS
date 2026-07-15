"""Cashier: the primary actor operating a Register."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Cashier:
    cashier_id: str
    name: str
