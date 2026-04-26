from __future__ import annotations

from dataclasses import dataclass

from src.models import Account
from src.repository.account import AccountRepository
from src.repository.transaction import TransactionRepository
from src.services.transaction import TransactionService


RECONCILIATION_LABEL = "Balance adjustment"


@dataclass
class ReconciliationRow:
    account: Account
    current_balance: int = 0


class ReconciliationService:
    def __init__(
        self,
        acct_repo: AccountRepository,
        txn_repo: TransactionRepository,
        txn_svc: TransactionService,
    ):
        self.acct_repo = acct_repo
        self.txn_repo = txn_repo
        self.txn_svc = txn_svc

    def list_rows(self) -> list[ReconciliationRow]:
        accounts = [
            acct for acct in self.acct_repo.list()
            if acct.account_type == "net_worth" and not acct.is_archived
        ]
        balances = self.txn_repo.balances_by_account([acct.id for acct in accounts])
        return [
            ReconciliationRow(account=acct, current_balance=balances.get(acct.id, 0))
            for acct in accounts
        ]

    def create_adjustments(self, latest_balance_cents: dict[int, int | None], today_iso: str) -> int:
        rows = self.list_rows()
        adjustments = []
        for row in rows:
            latest_cents = latest_balance_cents.get(row.account.id)
            if latest_cents is None:
                continue
            diff = latest_cents - row.current_balance
            if diff == 0:
                continue
            adjustments.append((
                today_iso,
                today_iso.replace("-", "_"),
                diff,
                RECONCILIATION_LABEL,
                row.account.id,
                row.account.label,
                None,
                "",
            ))
        return self.txn_svc.create_batch(adjustments)
