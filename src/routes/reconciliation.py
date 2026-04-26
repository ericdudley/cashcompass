from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from fasthtml.common import *
from fasthtml.common import to_xml
from starlette.responses import RedirectResponse
from starlette.responses import Response as StarletteResponse

from src.components.layout import page_layout
from src.components.reconciliation import reconciliation_page
from src.services.reconciliation import ReconciliationService


def _parse_balance_cents(raw_value: str) -> int:
    normalized = (raw_value or "").strip().replace("$", "").replace(",", "")
    if not normalized:
        raise ValueError("latest balance is required")
    try:
        amount = Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError("latest balance must be a valid number") from exc
    cents = int((amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return cents


def _render_page(
    reconciliation_svc: ReconciliationService,
    latest_values: dict[int, str] | None = None,
    invalid_accounts: set[int] | None = None,
    success_count: int = 0,
    status_msg: str = "",
    error_msg: str = "",
):
    rows = reconciliation_svc.list_rows()
    return page_layout(
        "accounts",
        *reconciliation_page(
            rows,
            latest_values=latest_values,
            invalid_accounts=invalid_accounts,
            success_count=success_count,
            status_msg=status_msg,
            error_msg=error_msg,
        ),
    )


def register(rt, reconciliation_svc: ReconciliationService):

    @rt("/accounts/reconcile", methods=["GET"])
    def get(req: Request):
        saved_str = req.query_params.get("saved", "0")
        status = req.query_params.get("status", "")
        try:
            saved_count = int(saved_str)
        except (TypeError, ValueError):
            saved_count = 0

        status_msg = ""
        if status == "no_changes":
            status_msg = "No balance adjustments were needed."

        return _render_page(
            reconciliation_svc,
            success_count=saved_count,
            status_msg=status_msg,
        )

    @rt("/accounts/reconcile", methods=["POST"])
    async def post(req: Request):
        form = await req.form()
        rows = reconciliation_svc.list_rows()
        latest_values = {}
        invalid_accounts = set()
        latest_balance_cents = {}

        for row in rows:
            field_name = f"latest_balance_{row.account.id}"
            raw_value = str(form.get(field_name, "") or "").strip()
            latest_values[row.account.id] = raw_value
            if not raw_value:
                latest_balance_cents[row.account.id] = None
                continue
            try:
                latest_balance_cents[row.account.id] = _parse_balance_cents(raw_value)
            except ValueError:
                invalid_accounts.add(row.account.id)

        if invalid_accounts:
            return StarletteResponse(
                to_xml(_render_page(
                    reconciliation_svc,
                    latest_values=latest_values,
                    invalid_accounts=invalid_accounts,
                    error_msg="Enter valid balances for every non-blank row.",
                )),
                media_type="text/html",
                status_code=400,
            )

        today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        saved_count = reconciliation_svc.create_adjustments(latest_balance_cents, today_iso)

        if saved_count == 0:
            return RedirectResponse("/accounts/reconcile?status=no_changes", status_code=303)
        return RedirectResponse(f"/accounts/reconcile?saved={saved_count}", status_code=303)
