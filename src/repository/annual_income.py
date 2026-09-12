from __future__ import annotations

from src.db import Database
from src.models import AnnualIncome
from src.utils.ids import generate_uid


_COLS = """
    id,
    uid,
    tax_year,
    gross_income_cents,
    federal_tax_cents,
    state_tax_cents,
    notes,
    created_at,
    updated_at
"""


def _row_to_annual_income(row) -> AnnualIncome:
    return AnnualIncome(
        id=row["id"],
        uid=row["uid"],
        tax_year=row["tax_year"],
        gross_income_cents=row["gross_income_cents"],
        federal_tax_cents=row["federal_tax_cents"],
        state_tax_cents=row["state_tax_cents"],
        notes=row["notes"] or "",
        created_at=row["created_at"] or "",
        updated_at=row["updated_at"] or "",
    )


class AnnualIncomeRepository:
    def __init__(self, db: Database):
        self.db = db

    def list(self) -> list[AnnualIncome]:
        rows = self.db.execute(
            f"SELECT {_COLS} FROM annual_incomes ORDER BY tax_year DESC"
        ).fetchall()
        return [_row_to_annual_income(row) for row in rows]

    def get_by_id(self, id: int) -> AnnualIncome:
        row = self.db.execute(
            f"SELECT {_COLS} FROM annual_incomes WHERE id = ?", [id]
        ).fetchone()
        if row is None:
            raise ValueError(f"annual income {id} not found")
        return _row_to_annual_income(row)

    def get_by_year(self, tax_year: int) -> AnnualIncome | None:
        row = self.db.execute(
            f"SELECT {_COLS} FROM annual_incomes WHERE tax_year = ?", [tax_year]
        ).fetchone()
        return _row_to_annual_income(row) if row is not None else None

    def create(
        self,
        tax_year: int,
        gross_income_cents: int,
        federal_tax_cents: int,
        state_tax_cents: int,
        notes: str,
    ) -> AnnualIncome:
        cur = self.db.execute(
            """
            INSERT INTO annual_incomes (
                uid, tax_year, gross_income_cents, federal_tax_cents, state_tax_cents, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                generate_uid("inc"),
                tax_year,
                gross_income_cents,
                federal_tax_cents,
                state_tax_cents,
                notes,
            ],
        )
        self.db.commit()
        return self.get_by_id(cur.lastrowid)

    def update(
        self,
        id: int,
        tax_year: int,
        gross_income_cents: int,
        federal_tax_cents: int,
        state_tax_cents: int,
        notes: str,
    ):
        self.db.execute(
            """
            UPDATE annual_incomes
            SET tax_year = ?,
                gross_income_cents = ?,
                federal_tax_cents = ?,
                state_tax_cents = ?,
                notes = ?,
                updated_at = datetime('now')
            WHERE id = ?
            """,
            [tax_year, gross_income_cents, federal_tax_cents, state_tax_cents, notes, id],
        )
        self.db.commit()

    def delete(self, id: int):
        self.db.execute("DELETE FROM annual_incomes WHERE id = ?", [id])
        self.db.commit()
