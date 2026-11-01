import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from fasthtml.common import fast_app
from starlette.testclient import TestClient

from src.db import Database, seed_if_empty
from src.repository.account import AccountRepository
from src.repository.category import CategoryRepository
from src.repository.transaction import TransactionRepository
from src.routes import accounts, reconciliation, transactions
from src.services.account import AccountService
from src.services.category import CategoryService
from src.services.category_recommendation import CategoryRecommendationService
from src.services.dashboard import DashboardMetricsService
from src.services.reconciliation import ReconciliationService
from src.services.transaction import TransactionService
from src.utils.format import parse_cents, SQLITE_MIN_INT, SQLITE_MAX_INT


class CorrectnessTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")
        self.db.run_migrations(str(Path(__file__).resolve().parents[2] / "src/migrations"))
        seed_if_empty(self.db)
        self.repo = TransactionRepository(self.db)
        self.txns = TransactionService(self.repo)
        self.accounts = AccountService(AccountRepository(self.db), self.repo)
        self.cats = CategoryService(CategoryRepository(self.db), self.repo)
        self.reconcile = ReconciliationService(self.accounts.repo, self.repo, self.txns)
        app, rt = fast_app(secret_key="test", htmx=False)
        transactions.register(rt, self.txns, self.accounts, self.cats, CategoryRecommendationService())
        accounts.register(rt, self.accounts)
        reconciliation.register(rt, self.reconcile)
        self.client = TestClient(app, raise_server_exceptions=False)

    def tearDown(self):
        self.client.close()
        self.db.conn.close()

    def test_invalid_transaction_edits_are_atomic(self):
        original = self.repo.list_all()[0]
        for invalid in ({"label": "   "}, {"amount": "0"}, {"amount": ""}, {"account_id": "999"}, {"category_id": "999"}, {"amount": "Infinity"}):
            with self.subTest(invalid=invalid):
                response = self.client.put(f"/transactions/{original.id}", data={"date": "2026-09-15", **invalid})
                self.assertEqual(response.status_code, 400)
                self.assertEqual(self.repo.get_by_id(original.id), original)

    def test_valid_partial_edit_preserves_omitted_fields(self):
        original = self.repo.list_all()[0]
        self.assertEqual(self.client.put(f"/transactions/{original.id}", data={"label": " Renamed "}).status_code, 200)
        updated = self.repo.get_by_id(original.id)
        self.assertEqual(updated.label, "Renamed")
        for field in ("date", "amount", "account_id", "category_id", "uid"):
            self.assertEqual(getattr(original, field), getattr(updated, field))

    def test_populated_accounts_cannot_be_deleted_even_when_archived(self):
        for archived in (False, True):
            if archived:
                self.accounts.toggle_archived(3)
            response = self.client.delete("/accounts/3")
            self.assertEqual(response.status_code, 409)
            self.assertIn("Archive it or move its transactions", response.text)
            self.assertEqual(len(self.repo.list_all()), 3)
            self.assertEqual(self.accounts.get_by_id(3).label, "Daily Expenses")

    def test_empty_account_can_be_deleted(self):
        self.assertEqual(self.client.delete("/accounts/1").status_code, 200)
        with self.assertRaises(ValueError):
            self.accounts.get_by_id(1)

    def test_decimal_money_rounding_and_bounds(self):
        for raw, expected in (("1.005", 101), ("-1.005", -101), ("$1,234.56", 123456),
                              ("92233720368547758.07", SQLITE_MAX_INT), ("-92233720368547758.08", SQLITE_MIN_INT)):
            self.assertEqual(parse_cents(raw), expected)
        for raw in ("NaN", "Infinity", "-Infinity", "1e999", "garbage", "92233720368547758.08", "-92233720368547758.09"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_cents(raw)

    def test_invalid_money_returns_400_without_creating_transactions(self):
        for raw in ("NaN", "Infinity", "1e309", "1e999", "92233720368547758.08"):
            with self.subTest(raw=raw):
                response = self.client.post("/transactions", data={"date": "2026-10-01", "label": "Test", "amount": raw, "account_id": "3"})
                self.assertEqual(response.status_code, 400)
                response = self.client.post("/accounts/reconcile", data={"latest_balance_1": raw})
                self.assertEqual(response.status_code, 400)
                self.assertEqual(len(self.repo.list_all()), 3)

    def test_reconciliation_overflow_does_not_save_other_adjustments(self):
        self.txns.create("2026-10-01", "2026_10_01", SQLITE_MIN_INT, "Opening", 2, "Savings", None, "")
        before = self.repo.list_all()
        response = self.client.post("/accounts/reconcile", data={"latest_balance_1": "10", "latest_balance_2": "0"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.repo.list_all(), before)

    def test_reconciliation_uses_configured_local_date(self):
        class FixedDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime(2026, 11, 1, 1, 30, tzinfo=timezone.utc).astimezone(tz)
        with patch.dict("os.environ", {"CASHCOMPASS_TIMEZONE": "America/Los_Angeles"}), patch("src.utils.dates.datetime", FixedDatetime):
            response = self.client.post("/accounts/reconcile", data={"latest_balance_1": "10"}, follow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self.repo.list_all()[-1].date, "2026_10_31")

    def test_reconciliation_rolls_back_on_batch_storage_failure(self):
        before = self.repo.list_all()
        insert = self.repo._insert
        calls = 0

        def fail_second(*record):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("simulated storage failure")
            return insert(*record)

        with patch.object(self.repo, "_insert", side_effect=fail_second), self.assertRaises(RuntimeError):
            self.reconcile.create_adjustments({1: 1000, 2: 2000}, "2026-10-01")
        self.assertEqual(self.repo.list_all(), before)

    def test_dashboard_excludes_archived_only_expense_accounts(self):
        self.accounts.toggle_archived(3)
        dashboard = DashboardMetricsService(self.txns)
        for params in ({}, {"expense_account_filter": "1"}):
            data = dashboard.build(params, self.accounts.list(), self.cats.list())
            self.assertEqual(data["selected_expenses"], "$0.00")
            self.assertEqual(data["this_month_expenses"], "$0.00")

    def test_refund_totals_and_projections_keep_their_sign(self):
        for txn in self.repo.list_all():
            self.txns.delete(txn.id)
        self.txns.create("2026-10-01", "2026_10_01", 1000, "Refund", 3, "Daily Expenses", 1, "Groceries")
        data = DashboardMetricsService(self.txns).build({}, self.accounts.list(), self.cats.list())
        self.assertEqual(data["selected_expenses"], "-$10.00")
        self.assertEqual(data["avg_monthly_expenses"], "-$10.00")
        self.assertEqual(data["selected_expenses_projection"], "-$120.00/year")
        self.assertEqual(data["cat_month_rows"][0]["total"], "-$10.00")
        self.assertEqual(data["expense_bars"][0]["amt_fmt"], "-$10.00")
        self.assertEqual(data["expense_bars"][0]["trailing_avg_fmt"], "-$10.00")
