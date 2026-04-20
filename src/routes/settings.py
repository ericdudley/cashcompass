from __future__ import annotations
from datetime import datetime, timezone
from urllib.parse import quote_plus

from fasthtml.common import *
from starlette.responses import RedirectResponse, Response as StarletteResponse

from src.services.account import AccountService
from src.services.backup import BackupService
from src.services.category import CategoryService
from src.services.transaction import TransactionService
from src.models import TransactionFilter
from src.components.settings import settings_page
from src.components.layout import page_layout

def register(rt, acct_svc: AccountService, cat_svc: CategoryService,
             txn_svc: TransactionService, backup_svc: BackupService, dev_mode: bool):

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

    @rt("/settings/import/backup", methods=["POST"])
    async def post_import_backup(req: Request):
        form = await req.form()
        file = form.get("file")
        if file is None:
            return RedirectResponse(f"/settings?error={quote_plus('no file uploaded')}", status_code=303)

        try:
            content = await file.read()
            payload = backup_svc.parse_backup_upload(content)
            backup_svc.restore_backup(payload)
        except ValueError as exc:
            return RedirectResponse(f"/settings?error={quote_plus(str(exc))}", status_code=303)
        except Exception as exc:
            return RedirectResponse(f"/settings?error={quote_plus(f'backup restore failed: {exc}')}", status_code=303)

        return RedirectResponse("/settings?imported=backup", status_code=303)

    @rt("/settings/export/backup", methods=["GET"])
    def get_export_backup():
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return StarletteResponse(
            backup_svc.export_backup_json(),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="cashcompass-backup-{today}.json"'},
        )

    @rt("/settings/export/transactions.csv", methods=["GET"])
    def get_export_transactions_csv():
        return StarletteResponse(
            backup_svc.export_transactions_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="transactions.csv"'},
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
