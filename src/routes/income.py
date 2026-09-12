from __future__ import annotations

from fasthtml.common import *

from src.components.income import (
    annual_income_card,
    annual_income_card_edit,
    annual_income_list,
    annual_income_page,
)
from src.components.layout import page_layout
from src.services.annual_income import AnnualIncomeService
from src.utils.format import parse_cents


def _parse_form(form) -> tuple[int, int, int, int, str]:
    try:
        tax_year = int(str(form.get("tax_year", "")).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError("tax year must be a number") from exc

    def money(field: str, label: str, default: str = "0") -> int:
        raw = str(form.get(field, default) or default)
        try:
            return parse_cents(raw)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{label} must be a valid amount") from exc

    return (
        tax_year,
        money("gross_income", "gross income", ""),
        money("federal_tax", "federal tax"),
        money("state_tax", "state tax"),
        str(form.get("notes", "") or ""),
    )


def register(rt, income_svc: AnnualIncomeService):
    @rt("/income", methods=["GET"])
    def get():
        return page_layout("income", *annual_income_page(income_svc.list()))

    @rt("/income", methods=["POST"])
    async def post(req: Request):
        form = await req.form()
        try:
            income_svc.create(*_parse_form(form))
        except ValueError as exc:
            return Response(str(exc), status_code=400)
        return annual_income_list(income_svc.list())

    @rt("/income/{id}", methods=["PUT"])
    async def put(req: Request, id: int):
        form = await req.form()
        try:
            income_svc.update(id, *_parse_form(form))
        except ValueError as exc:
            return Response(str(exc), status_code=400)
        return annual_income_list(income_svc.list())

    @rt("/income/{id}", methods=["DELETE"])
    def delete(id: int):
        try:
            income_svc.delete(id)
        except ValueError as exc:
            return Response(str(exc), status_code=404)
        return annual_income_list(income_svc.list())

    @rt("/partials/income/{id}", methods=["GET"])
    def get_card(id: int):
        return annual_income_card(income_svc.get_by_id(id))

    @rt("/partials/income/{id}/edit", methods=["GET"])
    def get_card_edit(id: int):
        return annual_income_card_edit(income_svc.get_by_id(id))
