from fasthtml.common import *
from starlette.responses import RedirectResponse
from urllib.parse import urlencode

from src.components.budget import budget_page
from src.components.layout import page_layout
from src.services.budget import BudgetService


def register(rt, budget_svc: BudgetService):
    @rt("/budget", methods=["GET"])
    def get(req: Request):
        try:
            data = budget_svc.build(req.query_params.get("month", ""))
        except ValueError as exc:
            return Response(str(exc), status_code=400)
        return page_layout("budget", *budget_page(data, saved=req.query_params.get("saved") == "1"))

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
