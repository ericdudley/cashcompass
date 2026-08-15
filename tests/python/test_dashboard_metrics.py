from __future__ import annotations

import unittest
from datetime import date, datetime, timezone

from fasthtml.common import to_xml

from src.components.dashboard import dashboard_page
from src.models import Account, AccountMonthBalance, Category, Transaction, TransactionFilter
from src.services.dashboard import (
    DashboardFilters,
    DashboardMetricsService,
    build_dashboard_view_model,
    _local_today,
    _compact_currency,
    _preset_dates,
    parse_dashboard_filters,
)


class FakeTransactionService:
    def __init__(self, txns: list[Transaction], balances: list[AccountMonthBalance]):
        self.txns = txns
        self.balances = balances
        self.filters = []
        self.last_balance_account_ids = None

    def list(self, f: TransactionFilter) -> list[Transaction]:
        self.filters.append(f)
        result = []
        for txn in self.txns:
            if f.date_from and txn.date < f.date_from:
                continue
            if f.date_to and txn.date > f.date_to:
                continue
            if f.account_ids and txn.account_id not in f.account_ids:
                continue
            if f.category_ids and txn.category_id not in f.category_ids:
                continue
            result.append(txn)
        return result

    def balances_by_month(self, account_ids: list[int]) -> list[AccountMonthBalance]:
        self.last_balance_account_ids = account_ids
        return [row for row in self.balances if row.account_id in account_ids]


def account(id: int, label: str, account_type: str, archived: bool = False) -> Account:
    return Account(id=id, label=label, account_type=account_type, is_archived=archived)


def txn(id: int, date: str, amount: int, account_id: int, account_label: str, category_id: int | None, category_label: str) -> Transaction:
    return Transaction(
        id=id,
        date=date,
        amount=amount,
        account_id=account_id,
        account_label=account_label,
        category_id=category_id,
        category_label=category_label,
    )


class DashboardMetricsTests(unittest.TestCase):
    def setUp(self):
        self.accounts = [
            account(1, "Everyday", "expenses"),
            account(2, "Travel", "expenses"),
            account(3, "Brokerage", "net_worth"),
            account(4, "Savings", "net_worth"),
            account(5, "Closed 401k", "net_worth", archived=True),
        ]
        self.categories = [
            Category(id=10, label="Food"),
            Category(id=11, label="Utilities"),
        ]

    def test_expense_metrics_respect_date_account_and_category_filters(self):
        txns = [
            txn(1, "2026_01_05", -1000, 1, "Everyday", 10, "Food"),
            txn(2, "2026_01_08", -500, 2, "Travel", 11, "Utilities"),
            txn(3, "2026_02_10", -2000, 1, "Everyday", 10, "Food"),
            txn(4, "2026_03_01", -300, 1, "Everyday", 10, "Food"),
        ]
        service = DashboardMetricsService(FakeTransactionService(txns, []), today_fn=lambda: date(2026, 3, 15))

        data = service.build(
            {
                "date_preset": "custom",
                "date_from": "2026-01-01",
                "date_to": "2026-02-28",
                "expense_account_id": ["1"],
                "category_id": ["10"],
            },
            self.accounts,
            self.categories,
        )

        self.assertEqual(data["selected_expenses"], "$30.00")
        self.assertEqual(data["this_month_expenses"], "$3.00")
        self.assertEqual(data["this_month_expenses_projection"], "$36.00/year")
        self.assertEqual(data["selected_expenses_projection"], "$180.00/year")
        self.assertEqual(data["avg_monthly_expenses_projection"], "$180.00/year")
        self.assertEqual([bar["month"] for bar in data["expense_bars"]], ["Jan '26", "Feb '26"])
        self.assertEqual([bar["amt_fmt"] for bar in data["expense_bars"]], ["$10.00", "$20.00"])
        self.assertEqual([bar["trailing_avg_fmt"] for bar in data["expense_bars"]], ["$10.00", "$15.00"])
        self.assertEqual(data["expense_trailing_avg_points"], "0.0,50.0 100.0,25.0")
        self.assertEqual(data["cat_month_rows"], [{
            "category": "Food",
            "totals": ["$10.00", "$20.00"],
            "total": "$30.00",
        }])

    def test_expense_chart_uses_12_month_trailing_average(self):
        txns = [
            txn(month, f"2026_{month:02d}_01", -(month * 100), 1, "Everyday", 10, "Food")
            for month in range(1, 13)
        ]
        txns.append(txn(13, "2027_01_01", -1300, 1, "Everyday", 10, "Food"))
        service = DashboardMetricsService(FakeTransactionService(txns, []), today_fn=lambda: date(2027, 1, 15))

        data = service.build({}, self.accounts, self.categories)

        self.assertEqual(data["expense_bars"][0]["trailing_avg_fmt"], "$1.00")
        self.assertEqual(data["expense_bars"][11]["trailing_avg_fmt"], "$6.50")
        self.assertEqual(data["expense_bars"][12]["trailing_avg_fmt"], "$7.50")
        self.assertEqual(data["expense_year_markers"], [{
            "year": "2027",
            "left_style": "left:92.3%",
            "value": "$78.00/yr",
            "value_label": "annualized spending",
        }])

    def test_expense_chart_stacks_monthly_totals_by_category(self):
        txns = [
            txn(1, "2026_01_05", -1000, 1, "Everyday", 10, "Food"),
            txn(2, "2026_01_10", -500, 1, "Everyday", 11, "Utilities"),
            txn(3, "2026_02_05", -2000, 1, "Everyday", 10, "Food"),
        ]
        service = DashboardMetricsService(FakeTransactionService(txns, []), today_fn=lambda: date(2026, 2, 15))

        data = service.build({}, self.accounts, self.categories)

        self.assertEqual(data["expense_chart_legend"], [
            {"label": "Food", "color": "#34d399"},
            {"label": "Utilities", "color": "#60a5fa"},
        ])
        self.assertEqual(data["expense_bars"][0]["segments"], [
            {"label": "Food", "value_fmt": "$10.00", "height_style": "height:50.0%", "color": "#34d399"},
            {"label": "Utilities", "value_fmt": "$5.00", "height_style": "height:25.0%", "color": "#60a5fa"},
        ])
        self.assertEqual(data["expense_bars"][1]["segments"], [
            {"label": "Food", "value_fmt": "$20.00", "height_style": "height:100.0%", "color": "#34d399"},
        ])
        self.assertEqual(data["expense_bars"][0]["total_compact"], "$15")
        self.assertEqual(data["expense_bars"][0]["total_position_style"], "bottom:75.0%")

    def test_compact_currency_keeps_bar_labels_short(self):
        self.assertEqual(_compact_currency(12_300), "$123")
        self.assertEqual(_compact_currency(99_950), "$1.0k")
        self.assertEqual(_compact_currency(100_000), "$1.0k")
        self.assertEqual(_compact_currency(99_900_000), "$999k")
        self.assertEqual(_compact_currency(99_950_000), "$1.0m")
        self.assertEqual(_compact_currency(100_000_000), "$1.0m")

    def test_net_worth_total_sums_carried_forward_account_balances(self):
        filters = DashboardFilters(
            date_preset="custom",
            date_from="2026_01_01",
            date_to="2026_04_30",
            expense_account_ids=[1],
            net_worth_account_ids=[3, 4],
        )
        balances = [
            AccountMonthBalance(account_id=3, account_label="Brokerage", month="2026-01", balance=1000),
            AccountMonthBalance(account_id=3, account_label="Brokerage", month="2026-03", balance=1500),
            AccountMonthBalance(account_id=4, account_label="Savings", month="2026-02", balance=2000),
        ]

        data = build_dashboard_view_model(filters, self.accounts, self.categories, [], [], balances)

        self.assertEqual(data["nw_months"], ["Jan '26", "Feb '26", "Mar '26", "Apr '26"])
        self.assertEqual([bar["total_fmt"] for bar in data["nw_chart_bars"]], ["$10.00", "$30.00", "$35.00", "$35.00"])
        self.assertEqual(data["nw_chart_bars"][1]["segments"][0]["value_fmt"], "$10.00")
        self.assertEqual(data["nw_chart_bars"][1]["segments"][1]["value_fmt"], "$20.00")
        self.assertEqual(data["nw_chart_bars"][0]["total_position_style"], "bottom:28.6%")
        self.assertEqual(data["nw_chart_bars"][3]["total_position_style"], "bottom:100.0%")
        self.assertEqual(data["nw_trailing_avg_values"], ["$10.00", "$20.00", "$25.00", "$27.50"])
        self.assertEqual(data["current_net_worth"], "$35.00")

    def test_long_chart_ranges_get_readable_min_widths(self):
        txns = [
            txn(month, f"2025_{month:02d}_01", -1000, 1, "Everyday", 10, "Food")
            for month in range(1, 13)
        ] + [
            txn(month + 12, f"2026_{month:02d}_01", -1000, 1, "Everyday", 10, "Food")
            for month in range(1, 13)
        ]
        filters = DashboardFilters(
            date_preset="custom",
            date_from="2025_01_01",
            date_to="2026_12_31",
            expense_account_ids=[1],
            net_worth_account_ids=[3],
        )
        balances = [
            AccountMonthBalance(account_id=3, account_label="Brokerage", month=f"2025-{month:02d}", balance=1000)
            for month in range(1, 13)
        ] + [
            AccountMonthBalance(account_id=3, account_label="Brokerage", month=f"2026-{month:02d}", balance=1000)
            for month in range(1, 13)
        ]

        data = build_dashboard_view_model(filters, self.accounts, self.categories, txns, txns, balances)

        self.assertEqual(data["expense_chart_width_style"], "min-width:1056px")
        self.assertEqual(data["nw_chart_width_style"], "min-width:1056px")

    def test_net_worth_view_controls_stacked_bar_segments(self):
        filters = DashboardFilters(
            date_preset="custom",
            date_from="2026_01_01",
            date_to="2026_02_28",
            expense_account_ids=[1],
            net_worth_account_ids=[3],
            net_worth_view="accounts_only",
        )
        balances = [
            AccountMonthBalance(account_id=3, account_label="Brokerage", month="2026-01", balance=1000),
            AccountMonthBalance(account_id=3, account_label="Brokerage", month="2026-02", balance=1500),
        ]

        data = build_dashboard_view_model(filters, self.accounts, self.categories, [], [], balances)

        self.assertEqual(data["nw_chart_legend"], [{"label": "Brokerage", "color": "#34d399"}])
        self.assertEqual(data["nw_chart_bars"][0]["segments"][0]["label"], "Brokerage")

    def test_total_only_net_worth_view_uses_total_bars(self):
        filters = DashboardFilters(
            date_preset="custom",
            date_from="2026_01_01",
            date_to="2026_02_28",
            expense_account_ids=[1],
            net_worth_account_ids=[3],
            net_worth_view="total_only",
        )
        balances = [
            AccountMonthBalance(account_id=3, account_label="Brokerage", month="2026-01", balance=1000),
            AccountMonthBalance(account_id=3, account_label="Brokerage", month="2026-02", balance=1500),
        ]

        data = build_dashboard_view_model(filters, self.accounts, self.categories, [], [], balances)

        self.assertEqual(data["nw_chart_legend"], [{"label": "Total Net Worth", "color": "#f8fafc"}])
        self.assertEqual(data["nw_chart_bars"][1]["segments"][0]["label"], "Total Net Worth")
        self.assertEqual(data["nw_chart_bars"][1]["segments"][0]["value_fmt"], "$15.00")

    def test_invalid_filter_params_fall_back_to_defaults(self):
        filters = parse_dashboard_filters(
            {
                "date_preset": "tomorrowish",
                "expense_account_id": ["999"],
                "net_worth_account_id": ["5", "n/a"],
                "category_id": ["999"],
                "net_worth_view": "stacked",
            },
            self.accounts,
            self.categories,
        )

        self.assertEqual(filters.date_preset, "all_time")
        self.assertEqual(filters.expense_account_ids, [1, 2])
        self.assertEqual(filters.net_worth_account_ids, [3, 4])
        self.assertEqual(filters.category_ids, [])
        self.assertEqual(filters.net_worth_view, "total_accounts")

    def test_initial_load_defaults_account_filters_to_all_active_accounts(self):
        filters = parse_dashboard_filters({}, self.accounts, self.categories)

        self.assertEqual(filters.expense_account_ids, [1, 2])
        self.assertEqual(filters.net_worth_account_ids, [3, 4])
        self.assertFalse(filters.expense_accounts_submitted)
        self.assertFalse(filters.net_worth_accounts_submitted)

    def test_submitted_empty_account_filters_mean_no_accounts(self):
        filters = parse_dashboard_filters(
            {
                "expense_account_filter": "1",
                "net_worth_account_filter": "1",
            },
            self.accounts,
            self.categories,
        )

        self.assertEqual(filters.expense_account_ids, [])
        self.assertEqual(filters.net_worth_account_ids, [])
        self.assertTrue(filters.expense_accounts_submitted)
        self.assertTrue(filters.net_worth_accounts_submitted)

    def test_empty_category_selection_still_means_all_categories(self):
        txns = [
            txn(1, "2026_01_05", -1000, 1, "Everyday", 10, "Food"),
            txn(2, "2026_01_08", -500, 1, "Everyday", 11, "Utilities"),
        ]
        service = DashboardMetricsService(FakeTransactionService(txns, []), today_fn=lambda: date(2026, 1, 20))

        data = service.build(
            {
                "expense_account_filter": "1",
                "expense_account_id": ["1"],
            },
            self.accounts,
            self.categories,
        )

        self.assertEqual(data["this_month_expenses"], "$15.00")
        self.assertEqual(data["selected_expenses"], "$15.00")

    def test_submitted_empty_account_filters_do_not_query_all_accounts(self):
        txns = [txn(1, "2026_01_05", -1000, 1, "Everyday", 10, "Food")]
        balances = [AccountMonthBalance(account_id=3, account_label="Brokerage", month="2026-01", balance=1000)]
        fake = FakeTransactionService(txns, balances)
        service = DashboardMetricsService(fake)

        data = service.build(
            {
                "expense_account_filter": "1",
                "net_worth_account_filter": "1",
            },
            self.accounts,
            self.categories,
        )

        self.assertEqual(data["this_month_expenses"], "$0.00")
        self.assertEqual(data["selected_expenses"], "$0.00")
        self.assertEqual(data["current_net_worth"], "$0.00")
        self.assertEqual(fake.filters, [])
        self.assertIsNone(fake.last_balance_account_ids)

    def test_custom_date_inputs_are_normalized(self):
        filters = parse_dashboard_filters(
            {
                "date_preset": "custom",
                "date_from": "2026-02-01",
                "date_to": "2026-01-01",
            },
            self.accounts,
            self.categories,
        )

        self.assertEqual(filters.date_from, "2026_01_01")
        self.assertEqual(filters.date_to, "2026_02_01")
        self.assertEqual(filters.date_from_display, "2026-01-01")
        self.assertEqual(filters.date_to_display, "2026-02-01")

    def test_this_month_remains_current_month_for_this_year_filter(self):
        txns = [
            txn(1, "2026_01_05", -1000, 1, "Everyday", 10, "Food"),
            txn(2, "2026_08_05", -2500, 1, "Everyday", 10, "Food"),
            txn(3, "2026_09_05", -5000, 1, "Everyday", 10, "Food"),
        ]
        service = DashboardMetricsService(FakeTransactionService(txns, []), today_fn=lambda: date(2026, 8, 10))

        data = service.build({"date_preset": "this_year"}, self.accounts, self.categories)

        self.assertEqual(data["this_month_expenses"], "$25.00")
        self.assertEqual(data["selected_expenses"], "$85.00")

    def test_this_month_remains_current_month_for_custom_filter(self):
        txns = [
            txn(1, "2026_01_05", -1000, 1, "Everyday", 10, "Food"),
            txn(2, "2026_08_05", -2500, 1, "Everyday", 10, "Food"),
        ]
        service = DashboardMetricsService(FakeTransactionService(txns, []), today_fn=lambda: date(2026, 8, 10))

        data = service.build(
            {
                "date_preset": "custom",
                "date_from": "2026-01-01",
                "date_to": "2026-01-31",
            },
            self.accounts,
            self.categories,
        )

        self.assertEqual(data["this_month_expenses"], "$25.00")
        self.assertEqual(data["selected_expenses"], "$10.00")

    def test_this_month_respects_selected_account_and_category_filters(self):
        txns = [
            txn(1, "2026_08_05", -1000, 1, "Everyday", 10, "Food"),
            txn(2, "2026_08_06", -2000, 2, "Travel", 10, "Food"),
            txn(3, "2026_08_07", -3000, 1, "Everyday", 11, "Utilities"),
        ]
        service = DashboardMetricsService(FakeTransactionService(txns, []), today_fn=lambda: date(2026, 8, 10))

        data = service.build(
            {
                "expense_account_id": ["1"],
                "category_id": ["10"],
            },
            self.accounts,
            self.categories,
        )

        self.assertEqual(data["this_month_expenses"], "$10.00")

    def test_local_today_uses_configured_timezone_at_month_boundary(self):
        utc_month_start = lambda: datetime(2026, 9, 1, 6, 30, tzinfo=timezone.utc)

        self.assertEqual(_local_today(now_fn=utc_month_start, timezone_name="America/Los_Angeles"), date(2026, 8, 31))
        self.assertEqual(_local_today(now_fn=utc_month_start, timezone_name="UTC"), date(2026, 9, 1))
        self.assertEqual(_preset_dates("this_month", today=date(2026, 8, 31)), ("2026_08_01", "2026_08_31"))


class DashboardComponentTests(unittest.TestCase):
    def setUp(self):
        self.accounts = [
            account(1, "Everyday", "expenses"),
            account(3, "Brokerage", "net_worth"),
        ]
        self.categories = [Category(id=10, label="Food")]

    def _data(self, net_worth_view: str = "total_accounts"):
        filters = DashboardFilters(
            date_preset="custom",
            date_from="2026_01_01",
            date_to="2026_02_28",
            date_from_display="2026-01-01",
            date_to_display="2026-02-28",
            category_ids=[10],
            expense_account_ids=[1],
            net_worth_account_ids=[3],
            net_worth_view=net_worth_view,
            range_label="2026-01-01 to 2026-02-28",
        )
        balances = [
            AccountMonthBalance(account_id=3, account_label="Brokerage", month="2026-01", balance=1000),
            AccountMonthBalance(account_id=3, account_label="Brokerage", month="2026-02", balance=1500),
        ]
        return build_dashboard_view_model(filters, self.accounts, self.categories, [], [], balances)

    def _data_with_expenses(self):
        filters = DashboardFilters(expense_account_ids=[1], net_worth_account_ids=[3])
        expenses = [
            txn(1, "2026_12_05", -1000, 1, "Everyday", 10, "Food"),
            txn(2, "2027_01_05", -2000, 1, "Everyday", 10, "Food"),
        ]
        return build_dashboard_view_model(filters, self.accounts, self.categories, expenses, expenses, [])

    def _data_with_net_worth_year_boundary(self):
        filters = DashboardFilters(
            date_preset="custom",
            date_from="2026_12_01",
            date_to="2027_01_31",
            expense_account_ids=[1],
            net_worth_account_ids=[3],
        )
        balances = [
            AccountMonthBalance(account_id=3, account_label="Brokerage", month="2026-12", balance=1000),
            AccountMonthBalance(account_id=3, account_label="Brokerage", month="2027-01", balance=1500),
        ]
        return build_dashboard_view_model(filters, self.accounts, self.categories, [], [], balances)

    def test_filter_controls_render_selected_state(self):
        html = to_xml(dashboard_page(self._data()))

        self.assertIn('data-testid="dashboard-filter-trigger"', html)
        self.assertIn('data-testid="stat-this-month"', html)
        self.assertIn('data-testid="stat-selected-expenses"', html)
        self.assertIn('$0.00/year', html)
        self.assertIn('data-testid="dashboard-filters"', html)
        self.assertIn('value="custom" selected', html)
        self.assertIn('name="expense_account_filter" value="1"', html)
        self.assertIn('name="net_worth_account_filter" value="1"', html)
        self.assertIn('data-testid="dashboard-category-select"', html)
        self.assertIn('name="category_id" value="10" checked', html)
        self.assertIn('data-testid="dashboard-expense-account-select"', html)
        self.assertIn('name="expense_account_id" value="1" checked', html)
        self.assertIn('data-testid="dashboard-net-worth-account-select"', html)
        self.assertIn('name="net_worth_account_id" value="3" checked', html)

    def test_total_and_account_series_render_by_default(self):
        html = to_xml(dashboard_page(self._data()))

        self.assertIn('data-testid="net-worth-chart"', html)
        self.assertIn('data-nw-segment-label="Brokerage"', html)
        self.assertIn('data-nw-total="$15.00"', html)
        self.assertIn('data-testid="net-worth-month-tooltip"', html)
        self.assertNotIn('min-h-1', html)
        self.assertIn('data-testid="net-worth-trailing-average-line"', html)
        self.assertIn('data-testid="net-worth-chart-scroll"', html)
        self.assertIn('data-series-kind="net-worth-trailing-average"', html)
        self.assertIn('Brokerage', html)

    def test_expense_chart_renders_trailing_average_line(self):
        html = to_xml(dashboard_page(self._data_with_expenses()))

        self.assertIn('data-testid="expense-trailing-average-line"', html)
        self.assertIn('data-testid="expense-month-tooltip"', html)
        self.assertIn('data-stacked-bar-label="Food"', html)
        self.assertIn('data-testid="expense-trailing-average-points"', html)
        self.assertIn('data-testid="expense-chart-scroll"', html)
        self.assertIn('data-series-kind="expense-trailing-average"', html)
        self.assertIn("Jan '27: $15.00", html)
        self.assertIn('12-month avg', html)
        self.assertIn('data-testid="expense-year-markers"', html)
        self.assertIn('2027', html)
        self.assertIn('$120.00/yr', html)
        self.assertIn('data-year-marker-label="annualized spending"', html)

    def test_total_only_mode_hides_account_line(self):
        html = to_xml(dashboard_page(self._data(net_worth_view="total_only")))

        self.assertIn('data-nw-segment-label="Total Net Worth"', html)
        self.assertNotIn('data-nw-segment-label="Brokerage"', html)

    def test_accounts_only_mode_hides_total_line(self):
        html = to_xml(dashboard_page(self._data(net_worth_view="accounts_only")))

        self.assertNotIn('data-nw-segment-label="Total Net Worth"', html)
        self.assertIn('data-nw-segment-label="Brokerage"', html)

    def test_net_worth_chart_renders_year_markers(self):
        html = to_xml(dashboard_page(self._data_with_net_worth_year_boundary()))

        self.assertIn('data-testid="net-worth-year-markers"', html)
        self.assertIn('data-testid="net-worth-trailing-average-points"', html)
        self.assertIn('2027', html)
        self.assertIn("Jan '27", html)
        self.assertIn('$15.00', html)
        self.assertIn("Jan '27: $12.50", html)
        self.assertIn('$10.00', html)
        self.assertIn('data-year-marker-label="12-month avg"', html)


if __name__ == "__main__":
    unittest.main()
