BEGIN;

CREATE TABLE recurring_budgets (
    month TEXT NOT NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    amount_cents INTEGER CHECK(amount_cents IS NULL OR amount_cents >= 0)
);

INSERT INTO recurring_budgets (month, category_id, amount_cents)
SELECT month, category_id, amount_cents FROM monthly_budgets;

DROP TABLE monthly_budgets;
ALTER TABLE recurring_budgets RENAME TO monthly_budgets;

CREATE UNIQUE INDEX idx_monthly_budgets_month_category
ON monthly_budgets(month, COALESCE(category_id, 0));

COMMIT;
