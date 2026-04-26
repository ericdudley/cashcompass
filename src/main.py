import os
import logging

from fasthtml.common import *
from dotenv import load_dotenv
from starlette.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from src.db import Database, seed_if_empty
from src.repository.account import AccountRepository
from src.repository.category import CategoryRepository
from src.repository.transaction import TransactionRepository
from src.services.account import AccountService
from src.services.backup import BackupService
from src.services.category import CategoryService
from src.services.category_recommendation import build_category_recommendation_service
from src.services.reconciliation import ReconciliationService
from src.services.transaction import TransactionService

import src.routes.accounts as accounts_routes
import src.routes.categories as categories_routes
import src.routes.transactions as transactions_routes
import src.routes.dashboard as dashboard_routes
import src.routes.reconciliation as reconciliation_routes
import src.routes.settings as settings_routes
import src.routes.dev as dev_routes

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cashcompass")

DB_PATH = os.environ.get("CASHCOMPASS_DB_PATH", "./src/data/cashcompass.db")
MIGRATIONS_PATH = os.environ.get("CASHCOMPASS_MIGRATIONS_PATH", "./src/migrations")
PORT = int(os.environ.get("CASHCOMPASS_PORT", "8080"))
DEV_MODE = os.environ.get("CASHCOMPASS_DEV", "").lower() == "true"

app, rt = fast_app(
    pico=False,
    hdrs=(
        Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/daisyui@5", type="text/css"),
        Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/daisyui@5/themes.css", type="text/css"),
        Script(
            """
            (() => {
              const theme = localStorage.getItem("cashcompass-theme") || "abyss";
              document.documentElement.setAttribute("data-theme", theme);
            })();
            """
        ),
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Script(src="https://unpkg.com/htmx.org@1.9.12"),
        Link(rel="stylesheet", href="/static/app.css"),
    ),
)

# Mount static files
app.mount("/static", StaticFiles(directory="./static"), name="static")

# Init DB
db = Database(DB_PATH)
db.run_migrations(MIGRATIONS_PATH)
seed_if_empty(db)

# Wire up repositories and services
txn_repo = TransactionRepository(db)
acct_repo = AccountRepository(db)
cat_repo = CategoryRepository(db)

acct_svc = AccountService(acct_repo, txn_repo)
cat_svc = CategoryService(cat_repo, txn_repo)
txn_svc = TransactionService(txn_repo)
backup_svc = BackupService(db, acct_repo, cat_repo, txn_repo)
reconciliation_svc = ReconciliationService(acct_repo, txn_repo, txn_svc)
category_recommendation_svc = build_category_recommendation_service()

logger.info(
    "Anthropic category recommendations: %s",
    "enabled" if category_recommendation_svc.is_enabled else "disabled",
)

# Register routes
accounts_routes.register(rt, acct_svc)
reconciliation_routes.register(rt, reconciliation_svc)
categories_routes.register(rt, cat_svc)
transactions_routes.register(rt, txn_svc, acct_svc, cat_svc, category_recommendation_svc)
dashboard_routes.register(rt, acct_svc, cat_svc, txn_svc)
settings_routes.register(rt, acct_svc, cat_svc, txn_svc, backup_svc, DEV_MODE)
dev_routes.register(rt, db, DEV_MODE)


@rt("/", methods=["GET"])
def get():
    return RedirectResponse("/dashboard", status_code=302)


@rt("/healthz", methods=["GET"])
def get_healthz():
    return "ok"

def _prioritize_literal_route(path: str):
    routes = app.router.routes
    target_idx = next((i for i, route in enumerate(routes) if getattr(route, "path", None) == path), None)
    static_idx = next((i for i, route in enumerate(routes) if getattr(route, "path", None) == "/{fname:path}.{ext:static}"), None)
    if target_idx is None or static_idx is None or target_idx < static_idx:
        return
    routes.insert(static_idx, routes.pop(target_idx))


_prioritize_literal_route("/settings/export/transactions.csv")

serve(port=PORT)
