from __future__ import annotations
import math
import string
from datetime import datetime, timezone

from fasthtml.common import *
from src.services.account import AccountService
from src.services.category import CategoryService
from src.services.transaction import TransactionService
from src.models import TransactionFilter
from src.components.dashboard import dashboard_page, dash_month_label, NW_COLORS
from src.components.layout import page_layout
from src.utils.format import cents_abs, cents_dollars


def register(rt, acct_svc: AccountService, cat_svc: CategoryService, txn_svc: TransactionService):

    @rt("/dashboard", methods=["GET"])
    def get():
        now = datetime.now(timezone.utc)
        this_month = now.strftime("%Y-%m")
        prev_month = (now.replace(day=1) if now.month > 1
                      else now.replace(year=now.year - 1, month=12, day=1))
        if now.month == 1:
            prev_month_str = f"{now.year - 1}-12"
        else:
            prev_month_str = f"{now.year}-{now.month - 1:02d}"

        exp_sums = txn_svc.sum_by_month("expenses")
        exp_map = {s.month: -s.amount for s in exp_sums}

        this_month_exp = exp_map.get(this_month, 0)
        prev_month_exp = exp_map.get(prev_month_str, 0)

        change_str = ""
        change_pos = False
        if prev_month_exp > 0:
            pct = (this_month_exp - prev_month_exp) / prev_month_exp * 100
            if pct >= 0:
                change_str = f"+{pct:.0f}%"
            else:
                change_str = f"{pct:.0f}%"
                change_pos = True

        avg_sum = sum(-s.amount for s in exp_sums if s.month < this_month)
        avg_count = sum(1 for s in exp_sums if s.month < this_month)
        avg_str = cents_abs(avg_sum // avg_count) if avg_count > 0 else "$0.00"

        all_exp_months = sorted(exp_map.keys())
        if len(all_exp_months) > 12:
            all_exp_months = all_exp_months[-12:]

        max_exp = max((exp_map[m] for m in all_exp_months), default=1) or 1

        expense_bars = []
        expense_months = []
        for m in all_exp_months:
            amt = exp_map[m]
            pct = amt / max_exp * 100
            expense_bars.append({
                "month": dash_month_label(m),
                "amt_fmt": cents_abs(amt),
                "height_style": f"height:{pct:.1f}%",
            })
            expense_months.append(dash_month_label(m))

        # Category-by-month table (last 6 months)
        cat_months = all_exp_months[-6:] if len(all_exp_months) > 6 else all_exp_months
        cat_month_rows = []
        cat_months_labels = [dash_month_label(m) for m in cat_months]

        if cat_months:
            last_m = cat_months[-1]
            try:
                t = datetime.strptime(last_m, "%Y-%m")
                if t.month == 12:
                    end_dt = datetime(t.year + 1, 1, 1)
                else:
                    end_dt = datetime(t.year, t.month + 1, 1)
                end_str = end_dt.strftime("%Y_%m_%d")
                # subtract one day
                from datetime import timedelta
                end_str = (datetime.strptime(end_str, "%Y_%m_%d") - timedelta(days=1)).strftime("%Y_%m_%d")
            except Exception:
                end_str = ""

            start_str = cat_months[0].replace("-", "_") + "_01"
            txns = txn_svc.list(TransactionFilter(
                account_type="expenses",
                date_from=start_str,
                date_to=end_str,
            ))

            cat_month_map = {}
            cat_totals = {}
            cat_order = []
            cat_seen = set()

            for txn in txns:
                cat = txn.category_label or "Uncategorized"
                m = ""
                if len(txn.date) >= 7:
                    m = txn.date[:7].replace("_", "-")
                key = (cat, m)
                cat_month_map[key] = cat_month_map.get(key, 0) + (-txn.amount)
                cat_totals[cat] = cat_totals.get(cat, 0) + (-txn.amount)
                if cat not in cat_seen:
                    cat_seen.add(cat)
                    cat_order.append(cat)

            cat_order.sort(key=lambda c: cat_totals[c], reverse=True)

            for c in cat_order:
                totals = []
                for m in cat_months:
                    amt = cat_month_map.get((c, m), 0)
                    totals.append("—" if amt == 0 else cents_abs(amt))
                cat_month_rows.append({
                    "category": c,
                    "totals": totals,
                    "total": cents_abs(cat_totals[c]),
                })

        # Net worth
        all_accts = acct_svc.list()
        nw_ids = [a.id for a in all_accts if a.account_type == "net_worth" and not a.is_archived]

        balances = txn_svc.balances_by_month(nw_ids)

        nw_month_set = set()
        nw_map = {}
        nw_label_map = {}
        for b in balances:
            nw_month_set.add(b.month)
            if b.account_id not in nw_map:
                nw_map[b.account_id] = {}
            nw_map[b.account_id][b.month] = b.balance
            nw_label_map[b.account_id] = b.account_label

        nw_months = sorted(nw_month_set)
        nw_month_labels = [dash_month_label(m) for m in nw_months]

        total_nw = 0
        if nw_months:
            latest = nw_months[-1]
            for aid in nw_ids:
                if aid in nw_map:
                    prev = 0
                    for m in nw_months:
                        if m in nw_map[aid]:
                            prev = nw_map[aid][m]
                        if m == latest:
                            break
                    total_nw += prev

        nw_table_rows = []
        for aid in nw_ids:
            if aid not in nw_map:
                continue
            mb = nw_map[aid]
            balstr = []
            prev = 0
            for m in nw_months:
                if m in mb:
                    prev = mb[m]
                balstr.append(cents_dollars(prev))
            nw_table_rows.append({"label": nw_label_map[aid], "balances": balstr})

        # SVG net worth lines
        nw_lines = []
        if len(nw_months) >= 2:
            all_balances_flat = []
            for aid in nw_ids:
                if aid not in nw_map:
                    continue
                prev = 0
                for m in nw_months:
                    if m in nw_map[aid]:
                        prev = nw_map[aid][m]
                    all_balances_flat.append(prev)

            min_bal = min(all_balances_flat) if all_balances_flat else 0
            max_bal = max(all_balances_flat) if all_balances_flat else 1
            if min_bal == max_bal:
                max_bal = min_bal + 1

            SVG_W, SVG_H = 400.0, 150.0
            PAD_L, PAD_R, PAD_T, PAD_B = 10.0, 10.0, 10.0, 20.0

            for ci, aid in enumerate(nw_ids):
                if aid not in nw_map:
                    continue
                pts = []
                prev = 0
                for i, m in enumerate(nw_months):
                    if m in nw_map[aid]:
                        prev = nw_map[aid][m]
                    x = PAD_L + i / (len(nw_months) - 1) * (SVG_W - PAD_L - PAD_R)
                    y = PAD_T + (1 - (prev - min_bal) / (max_bal - min_bal)) * (SVG_H - PAD_T - PAD_B)
                    pts.append(f"{x:.1f},{y:.1f}")

                color = NW_COLORS[ci % len(NW_COLORS)]
                nw_lines.append({
                    "label": nw_label_map[aid],
                    "points": " ".join(pts),
                    "color": color,
                })

        data = {
            "this_month_expenses": cents_abs(this_month_exp),
            "expense_change_pct": change_str,
            "expense_change_pos": change_pos,
            "avg_monthly_expenses": avg_str,
            "current_net_worth": cents_dollars(total_nw),
            "expense_bars": expense_bars,
            "expense_months": expense_months,
            "cat_months": cat_months_labels,
            "cat_month_rows": cat_month_rows,
            "nw_months": nw_month_labels,
            "nw_table_rows": nw_table_rows,
            "nw_lines": nw_lines,
        }

        return page_layout("dashboard", *dashboard_page(data))
