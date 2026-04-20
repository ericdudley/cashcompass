from __future__ import annotations
import math
import logging
from datetime import datetime, timezone
from urllib.parse import urlencode

from fasthtml.common import *
from fasthtml.common import to_xml
from starlette.responses import Response as StarletteResponse

from src.models import TransactionFilter
from src.services.account import AccountService
from src.services.category import CategoryService
from src.services.category_recommendation import CategoryRecommendationService
from src.services.transaction import TransactionService
from src.components.transactions import (
    transaction_category_recommendation_panel, transaction_row, transaction_row_edit, transactions_list, transactions_page
)
from src.components.layout import page_layout
from src.utils.dates import preset_to_dates

logger = logging.getLogger("cashcompass.ai")


def _parse_filter(query_params, form_data=None) -> TransactionFilter:
    q = dict(query_params)
    fd = form_data or {}

    at = q.get("account_type", fd.get("account_type", "expenses"))
    if isinstance(at, list):
        at = at[0]
    if at not in ("expenses", "net_worth"):
        at = "expenses"

    date_preset = q.get("date_preset", "")
    if isinstance(date_preset, list):
        date_preset = date_preset[0]

    date_from = q.get("date_from", "")
    if isinstance(date_from, list):
        date_from = date_from[0]
    date_to = q.get("date_to", "")
    if isinstance(date_to, list):
        date_to = date_to[0]

    if not date_preset and not date_from and not date_to:
        date_preset = "this_month"

    label = q.get("label", "")
    if isinstance(label, list):
        label = label[0]

    cat_ids_raw = q.get("category_id", [])
    if isinstance(cat_ids_raw, str):
        cat_ids_raw = [cat_ids_raw]
    category_ids = []
    for s in cat_ids_raw:
        try:
            category_ids.append(int(s))
        except (ValueError, TypeError):
            pass

    return TransactionFilter(
        date_from=date_from,
        date_to=date_to,
        label=label,
        category_ids=category_ids,
        account_type=at,
    ), date_preset


def _filter_to_model(f: TransactionFilter, date_preset: str) -> TransactionFilter:
    mf = TransactionFilter(
        label=f.label,
        category_ids=f.category_ids,
        account_type=f.account_type,
    )
    if date_preset and date_preset != "all_time":
        dfrom, dto = preset_to_dates(date_preset)
        mf.date_from = dfrom
        mf.date_to = dto
    else:
        if f.date_from:
            mf.date_from = f.date_from.replace("-", "_")
        if f.date_to:
            mf.date_to = f.date_to.replace("-", "_")
    return mf


def _filter_qs(f: TransactionFilter, date_preset: str) -> str:
    params = [("account_type", f.account_type)]
    if date_preset:
        params.append(("date_preset", date_preset))
    if f.date_from:
        params.append(("date_from", f.date_from))
    if f.date_to:
        params.append(("date_to", f.date_to))
    if f.label:
        params.append(("label", f.label))
    for cid in f.category_ids:
        params.append(("category_id", str(cid)))
    return urlencode(params)


def _group_transactions(txns) -> list[dict]:
    groups = []
    idx = {}
    for t in txns:
        date = t.date.replace("_", "-")[:10]
        if date not in idx:
            groups.append({"date": date, "transactions": [], "subtotal": 0})
            idx[date] = len(groups) - 1
        i = idx[date]
        groups[i]["transactions"].append(t)
        groups[i]["subtotal"] += t.amount
    return groups


def _build_filter_state(f: TransactionFilter, date_preset: str):
    class FilterState:
        pass
    fs = FilterState()
    fs.account_type = f.account_type
    fs.date_preset = date_preset
    fs.date_from = f.date_from
    fs.date_to = f.date_to
    fs.label = f.label
    fs.category_ids = f.category_ids
    return fs


def _parse_amount_cents(amount_str: str, mode: str) -> int:
    try:
        amount = float(amount_str)
    except (ValueError, TypeError):
        return 0

    cents = int(math.floor(abs(amount) * 100 + 0.5))
    if mode == "debit":
        cents = -cents
    return cents


def _parse_amount_cents_strict(amount_str: str, mode: str) -> int:
    try:
        float(amount_str)
    except (ValueError, TypeError) as exc:
        raise ValueError("transaction amount must be a number") from exc
    return _parse_amount_cents(amount_str, mode)


def register(
    rt,
    txn_svc: TransactionService,
    acct_svc: AccountService,
    cat_svc: CategoryService,
    category_recommendation_svc: CategoryRecommendationService,
):

    @rt("/transactions", methods=["GET"])
    def get(req: Request):
        f, date_preset = _parse_filter(req.query_params)
        mf = _filter_to_model(f, date_preset)
        txns = txn_svc.list(mf)
        cats = cat_svc.list()
        groups = _group_transactions(txns)
        fs = _build_filter_state(f, date_preset)

        all_accts = acct_svc.list()
        mode_accts = [a for a in all_accts if a.account_type == f.account_type and not a.is_archived]

        last_acct = 0
        if "last_account_id" in req.cookies:
            try:
                last_acct = int(req.cookies["last_account_id"])
            except (ValueError, TypeError):
                pass

        form_data = {
            "accounts": mode_accts,
            "categories": cats,
            "today": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "last_account_id": last_acct,
            "account_type": f.account_type,
            "ai_enabled": category_recommendation_svc.is_enabled,
        }

        return page_layout("transactions", *transactions_page(groups, fs, cats, form_data))

    @rt("/transactions", methods=["POST"])
    async def post(req: Request):
        form = await req.form()
        date_str = form.get("date", "")  # yyyy-mm-dd
        label = form.get("label", "")
        amt_str = form.get("amount", "0")
        mode = form.get("amount_mode", "debit")
        account_id_str = form.get("account_id", "")
        category_id_str = form.get("category_id", "0")

        cents = _parse_amount_cents(amt_str, mode)

        try:
            account_id = int(account_id_str)
            acct = acct_svc.get_by_id(account_id)
        except (ValueError, TypeError, Exception):
            account_id = None
            acct = None

        acct_label = acct.label if acct else ""
        iso_date = date_str  # yyyy-mm-dd
        ymd = date_str.replace("-", "_")  # yyyy_mm_dd

        cat_id = None
        cat_label = ""
        try:
            cid = int(category_id_str)
            if cid > 0:
                cat = cat_svc.get_by_id(cid)
                cat_id = cid
                cat_label = cat.label
        except (ValueError, TypeError, Exception):
            pass

        try:
            txn_svc.create(iso_date, ymd, cents, label, account_id, acct_label, cat_id, cat_label)
        except ValueError as exc:
            return Response(str(exc), status_code=400)

        # Re-render list with current filter state
        f, date_preset = _parse_filter(req.query_params, dict(form))
        mf = _filter_to_model(f, date_preset)
        txns = txn_svc.list(mf)
        cats = cat_svc.list()
        groups = _group_transactions(txns)
        fs = _build_filter_state(f, date_preset)

        response = StarletteResponse(
            to_xml(transactions_list(groups, fs, cats)),
            media_type="text/html",
        )
        response.set_cookie("last_account_id", str(account_id or ""), path="/")
        return response

    @rt("/partials/transactions/recommend-category", methods=["POST"])
    async def recommend_category(req: Request):
        if not category_recommendation_svc.is_enabled:
            return ""

        form = await req.form()
        date_str = str(form.get("date", "") or "").strip()
        label = str(form.get("label", "") or "").strip()
        mode = str(form.get("amount_mode", "debit") or "debit")
        category_id_str = str(form.get("category_id", "0") or "0")
        cents = _parse_amount_cents(str(form.get("amount", "0") or "0"), mode)
        if not date_str or not label or cents == 0:
            logger.info(
                "Skipping category recommendation; incomplete inputs date=%s label_present=%s amount_cents=%s",
                bool(date_str),
                bool(label),
                cents,
            )
            return transaction_category_recommendation_panel(True)

        categories = cat_svc.list()
        logger.info(
            "Requesting category recommendation for date=%s amount_cents=%s label=%r categories=%s",
            date_str,
            cents,
            label,
            [c.label for c in categories],
        )
        recommendation = category_recommendation_svc.recommend_category(date_str, cents, label, categories)
        if not recommendation.has_recommendation:
            logger.info("No category recommendation rendered for label=%r", label)
            return transaction_category_recommendation_panel(True)

        try:
            selected_category_id = int(category_id_str)
        except (ValueError, TypeError):
            selected_category_id = 0
        if selected_category_id == recommendation.category_id:
            logger.info(
                "Suppressing category recommendation because selected category already matches category_id=%s",
                recommendation.category_id,
            )
            return transaction_category_recommendation_panel(True)

        logger.info(
            "Rendering category recommendation category_id=%s label=%s",
            recommendation.category_id,
            recommendation.category_label,
        )
        return transaction_category_recommendation_panel(True, recommendation)

    @rt("/partials/transactions", methods=["GET"])
    def get_list(req: Request):
        f, date_preset = _parse_filter(req.query_params)
        mf = _filter_to_model(f, date_preset)
        txns = txn_svc.list(mf)
        cats = cat_svc.list()
        groups = _group_transactions(txns)
        fs = _build_filter_state(f, date_preset)

        push_url = "/transactions?" + _filter_qs(f, date_preset)
        return StarletteResponse(
            to_xml(transactions_list(groups, fs, cats)),
            media_type="text/html",
            headers={"HX-Push-Url": push_url},
        )

    @rt("/partials/transactions/{id}", methods=["GET"])
    def get_row(id: int):
        return transaction_row(txn_svc.get_by_id(id))

    @rt("/partials/transactions/{id}/edit", methods=["GET"])
    def get_row_edit(id: int):
        txn = txn_svc.get_by_id(id)
        accts = acct_svc.list()
        cats = cat_svc.list()
        return transaction_row_edit(txn, accts, cats)

    @rt("/transactions/{id}", methods=["PUT"])
    async def put(req: Request, id: int):
        form = await req.form()
        form_data = dict(form)
        date_str = form.get("date")
        label = form.get("label")
        amt_str = form.get("amount", "")
        mode = form.get("amount_mode", "debit")
        account_id_str = form.get("account_id")
        category_id_str = form.get("category_id")

        try:
            if date_str is not None:
                txn_svc.update_date(id, date_str, date_str.replace("-", "_"))

            if label is not None:
                txn_svc.update_label(id, label)

            if amt_str != "":
                cents = _parse_amount_cents_strict(amt_str, mode)
                txn_svc.update_amount(id, cents)

            if account_id_str is not None:
                try:
                    aid = int(account_id_str)
                    acct = acct_svc.get_by_id(aid)
                except Exception as exc:
                    raise ValueError("transaction account is invalid") from exc
                txn_svc.update_account(id, aid, acct.label)

            if category_id_str is not None:
                try:
                    cid = int(category_id_str)
                except (ValueError, TypeError) as exc:
                    raise ValueError("transaction category is invalid") from exc
                if cid > 0:
                    try:
                        cat = cat_svc.get_by_id(cid)
                    except Exception as exc:
                        raise ValueError("transaction category is invalid") from exc
                    txn_svc.update_category(id, cid, cat.label)
                else:
                    txn_svc.update_category(id, None, "")
        except ValueError as exc:
            return Response(str(exc), status_code=400)

        f, date_preset = _parse_filter(req.query_params, form_data)
        mf = _filter_to_model(f, date_preset)
        txns = txn_svc.list(mf)
        cats = cat_svc.list()
        groups = _group_transactions(txns)
        fs = _build_filter_state(f, date_preset)
        return transactions_list(groups, fs, cats)

    @rt("/transactions/{id}", methods=["DELETE"])
    def delete(req: Request, id: int):
        txn_svc.delete(id)
        f, date_preset = _parse_filter(req.query_params)
        mf = _filter_to_model(f, date_preset)
        txns = txn_svc.list(mf)
        cats = cat_svc.list()
        groups = _group_transactions(txns)
        fs = _build_filter_state(f, date_preset)
        return transactions_list(groups, fs, cats)
