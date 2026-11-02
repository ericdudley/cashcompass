from __future__ import annotations

import unittest
import sqlite3
from datetime import date
from pathlib import Path
from unittest.mock import patch

from fasthtml.common import to_xml
from starlette.datastructures import QueryParams

from src.components.budget import budget_page, category_breakdown_panel
from src.db import Database
from src.models import Category, Transaction, TransactionFilter, MonthlyRolloverChange
from src.repository.category import CategoryRepository
from src.repository.account import AccountRepository
from src.repository.annual_income import AnnualIncomeRepository
from src.repository.budget import BudgetRepository
from src.repository.transaction import TransactionRepository
from src.routes.transactions import _parse_filter
from src.services.budget import BudgetService, adjacent_month, category_breakdown, month_bounds, parse_budget_limit, budget_segments, budget_year
from src.services.backup import BackupService
from src.services.category import CategoryService
from src.services.transaction import TransactionService
from src.db import seed_if_empty
from src.utils.dates import preset_to_dates


class CategoryBreakdownTests(unittest.TestCase):
    def test_groups_by_identity_and_preserves_refund_only_and_uncategorized_rows(self):
        breakdown = category_breakdown([
            Transaction(category_id=1, category_label="Same name", amount=-1000),
            Transaction(category_id=1, category_label="Old name", amount=250),
            Transaction(category_id=2, category_label="Same name", amount=-2000),
            Transaction(category_id=3, category_label="Refund only", amount=500),
            Transaction(category_label="Stale label", amount=-300),
        ])
        rows = {row.category_id: row for row in breakdown.rows}
        self.assertEqual((breakdown.spending, breakdown.credits, breakdown.net_expenses, breakdown.count), (3300, 750, 2550, 5))
        self.assertEqual((rows[1].spending, rows[1].credits, rows[1].net_expenses, rows[1].count), (1000, 250, 750, 2))
        self.assertEqual(rows[2].net_expenses, 2000)
        self.assertEqual(rows[3].net_expenses, -500)
        self.assertEqual(rows[None].label, "Uncategorized")

    def test_current_category_names_and_zero_activity_are_preserved(self):
        breakdown = category_breakdown([
            Transaction(category_id=1, category_label="Old name", amount=-1000),
        ], [Category(id=1, label="New name"), Category(id=2, label="Unused")])
        rows = {row.category_id: row for row in breakdown.rows}
        self.assertEqual(rows[1].label, "New name")
        self.assertEqual((rows[2].count, rows[2].net_expenses), (0, 0))

    def test_credit_only_totals_are_displayed_with_a_negative_sign(self):
        breakdown = category_breakdown([Transaction(category_id=1, category_label="Refund", amount=1200)])
        html = to_xml(category_breakdown_panel(breakdown))
        self.assertIn('-$12.00', html)
        self.assertIn('0.0%', html)
        self.assertNotIn('nan', html.lower())


class BudgetServiceTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")
        self.db.run_migrations(str(Path(__file__).resolve().parents[2] / "src" / "migrations"))
        self.db.execute("INSERT INTO accounts (id, uid, label, account_type) VALUES (1, 'acct_expense', 'Expenses', 'expenses')")
        self.db.execute("INSERT INTO accounts (id, uid, label, account_type) VALUES (2, 'acct_assets', 'Assets', 'net_worth')")
        self.db.commit()
        self.repo = TransactionRepository(self.db)
        self.txns = TransactionService(self.repo)
        self.cats = CategoryService(CategoryRepository(self.db), self.repo)
        self.food = self.cats.create("Food")
        self.unused = self.cats.create("Unused")
        self.budgets = BudgetRepository(self.db)
        self.service = BudgetService(self.txns, self.cats, self.budgets, today_fn=lambda: date(2024, 2, 29))

    def tearDown(self):
        self.db.conn.close()

    def add(self, day: str, amount: int, *, account=1, category=None):
        return self.txns.create(day, day.replace("-", "_"), amount, "Test", account, "Expenses" if account == 1 else "Assets",
                                category.id if category else None, category.label if category else "")

    def test_month_includes_leap_day_and_excludes_other_months_and_net_worth(self):
        self.add("2024-01-31", -2000, category=self.food)
        self.add("2024-02-01", -1000, category=self.food)
        self.add("2024-02-29", -1500, category=self.food)
        self.add("2024-02-29", 500, category=self.food)
        self.add("2024-02-15", -300)
        self.add("2024-03-01", -9999, category=self.food)
        self.add("2024-02-10", -9999, account=2, category=self.food)
        data = self.service.build()
        self.assertEqual(data["month"], "2024-02")
        self.assertEqual(data["breakdown"].net_expenses, 2300)
        self.assertEqual(data["previous_breakdown"].net_expenses, 2000)
        self.assertEqual(data["breakdown"].count, 4)
        self.assertIn("date_to=2024-02-29", data["transactions_url"])

    def test_recategorization_rename_and_deletion_update_monthly_totals(self):
        txn = self.add("2024-02-01", -1000, category=self.food)
        self.cats.update_label(self.food.id, "Groceries")
        rows = {row.category_id: row for row in self.service.build()["breakdown"].rows}
        self.assertEqual(rows[self.food.id].label, "Groceries")
        self.txns.update_category(txn.id, self.unused.id, self.unused.label)
        rows = {row.category_id: row for row in self.service.build()["breakdown"].rows}
        self.assertEqual(rows[self.food.id].net_expenses, 0)
        self.assertEqual(rows[self.unused.id].net_expenses, 1000)
        self.cats.delete(self.unused.id)
        rows = {row.category_id: row for row in self.service.build()["breakdown"].rows}
        self.assertEqual(rows[None].net_expenses, 1000)
        self.txns.delete(txn.id)
        self.assertEqual(self.service.build()["breakdown"].count, 0)

    def test_uncategorized_filter_can_be_combined_with_multiple_categories(self):
        self.add("2024-02-01", -1000, category=self.food)
        self.add("2024-02-01", -2000, category=self.unused)
        self.add("2024-02-01", -300)
        uncategorized = self.txns.list(TransactionFilter(category_ids=[0], account_type="expenses"))
        self.assertEqual([txn.amount for txn in uncategorized], [-300])
        combined = self.txns.list(TransactionFilter(category_ids=[0, self.food.id], account_type="expenses"))
        self.assertEqual(sum(txn.amount for txn in combined), -1300)

    def test_prior_only_activity_remains_visible_in_month_comparison(self):
        self.add("2024-01-01", -1000)
        data = self.service.build()
        html = to_xml(budget_page(data))
        self.assertIn('Uncategorized', html)
        self.assertIn('-$10.00', html)
        self.assertIn('No expenses recorded this period', html)

    def test_month_navigation_and_validation(self):
        self.assertEqual(month_bounds("2024-02"), ("2024_02_01", "2024_02_29"))
        self.assertEqual(month_bounds("2025-02"), ("2025_02_01", "2025_02_28"))
        self.assertEqual(adjacent_month("2024-12", 1), "2025-01")
        self.assertEqual(adjacent_month("2024-01", -1), "2023-12")
        self.assertEqual(adjacent_month("0001-01", -1), "")
        self.assertEqual(adjacent_month("9999-12", 1), "")
        for value in ["2024-13", "bad", "2024-2", "0000-01"]:
            with self.assertRaises(ValueError):
                self.service.build(value)

    def test_changes_preserve_scheduled_limits_and_blank_stops_while_zero_is_active(self):
        self.service.save_limits("2024-02", {self.food.id: "50.25", 0: "0"})
        self.service.save_limits("2024-03", {self.food.id: "100"})
        self.add("2024-02-15", -6000, category=self.food)
        data = self.service.build("2024-02")
        self.assertEqual(data["limits"], {self.food.id: 5025, None: 0})
        self.assertEqual(data["total_limits"] - data["budgeted_expenses"], -975)
        html = to_xml(budget_page(data))
        self.assertIn("Over by $9.75", html)
        self.assertIn('$0.00 remaining', html)
        self.service.save_limits("2024-02", {self.food.id: ""})
        self.assertEqual(self.service.build("2024-02")["limits"], {None: 0})
        self.assertEqual(self.service.build("2024-03")["limits"], {self.food.id: 10000, None: 0})

    def test_invalid_limits_do_not_partially_save(self):
        self.service.save_limits("2024-02", {self.food.id: "10"})
        for raw in ["-1", "NaN", "Infinity", "bad", "1.001", "1e999999999", "92233720368547758.08", "1.00000000000000000000000000001"]:
            with self.assertRaises(ValueError, msg=raw):
                self.service.save_limits("2024-02", {self.food.id: "20", self.unused.id: raw})
            self.assertEqual(self.service.build("2024-02")["limits"], {self.food.id: 1000})
        with self.assertRaises(ValueError):
            self.service.save_limits("2024-02", {999: "10"})
        self.assertEqual(parse_budget_limit("0.29"), 29)
        self.assertEqual(parse_budget_limit("10.000"), 1000)

    def test_travel_accumulates_and_spending_consumes_rollover(self):
        self.budgets.save_changes(rollover=[MonthlyRolloverChange("2024-01", key, True) for key in [self.food.id]])
        self.service.today_fn = lambda: date(2026, 11, 1)
        self.service.save_limits("2024-01", {self.food.id: "200"})
        self.add("2024-03-15", -50000, category=self.food)
        budget = self.service.build("2024-03")["budgets"][self.food.id]
        self.assertEqual(budget["contribution"], 20000)
        self.assertEqual(budget["rollover"], 40000)
        self.assertEqual(budget["available"], 60000)
        self.assertEqual(budget["remaining"], 10000)
        self.assertEqual(budget["annual_limit"], 240000)
        self.assertEqual(budget["annual_expenses"], 50000)
        data = self.service.build("2024-04")
        self.assertEqual(data["total_available"], 30000)
        self.assertEqual(data["total_remaining"], 30000)

    def test_inherited_edits_skip_unchanged_values_and_preserve_future_changes(self):
        self.service.save_limits("2024-01", {self.food.id: "200", self.unused.id: "50"})
        self.service.save_limits("2024-07", {self.food.id: "300"})
        before = self.budgets.list()
        self.service.save_limits("2024-03", {self.food.id: "200.00", self.unused.id: "50.0", 0: ""})
        self.assertEqual(self.budgets.list(), before)
        self.service.save_limits("2024-03", {self.food.id: "250", self.unused.id: "50"})
        self.assertEqual([(row.category_id, row.amount_cents) for row in self.budgets.list("2024-03")],
                         [(self.food.id, 25000)])
        self.assertEqual(self.service.build("2024-02")["limits"][self.food.id], 20000)
        self.assertEqual(self.service.build("2024-06")["limits"][self.food.id], 25000)
        july = self.service.build("2024-07")["budgets"][self.food.id]
        self.assertEqual(july["contribution"], 30000)
        self.assertEqual(july["annual_limit"], 2 * 20000 + 4 * 25000 + 6 * 30000)
        self.assertEqual(self.service.build("2024-03")["budgets"][self.food.id]["next_change"].month, "2024-07")
        self.assertIn("Next contribution change: 2024-07", to_xml(budget_page(self.service.build("2024-03"))))

    def test_annual_budget_sums_months_and_spending_stops_at_selected_month(self):
        self.service.today_fn = lambda: date(2026, 11, 1)
        self.service.save_limits("2024-01", {self.food.id: "200"})
        self.service.save_limits("2024-07", {self.food.id: "300"})
        self.add("2024-01-01", -2000, category=self.food)
        self.add("2024-06-30", -5000, category=self.food)
        self.add("2024-07-01", -9999, category=self.food)
        self.add("2024-03-01", -9999, category=self.food, account=2)
        self.add("2024-03-01", 500, category=self.food)
        data = self.service.build("2024-06")
        self.assertEqual(data["annual_limit"], 300000)
        self.assertEqual(data["annual_expenses"], 6500)
        self.assertEqual(data["annual_period"], "January 1–2024-06-30")
        self.assertEqual(data["budgets"][self.food.id]["annual_remaining"], 293500)

    def test_midyear_start_excludes_opening_deficit_but_includes_earlier_annual_spending(self):
        self.service.today_fn = lambda: date(2026, 11, 1)
        self.add("2024-02-01", -10000, category=self.food)
        self.service.save_limits("2024-07", {self.food.id: "200"})
        july = self.service.build("2024-07")["budgets"][self.food.id]
        self.assertEqual((july["rollover"], july["available"], july["remaining"]), (0, 20000, 20000))
        self.assertEqual((july["annual_limit"], july["annual_expenses"]), (120000, 10000))
        self.assertNotIn(self.food.id, self.service.build("2024-06")["limits"])

    def test_deficits_refunds_and_historical_corrections_recalculate(self):
        self.budgets.save_changes(rollover=[MonthlyRolloverChange("2024-01", key, True) for key in [self.food.id, self.unused.id]])
        self.service.save_limits("2024-01", {self.food.id: "100", self.unused.id: "100"})
        txn = self.add("2024-01-01", -25000, category=self.food)
        self.add("2024-02-01", 2500, category=self.food)
        feb = self.service.build("2024-02")["budgets"][self.food.id]
        self.assertEqual((feb["rollover"], feb["available"], feb["remaining"]), (-15000, -5000, -2500))
        html = to_xml(budget_page(self.service.build("2024-02")))
        self.assertIn("Over by $25.00", html)
        self.assertNotIn("nan", html.lower())
        self.txns.update_amount(txn.id, -20000)
        self.assertEqual(self.service.build("2024-02")["budgets"][self.food.id]["remaining"], 2500)
        self.txns.update_category(txn.id, self.unused.id, self.unused.label)
        data = self.service.build("2024-02")["budgets"]
        self.assertEqual(data[self.food.id]["remaining"], 22500)
        self.assertEqual(data[self.unused.id]["remaining"], 0)
        self.txns.update_date(txn.id, "2024-03-01", "2024_03_01")
        self.assertEqual(self.service.build("2024-02")["budgets"][self.unused.id]["remaining"], 20000)
        self.txns.delete(txn.id)
        self.service.save_limits("2024-01", {self.food.id: "150"})
        self.assertEqual(self.service.build("2024-02")["budgets"][self.food.id]["remaining"], 32500)

    def test_zero_preserves_rollover_and_stop_resume_discards_it(self):
        self.budgets.save_changes(rollover=[MonthlyRolloverChange("2024-01", key, True) for key in [self.food.id, None]])
        self.service.save_limits("2024-01", {self.food.id: "100", 0: "10"})
        self.service.save_limits("2024-02", {self.food.id: "0", 0: "0"})
        feb = self.service.build("2024-02")["budgets"]
        self.assertEqual((feb[self.food.id]["available"], feb[None]["available"]), (10000, 1000))
        self.service.save_limits("2024-03", {self.food.id: "", 0: ""})
        self.add("2024-03-10", -90000, category=self.food)
        self.service.save_limits("2024-05", {self.food.id: "200", 0: "20"})
        self.assertEqual(self.service.build("2024-04")["limits"], {})
        may = self.service.build("2024-05")["budgets"]
        self.assertEqual((may[self.food.id]["rollover"], may[self.food.id]["available"]), (0, 20000))
        self.assertEqual((may[None]["rollover"], may[None]["available"]), (0, 2000))
        self.assertEqual(may[self.food.id]["annual_limit"], 10000 + 8 * 20000)
        self.assertIsNone(self.budgets.list("2024-03")[0].amount_cents)

    def test_january_resets_positive_and_negative_balances_and_retains_contributions(self):
        self.service.save_limits("2024-12", {self.food.id: "100", self.unused.id: "100"})
        self.add("2024-12-31", -25000, category=self.unused)
        january = self.service.build("2025-01")["budgets"]
        for category in [self.food, self.unused]:
            with self.subTest(category=category.label):
                budget = january[category.id]
                self.assertEqual((budget["contribution"], budget["rollover"], budget["remaining"]), (10000, 0, 10000))
                self.assertEqual((budget["annual_limit"], budget["annual_expenses"]), (120000, 0))

    def test_zero_and_unbudgeted_progress_are_safe(self):
        self.service.save_limits("2024-01", {self.food.id: "0"})
        self.add("2024-01-01", -100, category=self.food)
        data = self.service.build("2024-01")
        self.assertEqual(data["annual_limit"], 0)
        self.assertEqual(data["budgets"][self.food.id]["remaining"], -100)
        self.assertIsNone(data["budgets"][self.unused.id]["annual_limit"])
        html = to_xml(budget_page(data))
        self.assertIn("Over by $1.00", html)
        self.assertNotIn("nan", html.lower())

    def test_category_rename_preserves_limits_and_deletion_removes_them(self):
        self.service.save_limits("2024-02", {self.food.id: "10", 0: "5"})
        self.cats.update_label(self.food.id, "Renamed")
        self.assertEqual(self.service.build("2024-02")["limits"][self.food.id], 1000)
        self.cats.delete(self.food.id)
        self.assertEqual(self.service.build("2024-02")["limits"], {None: 500})

    def test_backup_round_trip_preserves_limits_and_imports_older_versions(self):
        backup = BackupService(self.db, AccountRepository(self.db), CategoryRepository(self.db), self.repo,
                               AnnualIncomeRepository(self.db), self.budgets)
        self.service.save_limits("2024-02", {self.food.id: "10.29", 0: "0"})
        self.service.save_limits("2024-03", {self.unused.id: "100"})
        self.service.save_limits("2024-04", {self.food.id: ""})
        payload = backup.export_backup()
        self.assertEqual(payload["version"], 5)
        self.service.save_limits("2024-02", {self.food.id: "100"})
        backup.restore_backup(payload)
        self.assertEqual(backup.export_backup()["monthly_budgets"], payload["monthly_budgets"])
        self.assertNotIn(self.food.id, self.service.build("2024-05")["limits"])
        legacy = {**payload, "version": 3,
                  "monthly_budgets": [row for row in payload["monthly_budgets"] if row["amount_cents"] is not None]}
        backup.restore_backup(legacy)
        self.assertEqual(self.service.build("2025-01")["limits"][self.food.id], 1029)
        for version in [1, 2]:
            legacy = {**payload, "version": version}
            del legacy["monthly_budgets"]
            backup.restore_backup(legacy)
            self.assertEqual(self.budgets.list(), [])

    def test_backup_rejects_invalid_budgets_before_replacing_data(self):
        backup = BackupService(self.db, AccountRepository(self.db), CategoryRepository(self.db), self.repo,
                               AnnualIncomeRepository(self.db), self.budgets)
        self.service.save_limits("2024-02", {self.food.id: "10"})
        payload = backup.export_backup()
        for invalid in [
            {"month": "2024-13", "category_id": None, "amount_cents": 100},
            {"month": "2024-02", "category_id": "missing", "amount_cents": 100},
            {"month": "2024-02", "category_id": None, "amount_cents": -100},
            {"month": "2024-02", "category_id": None, "amount_cents": True},
            {"month": "2024-02", "category_id": None, "amount_cents": 2**63},
            {"month": "2024-02", "category_id": None},
        ]:
            with self.assertRaises(ValueError):
                backup.restore_backup({**payload, "monthly_budgets": [invalid]})
            self.assertEqual(self.service.build("2024-02")["limits"], {self.food.id: 1000})
        with self.assertRaises(ValueError):
            backup.restore_backup({**payload, "monthly_budgets": payload["monthly_budgets"] * 2})
        with self.assertRaises(ValueError):
            backup.restore_backup({**payload, "version": 3, "monthly_budgets": [
                {"month": "2024-02", "category_id": None, "amount_cents": None},
            ]})
        self.assertEqual(self.budgets.list()[0].amount_cents, 1000)

    def test_new_monthly_budgets_reset_and_rollover_toggle_starts_fresh(self):
        self.service.today_fn = lambda: date(2025, 1, 1)
        self.service.save_limits("2024-01", {self.food.id: "100"})
        self.add("2024-01-10", -2000, category=self.food)
        self.assertEqual(self.service.build("2024-02")["budgets"][self.food.id]["available"], 10000)
        self.service.save_category(self.food.id, "2024-02", "monthly", "100", True)
        self.assertEqual(self.service.build("2024-02")["budgets"][self.food.id]["rollover"], 0)
        self.service.save_limits("2024-04", {self.food.id: "200"})
        self.assertEqual(self.service.build("2024-04")["budgets"][self.food.id]["available"], 40000)
        self.service.save_category(self.food.id, "2024-03", "monthly", "100", False)
        self.assertEqual(self.service.build("2024-04")["budgets"][self.food.id]["available"], 20000)
        self.assertTrue(self.service.build("2024-02")["budgets"][self.food.id]["rollover_enabled"])
        self.assertFalse(self.service.build("2024-04")["budgets"][self.food.id]["rollover_enabled"])

    def test_annual_plans_apply_to_selected_year_and_preserve_later_plans(self):
        self.service.today_fn = lambda: date(2027, 1, 1)
        self.service.save_limits("2023-01", {self.food.id: "100"})
        self.add("2024-01-10", -50000, category=self.food)
        self.service.save_category(self.food.id, "2024-07", "annual", "3000", False)
        self.assertEqual(self.service.build("2023-12")["budgets"][self.food.id]["period"], "monthly")
        january = self.service.build("2024-01")["budgets"][self.food.id]
        self.assertEqual((january["period"], january["annual_limit"], january["annual_remaining"]), ("annual", 300000, 250000))
        self.service.save_category(self.food.id, "2026-01", "annual", "4000", False)
        self.service.save_category(self.food.id, "2025-08", "annual", "3500", False)
        self.assertEqual(self.service.build("2025-01")["budgets"][self.food.id]["annual_limit"], 350000)
        self.assertEqual(self.service.build("2026-01")["budgets"][self.food.id]["annual_limit"], 400000)
        self.assertEqual(self.service.build("2027-01")["budgets"][self.food.id]["annual_limit"], 400000)
        self.assertEqual(self.budgets.list()[0].amount_cents, 10000)

    def test_type_conversion_requires_amount_and_monthly_conversion_starts_in_january(self):
        self.service.save_limits("2024-07", {self.food.id: "200"})
        with self.assertRaises(ValueError):
            self.service.save_category(self.food.id, "2024-05", "annual", "", False)
        self.assertEqual(self.budgets.list_plans(), [])
        self.service.save_category(self.food.id, "2024-05", "annual", "3000", False)
        with self.assertRaises(ValueError):
            self.service.save_category(self.food.id, "2024-05", "monthly", "", False)
        self.service.save_category(self.food.id, "2024-05", "monthly", "150", False)
        self.assertEqual(self.service.build("2024-01")["limits"][self.food.id], 15000)
        self.assertEqual(self.service.build("2024-07")["limits"][self.food.id], 20000)
        self.assertEqual(self.service.build("2023-12")["limits"], {})

    def test_annual_limit_edit_stop_zero_and_compatibility_endpoint(self):
        self.service.save_category(0, "2024-06", "annual", "1000", False)
        self.service.save_category(0, "2024-08", "annual", "1500", False)
        self.assertEqual(self.service.build("2024-01")["budgets"][None]["annual_limit"], 150000)
        before = (self.budgets.list(), self.budgets.list_plans(), self.budgets.list_rollover())
        self.service.save_category(0, "2024-08", "annual", "1500.00", False)
        self.assertEqual(before, (self.budgets.list(), self.budgets.list_plans(), self.budgets.list_rollover()))
        with self.assertRaises(ValueError):
            self.service.save_limits("2024-06", {self.food.id: "20", 0: "50"})
        self.assertEqual(self.budgets.list(), [])
        self.service.save_category(0, "2024-08", "annual", "", False)
        self.assertIsNone(self.service.build("2025-01")["budgets"][None]["annual_limit"])
        self.service.save_category(0, "2024-08", "annual", "0", False)
        self.assertEqual(self.service.build("2024-01")["budgets"][None]["annual_limit"], 0)

    def test_reporting_cutoffs_drilldowns_pace_and_future_plans(self):
        self.service.today_fn = lambda: date(2024, 2, 20)
        self.service.save_limits("2024-01", {self.food.id: "100"})
        self.service.save_category(self.unused.id, "2024-01", "annual", "3000", False)
        self.add("2024-02-20", -1000, category=self.food)
        self.add("2024-02-21", -2000, category=self.food)
        self.add("2024-03-01", -3000, category=self.food)
        self.add("2024-02-20", -5000, category=self.unused)
        data = self.service.build("2024-02")
        self.assertEqual(data["breakdown"].net_expenses, 6000)
        self.assertEqual(data["report_end"], "2024-02-20")
        self.assertIn("date_to=2024-02-20", data["transactions_url"])
        self.assertAlmostEqual(data["budgets"][self.unused.id]["pace"], 51 / 366)
        future = self.service.build("2024-03")
        self.assertIsNone(future["report_end"])
        self.assertEqual(future["breakdown"].net_expenses, 0)
        self.assertEqual(future["budgets"][self.unused.id]["annual_expenses"], 5000)
        annual = self.service.build(view="annual", requested_year="2024")
        self.assertEqual(annual["report_start"], "2024-01-01")
        self.assertEqual(annual["report_end"], "2024-02-20")
        planned = self.service.build(view="annual", requested_year="2025")
        self.assertIsNone(planned["report_end"])
        self.assertEqual(planned["annual_expenses"], 0)
        self.assertIsNone(planned["budgets"][self.unused.id]["pace"])
        self.service.today_fn = lambda: date(2025, 1, 1)
        self.assertEqual(self.service.build(view="annual", requested_year="2024")["budgets"][self.unused.id]["pace"], 1)

    def test_leap_day_pace_and_year_validation(self):
        self.service.save_category(self.food.id, "2024-01", "annual", "100", False)
        data = self.service.build(view="annual", requested_year="2024")
        self.assertAlmostEqual(data["budgets"][self.food.id]["pace"], 60 / 366)
        for raw in ["bad", "2024-02", "0000", "10000", True, 2.5]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                budget_year(raw)
        for raw in ["bad", "week"]:
            with self.assertRaises(ValueError):
                self.service.build(view=raw)

    def test_segment_allocation_and_accessible_edge_states(self):
        for spent, amounts in [(30000, [30000, 20000, 20000]), (60000, [60000, 10000]), (80000, [70000])]:
            bar = budget_segments(50000, 20000, spent)
            self.assertEqual([p["amount"] for p in bar["segments"]], amounts)
            self.assertAlmostEqual(sum(p["percent"] for p in bar["segments"]), 100)
            self.assertAlmostEqual(bar["boundary"], 50000 / 70000 * 100)
        self.assertEqual([p["amount"] for p in budget_segments(50000, -10000, 30000)["segments"]], [30000, 10000])
        for contribution, rollover, spent in [(0, 0, 100), (100, -200, 50), (100, 0, -50)]:
            bar = budget_segments(contribution, rollover, spent)
            self.assertTrue(all(0 < p["percent"] <= 100 for p in bar["segments"]))
        self.service.save_limits("2024-01", {self.food.id: "0"})
        self.add("2024-01-10", -100, category=self.food)
        html = to_xml(budget_page(self.service.build("2024-01")))
        self.assertIn("Over by $1.00", html)
        self.assertIn('role="img"', html)
        self.assertNotIn("nan", html.lower())

    def test_v5_backup_preserves_plans_rollover_and_validates_before_replacement(self):
        backup = BackupService(self.db, AccountRepository(self.db), CategoryRepository(self.db), self.repo,
                               AnnualIncomeRepository(self.db), self.budgets)
        self.service.save_category(self.food.id, "2024-01", "monthly", "100", True)
        self.service.save_category(self.food.id, "2024-03", "monthly", "100", False)
        self.service.save_category(0, "2024-06", "annual", "2000", False)
        payload = backup.export_backup()
        backup.restore_backup(payload)
        for field in ["budget_plans", "monthly_budget_rollover", "monthly_budgets"]:
            self.assertEqual(backup.export_backup()[field], payload[field])
        for field, records in [
            ("budget_plans", [{"year": True, "category_id": None, "period": "annual", "annual_amount_cents": 100}]),
            ("budget_plans", [{"year": 2024, "category_id": None, "period": "monthly", "annual_amount_cents": 100}]),
            ("budget_plans", [{"year": 2024, "category_id": "missing", "period": "annual", "annual_amount_cents": 100}]),
            ("budget_plans", payload["budget_plans"] * 2),
            ("monthly_budget_rollover", [{"month": "2024-13", "category_id": None, "enabled": True}]),
            ("monthly_budget_rollover", [{"month": "2024-01", "category_id": None, "enabled": 1}]),
            ("monthly_budget_rollover", payload["monthly_budget_rollover"] * 2),
        ]:
            with self.subTest(field=field, records=records), self.assertRaises(ValueError):
                backup.restore_backup({**payload, field: records})
            self.assertEqual(backup.export_backup()["budget_plans"], payload["budget_plans"])
        self.cats.delete(self.food.id)
        self.assertEqual(self.budgets.list_rollover(), [])
        self.service.clear_limits()
        self.assertEqual(self.budgets.list_plans(), [])

    def test_legacy_v4_import_seeds_monthly_rollover_without_changing_balance(self):
        backup = BackupService(self.db, AccountRepository(self.db), CategoryRepository(self.db), self.repo,
                               AnnualIncomeRepository(self.db), self.budgets)
        self.service.save_limits("2024-01", {self.food.id: "200", 0: "0"})
        self.add("2024-01-10", -5000, category=self.food)
        payload = {**backup.export_backup(), "version": 4}
        del payload["budget_plans"], payload["monthly_budget_rollover"]
        backup.restore_backup(payload)
        feb = self.service.build("2024-02")["budgets"][self.food.id]
        self.assertEqual((feb["period"], feb["rollover_enabled"], feb["available"]), ("monthly", True, 35000))

    def test_transaction_filters_preserve_multiple_categories_and_clear_stale_dates_for_presets(self):
        filters, preset = _parse_filter(QueryParams("date_preset=custom&date_from=2024-02-01&category_id=1&category_id=2&category_id=0"))
        self.assertEqual(filters.category_ids, [1, 2, 0])
        self.assertEqual(filters.date_from, "2024-02-01")
        self.assertEqual(preset, "custom")
        filters, preset = _parse_filter(QueryParams("date_preset=all_time&date_from=2024-02-01"))
        self.assertEqual(filters.date_from, "")

    def test_month_presets_and_seed_data_use_local_calendar_month(self):
        with patch("src.utils.dates.local_today", return_value=date(2026, 10, 31)):
            self.assertEqual(preset_to_dates("this_month"), ("2026_10_01", "2026_10_31"))
            self.assertEqual(preset_to_dates("last_month"), ("2026_09_01", "2026_09_30"))
        self.db.execute("DELETE FROM categories")
        self.db.execute("DELETE FROM accounts")
        self.db.commit()
        with patch("src.db.local_today", return_value=date(2026, 10, 31)):
            seed_if_empty(self.db)
        dates = [txn.date for txn in self.repo.list_all()]
        self.assertTrue(all(day.startswith("2026_10_") for day in dates))


class RecurringBudgetMigrationTests(unittest.TestCase):
    def test_migration_preserves_existing_rows_and_constraints(self):
        db = Database(":memory:")
        self.addCleanup(db.conn.close)
        migrations = Path(__file__).resolve().parents[2] / "src" / "migrations"
        for migration in sorted(migrations.glob("*.sql")):
            if migration.name.startswith("0005"):
                break
            db.conn.executescript(migration.read_text())
        db.execute("INSERT INTO categories (id, uid, label) VALUES (1, 'travel', 'Travel')")
        db.execute("INSERT INTO monthly_budgets VALUES ('2024-01', 1, 20000)")
        db.execute("INSERT INTO monthly_budgets VALUES ('2024-01', NULL, 0)")
        db.commit()
        db.conn.executescript((migrations / "0005-recurring-budgets.sql").read_text())
        repo = BudgetRepository(db)
        self.assertEqual([(row.category_id, row.amount_cents) for row in repo.list()], [(None, 0), (1, 20000)])
        repo.save_limits("2024-03", {1: None, None: None})
        for category in [1, None]:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("INSERT INTO monthly_budgets VALUES ('2024-03', ?, 1)", [category])
            db.conn.rollback()
        with self.assertRaises(sqlite3.IntegrityError):
            db.execute("INSERT INTO monthly_budgets VALUES ('2024-04', 1, -1)")
        db.conn.rollback()
        db.conn.executescript((migrations / "0006-budget-plans.sql").read_text())
        self.assertEqual([(p.year, p.period) for p in repo.list_plans()], [(2024, "monthly"), (2024, "monthly")])
        self.assertTrue(all(change.enabled and change.month == "2024-01" for change in repo.list_rollover()))
        txns = TransactionService(TransactionRepository(db))
        categories = CategoryService(CategoryRepository(db), TransactionRepository(db))
        service = BudgetService(txns, categories, repo, today_fn=lambda: date(2025, 1, 1))
        migrated = service.build("2024-02")["budgets"][1]
        self.assertEqual((migrated["contribution"], migrated["rollover"], migrated["available"]), (20000, 20000, 40000))
        db.execute("DELETE FROM categories WHERE id = 1")
        db.commit()
        self.assertTrue(all(row.category_id is None for row in repo.list()))
        self.assertTrue(all(row.category_id is None for row in repo.list_plans()))
        self.assertTrue(all(row.category_id is None for row in repo.list_rollover()))


if __name__ == "__main__":
    unittest.main()
