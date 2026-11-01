CREATE TABLE IF NOT EXISTS monthly_budgets (
    month TEXT NOT NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    amount_cents INTEGER NOT NULL CHECK(amount_cents >= 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_monthly_budgets_month_category
ON monthly_budgets(month, COALESCE(category_id, 0));
