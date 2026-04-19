from __future__ import annotations
import csv
import io
import math
from datetime import datetime, timezone
from urllib.parse import quote_plus

from fasthtml.common import *
from starlette.responses import RedirectResponse, Response as StarletteResponse

from src.services.account import AccountService
from src.services.category import CategoryService
from src.services.transaction import TransactionService
from src.models import TransactionFilter
from src.components.settings import settings_page
from src.components.layout import page_layout


def _parse_amount(s: str) -> int:
    s = s.replace("$", "").replace(",", "").strip()
    f = float(s)
    return int(math.floor(abs(f) * 100 + 0.5))


def _parse_date(s: str, timezone_str: str = "") -> tuple[str, str]:
    s = s.strip()
    if len(s) < 10:
        raise ValueError(f"invalid date: {s!r}")

    if len(s) == 10:
        datetime.strptime(s, "%Y-%m-%d")
        return s, s.replace("-", "_")

    normalized = s.replace("Z", "+00:00") if s.endswith("Z") else s

    for fmt in [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    ]:
        try:
            t = datetime.strptime(normalized, fmt)
            break
        except ValueError:
            continue
    else:
        raise ValueError(f"invalid date: {s!r}")

    if timezone_str:
        try:
            import zoneinfo
            loc = zoneinfo.ZoneInfo(timezone_str)
            if t.tzinfo is None:
                from datetime import timezone as tz
                t = t.replace(tzinfo=tz.utc)
            t = t.astimezone(loc)
        except Exception:
            pass

    date_part = t.strftime("%Y-%m-%d")
    return date_part, date_part.replace("-", "_")


def register(rt, acct_svc: AccountService, cat_svc: CategoryService,
             txn_svc: TransactionService, dev_mode: bool):

    @rt("/settings", methods=["GET"])
    def get(req: Request):
        imported_type = req.query_params.get("imported", "")
        error_msg = req.query_params.get("error", "")
        count_str = req.query_params.get("count", "0")
        reset = req.query_params.get("reset", "") == "1"
        try:
            count = int(count_str)
        except (ValueError, TypeError):
            count = 0
        return page_layout("settings", *settings_page(
            imported_type=imported_type,
            imported_count=count,
            error_msg=error_msg,
            dev_mode=dev_mode,
            reset=reset,
        ))

    @rt("/settings/import/expenses", methods=["POST"])
    async def post_import_expenses(req: Request):
        form = await req.form()
        timezone_str = form.get("timezone", "UTC") or "UTC"
        file = form.get("file")
        if file is None:
            return RedirectResponse(f"/settings?error={quote_plus('no file uploaded')}", status_code=303)

        try:
            content = await file.read()
            text = content.decode("utf-8", errors="replace")
            reader = csv.DictReader(io.StringIO(text))
            rows = list(reader)
        except Exception as e:
            return RedirectResponse(f"/settings?error={quote_plus(str(e))}", status_code=303)

        for required in ("Amount", "Category", "Date", "Description"):
            if not rows or required not in rows[0]:
                return RedirectResponse(f"/settings?error={quote_plus(f'missing column: {required}')}", status_code=303)

        import_acct = acct_svc.create(
            f"Imported Expenses {datetime.now(timezone.utc).isoformat()}",
            "expenses"
        )

        cats = cat_svc.list()
        cat_map = {c.label: c for c in cats}
        count = 0

        for row in rows:
            amt_str = row.get("Amount", "").strip()
            cat_label = row.get("Category", "").strip()
            date_str = row.get("Date", "").strip()
            desc = row.get("Description", "").strip()

            if not date_str:
                continue
            try:
                cents = _parse_amount(amt_str)
                cents = -abs(cents)
            except Exception:
                continue

            try:
                iso8601, ymd = _parse_date(date_str, timezone_str)
            except Exception:
                continue

            if cat_label not in cat_map:
                cat = cat_svc.create(cat_label)
                cat_map[cat_label] = cat
            cat = cat_map[cat_label]

            txn_svc.create(iso8601, ymd, cents, desc, import_acct.id, import_acct.label, cat.id, cat.label)
            count += 1

        return RedirectResponse(f"/settings?imported=expenses&count={count}", status_code=303)

    @rt("/settings/export/expenses", methods=["GET"])
    def get_export_expenses():
        txns = txn_svc.list(TransactionFilter(account_type="expenses"))
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Amount", "Category", "Date", "Description"])
        for t in txns:
            amt = f"{abs(t.amount) / 100:.2f}"
            cat = t.category_label or "Uncategorized"
            w.writerow([amt, cat, t.iso8601, t.label])
        return StarletteResponse(
            buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="expenses.csv"'},
        )

    @rt("/settings/import/accounts", methods=["POST"])
    async def post_import_accounts(req: Request):
        form = await req.form()
        timezone_str = form.get("timezone", "UTC") or "UTC"
        file = form.get("file")
        if file is None:
            return RedirectResponse(f"/settings?error={quote_plus('no file uploaded')}", status_code=303)

        try:
            content = await file.read()
            text = content.decode("utf-8", errors="replace")
            reader = csv.DictReader(io.StringIO(text))
            rows = list(reader)
        except Exception as e:
            return RedirectResponse(f"/settings?error={quote_plus(str(e))}", status_code=303)

        for required in ("Account", "Date", "Balance"):
            if not rows or required not in rows[0]:
                return RedirectResponse(f"/settings?error={quote_plus(f'missing column: {required}')}", status_code=303)

        cats = cat_svc.list()
        cat_map = {c.label: c for c in cats}
        if "Reconciliation" not in cat_map:
            rec_cat = cat_svc.create("Reconciliation")
            cat_map["Reconciliation"] = rec_cat
        reconcile_cat = cat_map["Reconciliation"]

        all_accts = acct_svc.list()
        acct_map = {a.label: a for a in all_accts if a.account_type == "net_worth"}

        grouped = {}
        for row in rows:
            acct_label = row.get("Account", "").strip()
            date_str = row.get("Date", "").strip()
            bal_str = row.get("Balance", "").strip()
            if not acct_label or not date_str:
                continue
            grouped.setdefault(acct_label, []).append({"date": date_str, "balance": bal_str})

        count = 0
        for acct_label in sorted(grouped.keys()):
            if acct_label not in acct_map:
                acct = acct_svc.create(acct_label, "net_worth")
                acct_map[acct_label] = acct
            acct = acct_map[acct_label]

            rows_sorted = sorted(grouped[acct_label], key=lambda r: r["date"])
            prev_balance = 0
            for row in rows_sorted:
                try:
                    cents = _parse_amount(row["balance"])
                except Exception:
                    continue
                delta = cents - prev_balance
                if delta == 0:
                    prev_balance = cents
                    continue
                try:
                    iso8601, ymd = _parse_date(row["date"], timezone_str)
                except Exception:
                    continue

                txn_svc.create(iso8601, ymd, delta, "Reconciliation", acct.id, acct.label, reconcile_cat.id, reconcile_cat.label)
                count += 1
                prev_balance = cents

        return RedirectResponse(f"/settings?imported=accounts&count={count}", status_code=303)

    @rt("/settings/export/accounts", methods=["GET"])
    def get_export_accounts():
        all_accts = acct_svc.list()
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Account", "Date", "Balance"])

        for acct in all_accts:
            if acct.account_type != "net_worth":
                continue
            txns = txn_svc.list(TransactionFilter(account_ids=[acct.id]))
            txns_asc = list(reversed(txns))  # txns are DESC; reverse to ASC
            dates = []
            bal_map = {}
            cumulative = 0
            for t in txns_asc:
                cumulative += t.amount
                d = t.iso8601[:10] if t.iso8601 else t.date.replace("_", "-")[:10]
                if d not in bal_map:
                    dates.append(d)
                bal_map[d] = cumulative
            for d in dates:
                bal = f"{bal_map[d] / 100:.2f}"
                w.writerow([acct.label, d, bal])

        return StarletteResponse(
            buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="accounts.csv"'},
        )

    @rt("/settings/reset-database", methods=["POST"])
    def post_reset():
        if not dev_mode:
            return StarletteResponse("not available", status_code=403)

        txns = txn_svc.list(TransactionFilter())
        for t in txns:
            txn_svc.delete(t.id)

        cats = cat_svc.list()
        for c in cats:
            cat_svc.delete(c.id)

        accts = acct_svc.list()
        for a in accts:
            acct_svc.delete(a.id)

        return RedirectResponse("/settings?reset=1", status_code=303)
