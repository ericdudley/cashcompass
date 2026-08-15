from __future__ import annotations

from fasthtml.common import *

from src.components.dashboard import dashboard_page
from src.components.layout import page_layout
from src.services.account import AccountService
from src.services.category import CategoryService
from src.services.dashboard import DashboardMetricsService
from src.services.transaction import TransactionService


def register(rt, acct_svc: AccountService, cat_svc: CategoryService, txn_svc: TransactionService):
    dashboard_svc = DashboardMetricsService(txn_svc)

    @rt("/dashboard", methods=["GET"])
    def get(req: Request):
        accounts = acct_svc.list()
        categories = cat_svc.list()
        data = dashboard_svc.build(req.query_params, accounts, categories)
        return page_layout("dashboard", *dashboard_page(data))
