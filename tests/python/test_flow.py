from __future__ import annotations

import unittest

from src.models import AnnualIncome, Transaction, TransactionFilter
from src.services.flow import FlowService, build_flow_view_model


def transaction(amount: int, date: str = "2024_06_01", account_type: str = "net_worth") -> Transaction:
    return Transaction(
        date=date,
        amount=amount,
        account_id=1,
        account_label="Checking" if account_type == "net_worth" else "Daily Expenses",
        category_id=1 if account_type == "expenses" else None,
        category_label="Groceries" if account_type == "expenses" else "",
    )


def annual_income(
    gross: int = 10_000_000,
    federal_tax: int = 2_000_000,
    state_tax: int = 500_000,
) -> AnnualIncome:
    return AnnualIncome(
        tax_year=2024,
        gross_income_cents=gross,
        federal_tax_cents=federal_tax,
        state_tax_cents=state_tax,
    )


class FakeIncomeService:
    def __init__(self, income: AnnualIncome):
        self.income = income

    def list(self) -> list[AnnualIncome]:
        return [self.income]

    def get_by_year(self, year: int) -> AnnualIncome | None:
        return self.income if year == self.income.tax_year else None


class RecordingTransactionService:
    def __init__(self):
        self.filters: list[TransactionFilter] = []

    def list(self, filters: TransactionFilter) -> list[Transaction]:
        self.filters.append(filters)
        return []


class FlowViewModelTests(unittest.TestCase):
    def setUp(self):
        self.income = annual_income()
        self.expenses = [transaction(-150_000, account_type="expenses")]
        self.cash_flow_result = 7_350_000

    def test_net_worth_comparison_reports_match_more_and_less(self):
        cases = [
            (self.cash_flow_result, "matched", "matched the recorded left over"),
            (self.cash_flow_result + 10_000, "more", "$100.00 more than the recorded left over"),
            (self.cash_flow_result - 10_000, "less", "$100.00 less than the recorded left over"),
        ]

        for net_worth_change, expected_status, expected_message in cases:
            with self.subTest(status=expected_status):
                data = build_flow_view_model(
                    self.income,
                    self.expenses,
                    [transaction(net_worth_change)],
                )

                self.assertEqual(data["cash_flow_result"], self.cash_flow_result)
                self.assertEqual(data["net_worth_change"], net_worth_change)
                self.assertEqual(data["net_worth_comparison_status"], expected_status)
                self.assertIn(expected_message, data["net_worth_comparison_message"])

    def test_comparison_distinguishes_no_activity_from_zero_change(self):
        unavailable = build_flow_view_model(self.income, self.expenses, [])
        zero_change = build_flow_view_model(
            self.income,
            self.expenses,
            [transaction(1_000), transaction(-1_000)],
        )

        self.assertFalse(unavailable["has_net_worth_activity"])
        self.assertEqual(unavailable["net_worth_comparison_status"], "unavailable")
        self.assertEqual(
            unavailable["net_worth_comparison_message"],
            "No net-worth activity was recorded for this year.",
        )
        self.assertTrue(zero_change["has_net_worth_activity"])
        self.assertEqual(zero_change["net_worth_change"], 0)
        self.assertEqual(zero_change["net_worth_comparison_status"], "less")

    def test_shortfall_remains_signed_in_the_comparison(self):
        data = build_flow_view_model(
            annual_income(gross=100_000, federal_tax=0, state_tax=0),
            [transaction(-150_000, account_type="expenses")],
            [transaction(-40_000)],
        )

        self.assertEqual(data["cash_flow_result"], -50_000)
        self.assertEqual(data["cash_flow_label"], "Cash-flow Shortfall")
        self.assertEqual(data["shortfall"], 50_000)
        self.assertEqual(data["net_worth_difference"], 10_000)
        self.assertIn("$100.00 more than the cash-flow result", data["net_worth_comparison_message"])

    def test_sankey_nodes_have_explicit_destination_groups_and_order(self):
        data = build_flow_view_model(
            self.income,
            self.expenses,
            [transaction(self.cash_flow_result)],
        )
        nodes = {node["id"]: node for node in data["graph"]["nodes"]}

        self.assertEqual((nodes["federal-tax"]["group"], nodes["federal-tax"]["sort_order"]), ("taxes", 0))
        self.assertEqual((nodes["state-tax"]["group"], nodes["state-tax"]["sort_order"]), ("taxes", 1))
        self.assertEqual(nodes["category-0"]["group"], "expenses")
        self.assertGreater(nodes["category-0"]["sort_order"], nodes["state-tax"]["sort_order"])
        self.assertEqual(nodes["left-over"]["group"], "left-over")
        self.assertGreater(nodes["left-over"]["sort_order"], nodes["category-0"]["sort_order"])

    def test_flow_service_requests_expense_and_net_worth_activity_for_selected_year(self):
        txn_service = RecordingTransactionService()
        service = FlowService(FakeIncomeService(self.income), txn_service)

        service.build("2024")

        self.assertEqual(len(txn_service.filters), 3)
        history_filter, expense_filter, net_worth_filter = txn_service.filters
        self.assertEqual(history_filter.account_type, "expenses")
        self.assertEqual((history_filter.date_from, history_filter.date_to), ("", ""))
        self.assertEqual(
            (expense_filter.account_type, expense_filter.date_from, expense_filter.date_to),
            ("expenses", "2024_01_01", "2024_12_31"),
        )
        self.assertEqual(
            (net_worth_filter.account_type, net_worth_filter.date_from, net_worth_filter.date_to),
            ("net_worth", "2024_01_01", "2024_12_31"),
        )


if __name__ == "__main__":
    unittest.main()
