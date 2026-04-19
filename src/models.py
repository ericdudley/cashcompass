from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Account:
    id: int = 0
    label: str = ""
    account_type: str = "net_worth"
    is_archived: bool = False
    created_at: str = ""
    updated_at: str = ""


@dataclass
class Category:
    id: int = 0
    label: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class Transaction:
    id: int = 0
    iso8601: str = ""
    date: str = ""
    amount: int = 0
    label: str = ""
    account_id: Optional[int] = None
    account_label: str = ""
    category_id: Optional[int] = None
    category_label: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class TransactionFilter:
    date_from: str = ""
    date_to: str = ""
    label: str = ""
    account_ids: list = field(default_factory=list)
    category_ids: list = field(default_factory=list)
    account_type: str = ""


@dataclass
class MonthSum:
    month: str = ""
    amount: int = 0


@dataclass
class AccountMonthBalance:
    account_id: int = 0
    account_label: str = ""
    month: str = ""
    balance: int = 0
