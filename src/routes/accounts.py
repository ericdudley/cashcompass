from __future__ import annotations
from fasthtml.common import *
from src.services.account import AccountService
from src.components.accounts import account_card, account_card_edit, accounts_list, accounts_page
from src.components.layout import page_layout


def _split(accts):
    active = [a for a in accts if not a.is_archived]
    archived = [a for a in accts if a.is_archived]
    return active, archived


def register(rt, acct_svc: AccountService):

    @rt("/accounts", methods=["GET"])
    def get(req: Request):
        active, archived = _split(acct_svc.list())
        return page_layout("accounts", *accounts_page(active, archived))

    @rt("/accounts", methods=["POST"])
    async def post(req: Request):
        form = await req.form()
        label = form.get("label", "")
        account_type = form.get("account_type", "net_worth")
        if account_type not in ("net_worth", "expenses"):
            account_type = "net_worth"
        try:
            acct_svc.create(label, account_type)
        except ValueError as exc:
            return Response(str(exc), status_code=400)
        active, archived = _split(acct_svc.list())
        return accounts_list(active, archived)

    @rt("/accounts/{id}/label", methods=["PUT"])
    async def put_label(req: Request, id: int):
        form = await req.form()
        label = form.get("label", "")
        try:
            acct_svc.update_label(id, label)
        except ValueError as exc:
            return Response(str(exc), status_code=400)
        return account_card(acct_svc.get_by_id(id))

    @rt("/accounts/{id}/type", methods=["PUT"])
    async def put_type(req: Request, id: int):
        form = await req.form()
        account_type = form.get("account_type", "net_worth")
        if account_type not in ("net_worth", "expenses"):
            account_type = "net_worth"
        acct_svc.update_type(id, account_type)
        return account_card(acct_svc.get_by_id(id))

    @rt("/accounts/{id}/archive", methods=["PUT"])
    def put_archive(id: int):
        acct_svc.toggle_archived(id)
        active, archived = _split(acct_svc.list())
        return accounts_list(active, archived)

    @rt("/accounts/{id}", methods=["DELETE"])
    def delete(id: int):
        acct_svc.delete(id)
        return ""

    @rt("/partials/accounts", methods=["GET"])
    def get_list():
        active, archived = _split(acct_svc.list())
        return accounts_list(active, archived)

    @rt("/partials/accounts/{id}", methods=["GET"])
    def get_card(id: int):
        return account_card(acct_svc.get_by_id(id))

    @rt("/partials/accounts/{id}/edit", methods=["GET"])
    def get_card_edit(id: int):
        return account_card_edit(acct_svc.get_by_id(id))
