from __future__ import annotations
from fasthtml.common import *
from src.services.category import CategoryService
from src.components.categories import category_card, category_card_edit, categories_list, categories_page
from src.components.layout import page_layout


def register(rt, cat_svc: CategoryService):

    @rt("/categories", methods=["GET"])
    def get():
        return page_layout("categories", *categories_page(cat_svc.list()))

    @rt("/categories", methods=["POST"])
    async def post(req: Request):
        form = await req.form()
        label = form.get("label", "")
        try:
            cat_svc.create(label)
        except ValueError as exc:
            return Response(str(exc), status_code=400)
        return categories_list(cat_svc.list())

    @rt("/categories/{id}/label", methods=["PUT"])
    async def put_label(req: Request, id: int):
        form = await req.form()
        label = form.get("label", "")
        try:
            cat_svc.update_label(id, label)
        except ValueError as exc:
            return Response(str(exc), status_code=400)
        return category_card(cat_svc.get_by_id(id))

    @rt("/categories/{id}", methods=["DELETE"])
    def delete(id: int):
        cat_svc.delete(id)
        return ""

    @rt("/partials/categories", methods=["GET"])
    def get_list():
        return categories_list(cat_svc.list())

    @rt("/partials/categories/{id}", methods=["GET"])
    def get_card(id: int):
        return category_card(cat_svc.get_by_id(id))

    @rt("/partials/categories/{id}/edit", methods=["GET"])
    def get_card_edit(id: int):
        return category_card_edit(cat_svc.get_by_id(id))
