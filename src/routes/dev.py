from __future__ import annotations
from fasthtml.common import *
from src.db import Database, seed_if_empty


def register(rt, db: Database, dev_mode: bool):
    if not dev_mode:
        return

    @rt("/dev/reset", methods=["POST"])
    def post():
        db.execute("DELETE FROM transactions")
        db.execute("DELETE FROM categories")
        db.execute("DELETE FROM accounts")
        db.execute("DELETE FROM sqlite_sequence WHERE name IN ('transactions','categories','accounts')")
        db.commit()
        seed_if_empty(db)
        return "ok"
