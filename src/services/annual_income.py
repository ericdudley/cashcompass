from __future__ import annotations

from src.models import AnnualIncome
from src.repository.annual_income import AnnualIncomeRepository


class AnnualIncomeService:
    def __init__(self, repo: AnnualIncomeRepository):
        self.repo = repo

    def list(self) -> list[AnnualIncome]:
        return self.repo.list()

    def get_by_id(self, id: int) -> AnnualIncome:
        return self.repo.get_by_id(id)

    def get_by_year(self, tax_year: int) -> AnnualIncome | None:
        return self.repo.get_by_year(tax_year)

    def create(
        self,
        tax_year: int,
        gross_income_cents: int,
        federal_tax_cents: int,
        state_tax_cents: int,
        notes: str = "",
    ) -> AnnualIncome:
        values = self._validate(
            tax_year,
            gross_income_cents,
            federal_tax_cents,
            state_tax_cents,
            notes,
        )
        if self.repo.get_by_year(tax_year) is not None:
            raise ValueError(f"annual income for {tax_year} already exists")
        return self.repo.create(*values)

    def update(
        self,
        id: int,
        tax_year: int,
        gross_income_cents: int,
        federal_tax_cents: int,
        state_tax_cents: int,
        notes: str = "",
    ) -> AnnualIncome:
        values = self._validate(
            tax_year,
            gross_income_cents,
            federal_tax_cents,
            state_tax_cents,
            notes,
        )
        self.repo.get_by_id(id)
        existing = self.repo.get_by_year(tax_year)
        if existing is not None and existing.id != id:
            raise ValueError(f"annual income for {tax_year} already exists")
        self.repo.update(id, *values)
        return self.repo.get_by_id(id)

    def delete(self, id: int):
        self.repo.get_by_id(id)
        self.repo.delete(id)

    @staticmethod
    def _validate(
        tax_year: int,
        gross_income_cents: int,
        federal_tax_cents: int,
        state_tax_cents: int,
        notes: str,
    ) -> tuple[int, int, int, int, str]:
        if isinstance(tax_year, bool) or not isinstance(tax_year, int) or not 1900 <= tax_year <= 9999:
            raise ValueError("tax year must be between 1900 and 9999")
        if gross_income_cents <= 0:
            raise ValueError("gross income must be greater than zero")
        if federal_tax_cents < 0 or state_tax_cents < 0:
            raise ValueError("tax amounts cannot be negative")
        if federal_tax_cents + state_tax_cents > gross_income_cents:
            raise ValueError("federal and state tax cannot exceed gross income")
        return (
            tax_year,
            gross_income_cents,
            federal_tax_cents,
            state_tax_cents,
            (notes or "").strip(),
        )
