BEGIN;

CREATE TABLE budget_plans (
    year INTEGER NOT NULL CHECK(year BETWEEN 1 AND 9999),
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    period TEXT NOT NULL CHECK(period IN ('monthly', 'annual')),
    annual_amount_cents INTEGER CHECK(annual_amount_cents IS NULL OR annual_amount_cents >= 0),
    CHECK(period = 'annual' OR annual_amount_cents IS NULL)
);
CREATE UNIQUE INDEX idx_budget_plans_year_category
ON budget_plans(year, COALESCE(category_id, 0));

CREATE TABLE monthly_budget_rollover (
    month TEXT NOT NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    enabled INTEGER NOT NULL CHECK(enabled IN (0, 1))
);
CREATE UNIQUE INDEX idx_monthly_budget_rollover_month_category
ON monthly_budget_rollover(month, COALESCE(category_id, 0));

INSERT INTO budget_plans (year, category_id, period)
SELECT CAST(substr(MIN(month), 1, 4) AS INTEGER), category_id, 'monthly'
FROM monthly_budgets GROUP BY category_id;

INSERT INTO monthly_budget_rollover (month, category_id, enabled)
SELECT MIN(month), category_id, 1 FROM monthly_budgets GROUP BY category_id;

COMMIT;
