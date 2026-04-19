import os

from fasthtml.common import *
from starlette.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from src.db import Database, seed_if_empty
from src.repository.account import AccountRepository
from src.repository.category import CategoryRepository
from src.repository.transaction import TransactionRepository
from src.services.account import AccountService
from src.services.category import CategoryService
from src.services.transaction import TransactionService

import src.routes.accounts as accounts_routes
import src.routes.categories as categories_routes
import src.routes.transactions as transactions_routes
import src.routes.dashboard as dashboard_routes
import src.routes.settings as settings_routes
import src.routes.dev as dev_routes

DB_PATH = os.environ.get("CASHCOMPASS_DB_PATH", "./src/data/cashcompass.db")
MIGRATIONS_PATH = os.environ.get("CASHCOMPASS_MIGRATIONS_PATH", "./src/migrations")
PORT = int(os.environ.get("CASHCOMPASS_PORT", "8080"))
DEV_MODE = os.environ.get("CASHCOMPASS_DEV", "").lower() == "true"

app, rt = fast_app(
    pico=False,
    hdrs=(
        Script(src="https://cdn.tailwindcss.com"),
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

# Register routes
accounts_routes.register(rt, acct_svc)
categories_routes.register(rt, cat_svc)
transactions_routes.register(rt, txn_svc, acct_svc, cat_svc)
dashboard_routes.register(rt, acct_svc, cat_svc, txn_svc)
settings_routes.register(rt, acct_svc, cat_svc, txn_svc, DEV_MODE)
dev_routes.register(rt, db, DEV_MODE)


@rt("/", methods=["GET"])
def get():
    return RedirectResponse("/dashboard", status_code=302)


@rt("/healthz", methods=["GET"])
def get_healthz():
    return "ok"


serve(port=PORT)
