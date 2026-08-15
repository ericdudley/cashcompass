from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from src.models import Account, AccountMonthBalance, Category, Transaction, TransactionFilter
from src.services.transaction import TransactionService
from src.utils.format import cents_abs, cents_dollars


DATE_PRESETS = [
    ("all_time", "All time"),
    ("this_month", "This month"),
    ("last_month", "Last month"),
    ("last_3_months", "Last 3 months"),
    ("last_6_months", "Last 6 months"),
    ("this_year", "This year"),
    ("custom", "Custom"),
]

NET_WORTH_VIEWS = [
    ("total_accounts", "Total + accounts"),
    ("total_only", "Total only"),
    ("accounts_only", "Accounts only"),
]

NW_COLORS = [
    "#34d399",
    "#60a5fa",
    "#f472b6",
    "#fbbf24",
    "#a78bfa",
    "#fb923c",
]

EXPENSE_COLORS = [
    "#34d399",
    "#60a5fa",
    "#f472b6",
    "#fbbf24",
    "#a78bfa",
    "#fb923c",
]

TOTAL_NW_COLOR = "#f8fafc"


@dataclass
class DashboardFilters:
    date_preset: str = "all_time"
    date_from: str = ""
    date_to: str = ""
    date_from_display: str = ""
    date_to_display: str = ""
    category_ids: list[int] = field(default_factory=list)
    expense_account_ids: list[int] = field(default_factory=list)
    net_worth_account_ids: list[int] = field(default_factory=list)
    expense_accounts_submitted: bool = False
    net_worth_accounts_submitted: bool = False
    net_worth_view: str = "total_accounts"
    range_label: str = "All time"


class DashboardMetricsService:
    def __init__(self, txn_svc: TransactionService, today_fn: Callable[[], date] | None = None):
        self.txn_svc = txn_svc
        self.today_fn = today_fn

    def build(self, raw_params: Any, accounts: list[Account], categories: list[Category]) -> dict:
        today = self.today_fn() if self.today_fn else _local_today()
        filters = parse_dashboard_filters(raw_params, accounts, categories, today=today)

        if filters.expense_accounts_submitted and not filters.expense_account_ids:
            selected_expense_txns = []
            current_month_expense_txns = []
        else:
            selected_expense_txns = self.txn_svc.list(TransactionFilter(
                date_from=filters.date_from,
                date_to=filters.date_to,
                account_ids=filters.expense_account_ids,
                category_ids=filters.category_ids,
                account_type="expenses",
            ))
            current_month_from, current_month_to = _current_month_date_range(today)
            current_month_expense_txns = self.txn_svc.list(TransactionFilter(
                date_from=current_month_from,
                date_to=current_month_to,
                account_ids=filters.expense_account_ids,
                category_ids=filters.category_ids,
                account_type="expenses",
            ))

        if filters.net_worth_accounts_submitted and not filters.net_worth_account_ids:
            balances = []
        else:
            balances = self.txn_svc.balances_by_month(filters.net_worth_account_ids)
        return build_dashboard_view_model(filters, accounts, categories, selected_expense_txns, current_month_expense_txns, balances)


def parse_dashboard_filters(
    raw_params: Any,
    accounts: list[Account],
    categories: list[Category],
    today: date | None = None,
) -> DashboardFilters:
    preset = _first(raw_params, "date_preset") or "all_time"
    valid_presets = {value for value, _ in DATE_PRESETS}
    if preset not in valid_presets:
        preset = "all_time"

    date_from_display = _normalize_iso_date(_first(raw_params, "date_from"))
    date_to_display = _normalize_iso_date(_first(raw_params, "date_to"))
    if preset == "custom":
        date_from = date_from_display.replace("-", "_")
        date_to = date_to_display.replace("-", "_")
        if date_from and date_to and date_from > date_to:
            date_from, date_to = date_to, date_from
            date_from_display, date_to_display = date_to_display, date_from_display
    else:
        date_from, date_to = _preset_dates(preset, today=today)
        date_from_display = date_from.replace("_", "-")
        date_to_display = date_to.replace("_", "-")

    expense_accounts_submitted = _has(raw_params, "expense_account_filter")
    net_worth_accounts_submitted = _has(raw_params, "net_worth_account_filter")

    expense_account_ids = _valid_ids(
        _all(raw_params, "expense_account_id"),
        [a.id for a in accounts if a.account_type == "expenses" and not a.is_archived],
        default_all=not expense_accounts_submitted,
    )
    net_worth_account_ids = _valid_ids(
        _all(raw_params, "net_worth_account_id"),
        [a.id for a in accounts if a.account_type == "net_worth" and not a.is_archived],
        default_all=not net_worth_accounts_submitted,
    )
    category_ids = _valid_ids(_all(raw_params, "category_id"), [c.id for c in categories], default_all=False)

    net_worth_view = _first(raw_params, "net_worth_view") or "total_accounts"
    if net_worth_view not in {value for value, _ in NET_WORTH_VIEWS}:
        net_worth_view = "total_accounts"

    return DashboardFilters(
        date_preset=preset,
        date_from=date_from,
        date_to=date_to,
        date_from_display=date_from_display,
        date_to_display=date_to_display,
        category_ids=category_ids,
        expense_account_ids=expense_account_ids,
        net_worth_account_ids=net_worth_account_ids,
        expense_accounts_submitted=expense_accounts_submitted,
        net_worth_accounts_submitted=net_worth_accounts_submitted,
        net_worth_view=net_worth_view,
        range_label=_range_label(preset, date_from_display, date_to_display),
    )


def build_dashboard_view_model(
    filters: DashboardFilters,
    accounts: list[Account],
    categories: list[Category],
    selected_expense_txns: list[Transaction],
    current_month_expense_txns: list[Transaction],
    balances: list[AccountMonthBalance],
) -> dict:
    expense_month_totals = _monthly_expense_totals(selected_expense_txns)
    expense_months = sorted(expense_month_totals.keys())
    max_expense = max((max(expense_month_totals[m], 0) for m in expense_months), default=1) or 1
    trailing_averages = _trailing_monthly_averages(expense_month_totals, expense_months, window=12)

    expense_bars, expense_chart_legend = _expense_chart_bars(
        selected_expense_txns,
        expense_months,
        expense_month_totals,
        trailing_averages,
        max_expense,
    )

    visible_category_months = expense_months[-6:]
    category_rows = _category_month_rows(selected_expense_txns, visible_category_months)

    this_month_expenses = sum(-txn.amount for txn in current_month_expense_txns)
    selected_expenses = sum(-txn.amount for txn in selected_expense_txns)
    monthly_average = _monthly_average(expense_month_totals)

    active_net_worth_accounts = [a for a in accounts if a.account_type == "net_worth" and not a.is_archived]
    selected_net_worth_accounts = [a for a in active_net_worth_accounts if a.id in filters.net_worth_account_ids]
    nw_months, account_balance_rows, total_balances = _net_worth_balances(
        filters,
        selected_net_worth_accounts,
        balances,
    )

    nw_series = []
    include_total = filters.net_worth_view in ("total_accounts", "total_only")
    include_accounts = filters.net_worth_view in ("total_accounts", "accounts_only")
    if include_total and nw_months:
        nw_series.append({
            "kind": "total",
            "label": "Total Net Worth",
            "color": TOTAL_NW_COLOR,
            "values": total_balances,
        })
    if include_accounts:
        for idx, row in enumerate(account_balance_rows):
            nw_series.append({
                "kind": "account",
                "label": row["label"],
                "color": NW_COLORS[idx % len(NW_COLORS)],
                "values": row["raw_balances"],
            })

    current_net_worth = total_balances[-1] if total_balances else 0
    nw_chart_bars, nw_chart_legend = _net_worth_chart_bars(filters, account_balance_rows, total_balances, nw_months)
    nw_trailing_averages = _trailing_value_averages(total_balances, window=12)

    return {
        "filters": filters,
        "date_presets": DATE_PRESETS,
        "net_worth_views": NET_WORTH_VIEWS,
        "categories": categories,
        "expense_accounts": [a for a in accounts if a.account_type == "expenses" and not a.is_archived],
        "net_worth_accounts": active_net_worth_accounts,
        "this_month_expenses": cents_abs(this_month_expenses),
        "this_month_expenses_projection": _year_projection(this_month_expenses),
        "selected_expenses": cents_abs(selected_expenses),
        "selected_expenses_projection": _year_projection(monthly_average),
        "avg_monthly_expenses": cents_abs(monthly_average),
        "avg_monthly_expenses_projection": _year_projection(monthly_average),
        "current_net_worth": cents_dollars(current_net_worth),
        "expense_bars": expense_bars,
        "expense_chart_legend": expense_chart_legend,
        "expense_chart_width_style": _chart_width_style(len(expense_months)),
        "expense_trailing_avg_points": _line_points(trailing_averages, max_expense),
        "expense_year_markers": _year_markers(
            expense_months,
            trailing_averages,
            lambda average: f"{cents_abs(average * 12)}/yr",
            "annualized spending",
        ),
        "expense_months": [dash_month_label(month) for month in expense_months],
        "cat_months": [dash_month_label(month) for month in visible_category_months],
        "cat_month_rows": category_rows,
        "nw_months": [dash_month_label(month) for month in nw_months],
        "nw_chart_width_style": _chart_width_style(len(nw_months)),
        "nw_year_markers": _year_markers(
            nw_months,
            nw_trailing_averages,
            cents_dollars,
            "12-month avg",
        ),
        "nw_chart_bars": nw_chart_bars,
        "nw_chart_legend": nw_chart_legend,
        "nw_trailing_avg_points": _line_points(nw_trailing_averages, max((max(total, 0) for total in total_balances), default=1) or 1),
        "nw_trailing_avg_values": [cents_dollars(value) for value in nw_trailing_averages],
        "nw_table_rows": [
            {
                "label": row["label"],
                "balances": [cents_dollars(balance) for balance in row["raw_balances"]],
            }
            for row in account_balance_rows
        ],
        "nw_series": nw_series,
    }


def dash_month_label(yyyy_mm: str) -> str:
    try:
        t = datetime.strptime(yyyy_mm, "%Y-%m")
        return t.strftime("%b '%y")
    except Exception:
        return yyyy_mm


def _monthly_expense_totals(txns: list[Transaction]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for txn in txns:
        month = _txn_month(txn)
        if not month:
            continue
        totals[month] = totals.get(month, 0) + (-txn.amount)
    return totals


def _category_month_rows(txns: list[Transaction], months: list[str]) -> list[dict]:
    if not months:
        return []

    month_set = set(months)
    totals_by_key: dict[tuple[str, str], int] = {}
    totals_by_category: dict[str, int] = {}
    for txn in txns:
        month = _txn_month(txn)
        if month not in month_set:
            continue
        category = txn.category_label or "Uncategorized"
        amount = -txn.amount
        totals_by_key[(category, month)] = totals_by_key.get((category, month), 0) + amount
        totals_by_category[category] = totals_by_category.get(category, 0) + amount

    rows = []
    for category in sorted(totals_by_category, key=lambda name: totals_by_category[name], reverse=True):
        month_totals = [totals_by_key.get((category, month), 0) for month in months]
        rows.append({
            "category": category,
            "totals": ["—" if amount == 0 else cents_abs(amount) for amount in month_totals],
            "total": cents_abs(totals_by_category[category]),
        })
    return rows


def _expense_chart_bars(
    txns: list[Transaction],
    months: list[str],
    month_totals: dict[str, int],
    trailing_averages: list[int],
    max_expense: int,
) -> tuple[list[dict], list[dict]]:
    totals_by_category: dict[str, int] = {}
    values_by_month: dict[str, dict[str, int]] = {month: {} for month in months}
    for txn in txns:
        month = _txn_month(txn)
        if month not in values_by_month:
            continue
        category = txn.category_label or "Uncategorized"
        amount = max(-txn.amount, 0)
        values_by_month[month][category] = values_by_month[month].get(category, 0) + amount
        totals_by_category[category] = totals_by_category.get(category, 0) + amount

    category_order = sorted(totals_by_category, key=lambda category: (-totals_by_category[category], category))
    colors = {
        category: EXPENSE_COLORS[idx % len(EXPENSE_COLORS)]
        for idx, category in enumerate(category_order)
    }
    legend = [{"label": category, "color": colors[category]} for category in category_order]

    bars = []
    for idx, month in enumerate(months):
        segments = [
            {
                "label": category,
                "value_fmt": cents_abs(amount),
                "height_style": f"height:{amount / max_expense * 100:.1f}%",
                "color": colors[category],
            }
            for category, amount in (
                (category, values_by_month[month].get(category, 0))
                for category in category_order
            )
            if amount > 0
        ]
        bars.append({
            "month": dash_month_label(month),
            "amt_fmt": cents_abs(month_totals[month]),
            "total_compact": _compact_currency(month_totals[month]),
            "total_position_style": f"bottom:{max(month_totals[month], 0) / max_expense * 100:.1f}%",
            "trailing_avg_fmt": cents_abs(trailing_averages[idx]),
            "segments": segments,
        })
    return bars, legend


def _monthly_average(month_totals: dict[str, int]) -> int:
    if not month_totals:
        return 0
    return sum(month_totals.values()) // len(month_totals)


def _year_projection(monthly_amount: int) -> str:
    return f"{cents_abs(monthly_amount * 12)}/year"


def _compact_currency(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    dollars = abs(cents) / 100
    if dollars < 999.5:
        return f"{sign}${dollars:.0f}"

    for threshold, divisor, suffix in (
        (999_500_000, 1_000_000_000, "b"),
        (999_500, 1_000_000, "m"),
        (999.5, 1_000, "k"),
    ):
        if dollars >= threshold:
            value = dollars / divisor
            precision = 1 if value < 10 else 0
            return f"{sign}${value:.{precision}f}{suffix}"

    return f"{sign}${dollars:.0f}"


def _trailing_monthly_averages(month_totals: dict[str, int], months: list[str], window: int = 12) -> list[int]:
    averages = []
    for idx, month in enumerate(months):
        trailing_months = months[max(0, idx - window + 1):idx + 1]
        total = sum(month_totals[m] for m in trailing_months)
        averages.append(total // len(trailing_months))
    return averages


def _trailing_value_averages(values: list[int], window: int = 12) -> list[int]:
    averages = []
    for idx, _ in enumerate(values):
        trailing_values = values[max(0, idx - window + 1):idx + 1]
        averages.append(sum(trailing_values) // len(trailing_values))
    return averages


def _line_points(values: list[int], max_value: int) -> str:
    if not values:
        return ""
    if len(values) == 1:
        y = 100 - (max(values[0], 0) / max_value * 100)
        return f"50.0,{y:.1f}"

    points = []
    for idx, value in enumerate(values):
        x = idx / (len(values) - 1) * 100
        y = 100 - (max(value, 0) / max_value * 100)
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def _year_markers(
    months: list[str],
    trailing_values: list[int] | None = None,
    value_formatter: Callable[[int], str] | None = None,
    value_label: str = "",
) -> list[dict[str, str]]:
    markers = []
    if len(months) < 2:
        return markers

    for idx, month in enumerate(months[1:], start=1):
        previous_year = months[idx - 1][:4]
        year = month[:4]
        if year != previous_year:
            marker = {
                "year": year,
                "left_style": f"left:{idx / len(months) * 100:.1f}%",
            }
            # A new year starts at this boundary, so use the completed trailing
            # window ending with the immediately preceding month.
            if trailing_values and value_formatter and idx - 1 < len(trailing_values):
                marker["value"] = value_formatter(trailing_values[idx - 1])
                marker["value_label"] = value_label
            markers.append(marker)
    return markers


def _chart_width_style(month_count: int) -> str:
    min_width = max(560, month_count * 44)
    return f"min-width:{min_width}px"


def _net_worth_balances(
    filters: DashboardFilters,
    accounts: list[Account],
    balances: list[AccountMonthBalance],
) -> tuple[list[str], list[dict], list[int]]:
    if not accounts or not balances:
        return [], [], []

    balance_months = sorted({b.month for b in balances if b.month})
    display_months = _display_months(filters, balance_months)
    if not display_months:
        return [], [], []

    account_ids = [a.id for a in accounts]
    balance_by_account: dict[int, dict[str, int]] = {account_id: {} for account_id in account_ids}
    for row in balances:
        if row.account_id in balance_by_account:
            balance_by_account[row.account_id][row.month] = row.balance

    processing_start = min(balance_months[0] if balance_months else display_months[0], display_months[0])
    processing_months = _months_between(processing_start, display_months[-1])
    display_set = set(display_months)

    account_rows = []
    totals_by_month = [0 for _ in display_months]
    for account in accounts:
        prior = 0
        displayed: list[int] = []
        for month in processing_months:
            if month in balance_by_account[account.id]:
                prior = balance_by_account[account.id][month]
            if month in display_set:
                displayed.append(prior)
        account_rows.append({"label": account.label, "raw_balances": displayed})
        for idx, balance in enumerate(displayed):
            totals_by_month[idx] += balance

    return display_months, account_rows, totals_by_month


def _net_worth_chart_bars(
    filters: DashboardFilters,
    account_rows: list[dict],
    total_balances: list[int],
    months: list[str],
) -> tuple[list[dict], list[dict]]:
    if not months or not total_balances:
        return [], []

    max_total = max((max(total, 0) for total in total_balances), default=1) or 1
    if filters.net_worth_view == "total_only":
        return [
            {
                "month": dash_month_label(month),
                "total_fmt": cents_dollars(total_balances[idx]),
                "total_compact": _compact_currency(total_balances[idx]),
                "total_position_style": f"bottom:{max(total_balances[idx], 0) / max_total * 100:.1f}%",
                "segments": [
                    {
                        "label": "Total Net Worth",
                        "value_fmt": cents_dollars(total_balances[idx]),
                        "height_style": f"height:{max(total_balances[idx], 0) / max_total * 100:.1f}%",
                        "color": TOTAL_NW_COLOR,
                    }
                ],
            }
            for idx, month in enumerate(months)
        ], [{"label": "Total Net Worth", "color": TOTAL_NW_COLOR}]

    legend = [
        {
            "label": row["label"],
            "color": NW_COLORS[idx % len(NW_COLORS)],
        }
        for idx, row in enumerate(account_rows)
    ]
    bars = []
    for month_idx, month in enumerate(months):
        segments = []
        visible_stack_total = 0
        for account_idx, row in enumerate(account_rows):
            value = row["raw_balances"][month_idx]
            visible_stack_total += max(value, 0)
            segments.append({
                "label": row["label"],
                "value_fmt": cents_dollars(value),
                "height_style": f"height:{max(value, 0) / max_total * 100:.1f}%",
                "color": NW_COLORS[account_idx % len(NW_COLORS)],
            })
        bars.append({
            "month": dash_month_label(month),
            "total_fmt": cents_dollars(total_balances[month_idx]),
            "total_compact": _compact_currency(total_balances[month_idx]),
            "total_position_style": f"bottom:{min(visible_stack_total / max_total * 100, 100):.1f}%",
            "segments": segments,
        })
    return bars, legend


def _display_months(filters: DashboardFilters, balance_months: list[str]) -> list[str]:
    if filters.date_from or filters.date_to:
        start = (filters.date_from or (balance_months[0].replace("-", "_") + "_01" if balance_months else "")).replace("_", "-")[:7]
        end = (filters.date_to or (balance_months[-1].replace("-", "_") + "_28" if balance_months else "")).replace("_", "-")[:7]
        if start and end:
            return _months_between(start, end)

    if not balance_months:
        return []
    return _months_between(balance_months[0], balance_months[-1])


def _months_between(start_yyyy_mm: str, end_yyyy_mm: str) -> list[str]:
    try:
        cursor = datetime.strptime(start_yyyy_mm[:7], "%Y-%m")
        end = datetime.strptime(end_yyyy_mm[:7], "%Y-%m")
    except ValueError:
        return []

    months = []
    while cursor <= end:
        months.append(cursor.strftime("%Y-%m"))
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year + 1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month + 1)
    return months


def _txn_month(txn: Transaction) -> str:
    if len(txn.date) < 7:
        return ""
    return txn.date[:7].replace("_", "-")


def _first(raw_params: Any, key: str) -> str:
    if raw_params is None:
        return ""
    if hasattr(raw_params, "get"):
        value = raw_params.get(key, "")
    else:
        value = ""
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value) if value is not None else ""


def _all(raw_params: Any, key: str) -> list[str]:
    if raw_params is None:
        return []
    if hasattr(raw_params, "getlist"):
        return [str(value) for value in raw_params.getlist(key)]
    if hasattr(raw_params, "get"):
        value = raw_params.get(key, [])
        if isinstance(value, list):
            return [str(v) for v in value]
        if value in ("", None):
            return []
        return [str(value)]
    return []


def _has(raw_params: Any, key: str) -> bool:
    if raw_params is None:
        return False
    if hasattr(raw_params, "__contains__"):
        return key in raw_params
    if hasattr(raw_params, "get"):
        return raw_params.get(key, None) is not None
    return False


def _valid_ids(raw_ids: list[str], allowed_ids: list[int], default_all: bool = True) -> list[int]:
    allowed = set(allowed_ids)
    parsed = []
    for raw_id in raw_ids:
        try:
            item = int(raw_id)
        except (TypeError, ValueError):
            continue
        if item in allowed and item not in parsed:
            parsed.append(item)
    if parsed:
        return parsed
    return list(allowed_ids) if default_all else []


def _normalize_iso_date(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return ""


def _local_today(
    now_fn: Callable[[], datetime | date] | None = None,
    timezone_name: str | None = None,
) -> date:
    tz_name = timezone_name or os.environ.get("CASHCOMPASS_TIMEZONE") or "America/Los_Angeles"
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("America/Los_Angeles")

    if now_fn:
        now = now_fn()
        if isinstance(now, datetime):
            return now.astimezone(tz).date() if now.tzinfo else now.date()
        return now
    return datetime.now(tz).date()


def _current_month_date_range(today: date) -> tuple[str, str]:
    first = date(today.year, today.month, 1)
    last = _last_day_of_month(today.year, today.month)
    return first.strftime("%Y_%m_%d"), last.strftime("%Y_%m_%d")


def _preset_dates(preset: str, today: date | None = None) -> tuple[str, str]:
    current = today or _local_today()
    year, month = current.year, current.month

    if preset == "all_time":
        return "", ""
    if preset == "this_month":
        return _current_month_date_range(current)
    if preset == "last_month":
        if month == 1:
            year, month = year - 1, 12
        else:
            month -= 1
        first = date(year, month, 1)
        last = _last_day_of_month(year, month)
        return first.strftime("%Y_%m_%d"), last.strftime("%Y_%m_%d")
    if preset == "last_3_months":
        first = _month_start_offset(current, 2)
        last = _last_day_of_month(current.year, current.month)
        return first.strftime("%Y_%m_%d"), last.strftime("%Y_%m_%d")
    if preset == "last_6_months":
        first = _month_start_offset(current, 5)
        last = _last_day_of_month(current.year, current.month)
        return first.strftime("%Y_%m_%d"), last.strftime("%Y_%m_%d")
    if preset == "this_year":
        return date(year, 1, 1).strftime("%Y_%m_%d"), date(year, 12, 31).strftime("%Y_%m_%d")
    return "", ""


def _last_day_of_month(year: int, month: int) -> date:
    if month == 12:
        return date(year + 1, 1, 1) - timedelta(days=1)
    return date(year, month + 1, 1) - timedelta(days=1)


def _month_start_offset(current: date, offset: int) -> date:
    year = current.year
    month = current.month - offset
    while month <= 0:
        year -= 1
        month += 12
    return date(year, month, 1)


def _range_label(preset: str, date_from: str, date_to: str) -> str:
    labels = dict(DATE_PRESETS)
    if preset == "custom":
        if date_from and date_to:
            return f"{date_from} to {date_to}"
        if date_from:
            return f"Since {date_from}"
        if date_to:
            return f"Through {date_to}"
    return labels.get(preset, "All time")
