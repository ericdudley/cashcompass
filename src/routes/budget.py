from fasthtml.common import *
from starlette.responses import RedirectResponse
from urllib.parse import urlencode

from src.components.budget import budget_page, budget_edit, context_url
from src.components.layout import page_layout
from src.services.budget import BudgetService


def register(rt, budget_svc: BudgetService):
    def context(params):
        return budget_svc.build(str(params.get("month", "")), view=str(params.get("view", "monthly")),
                                requested_year=str(params.get("year", "")))

    @rt("/budget", methods=["GET"])
    def get(req: Request):
        try:
            data = context(req.query_params)
        except ValueError as exc:
            return Response(str(exc), status_code=400)
        return page_layout("budget", *budget_page(data, saved=req.query_params.get("saved") == "1"))

    @rt("/budget/categories/{category_id}/edit", methods=["GET"])
    def edit(req: Request, category_id: int):
        try:
            data = context(req.query_params)
            budget_svc.validate_category(category_id)
            return page_layout("budget", *budget_edit(data, data["budgets"][category_id or None]))
        except ValueError as exc:
            return Response(str(exc), status_code=400)

    @rt("/budget/categories/{category_id}", methods=["POST"])
    async def save_category(req: Request, category_id: int):
        form = await req.form()
        try:
            data = context(form)
            period = str(form.get("period", ""))
            effective = str(form.get("effective_month", data["month"])) if period == "monthly" else data["month"]
            if effective[:4] != f"{data['year']:04d}":
                raise ValueError("effective month must be in the selected year")
            rollover = str(form.get("rollover", "false"))
            if rollover not in ("true", "false"):
                raise ValueError("invalid rollover setting")
            budget_svc.save_category(category_id, effective, period, str(form.get("amount", "")), rollover == "true")
        except ValueError as exc:
            return Response(str(exc), status_code=400)
        return RedirectResponse(context_url(data) + "&saved=1", status_code=303)

    @rt("/budget/limits", methods=["POST"])
    async def post_limits(req: Request):
        form = await req.form()
        month = str(form.get("month", ""))
        try:
            if not month:
                raise ValueError("budget month is required")
            limits = {int(key.removeprefix("limit_")): str(value) for key, value in form.items() if key.startswith("limit_")}
            budget_svc.save_limits(month, limits)
        except ValueError as exc:
            return Response(str(exc), status_code=400)
        return RedirectResponse("/budget?" + urlencode({"month": month, "saved": "1"}), status_code=303)
