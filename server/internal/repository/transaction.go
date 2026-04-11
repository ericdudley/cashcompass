package repository

import (
	"context"
	"database/sql"
	"fmt"
	"strings"
	"time"

	"cashcompass-server/internal/model"
)

type TransactionRepository interface {
	List(ctx context.Context, filter model.TransactionFilter) ([]model.Transaction, error)
	GetByID(ctx context.Context, id int) (model.Transaction, error)
	Create(ctx context.Context, p model.CreateTransactionParams) (model.Transaction, error)
	UpdateAmount(ctx context.Context, id int, amount int) error
	UpdateLabel(ctx context.Context, id int, label string) error
	UpdateAccount(ctx context.Context, id int, accountID *int, accountLabel string) error
	UpdateCategory(ctx context.Context, id int, categoryID *int, categoryLabel string) error
	UpdateDate(ctx context.Context, id int, iso8601, date string) error
	Delete(ctx context.Context, id int) error
	SumByMonth(ctx context.Context, accountType model.AccountType, dateFrom, dateTo string) ([]model.MonthSum, error)
	BalancesByMonth(ctx context.Context, accountIDs []int) ([]model.AccountMonthBalance, error)
	// Sync helpers called by AccountService and CategoryService.
	SyncAccountLabel(ctx context.Context, accountID int, label string) error
	SyncCategoryLabel(ctx context.Context, categoryID int, label string) error
}

type SQLiteTransactionRepository struct {
	db *sql.DB
}

func NewSQLiteTransactionRepository(db *sql.DB) *SQLiteTransactionRepository {
	return &SQLiteTransactionRepository{db: db}
}

const txnColumns = "id, iso8601, yyyy_mm_dd, amount, label, account_id, account_label, category_id, category_label, created_at, updated_at"

func scanTransaction(s rowScanner) (model.Transaction, error) {
	var t model.Transaction
	var accountID, categoryID sql.NullInt64
	var createdAt, updatedAt string
	if err := s.Scan(
		&t.ID, &t.ISO8601, &t.Date, &t.Amount, &t.Label,
		&accountID, &t.AccountLabel,
		&categoryID, &t.CategoryLabel,
		&createdAt, &updatedAt,
	); err != nil {
		return model.Transaction{}, err
	}
	if accountID.Valid {
		id := int(accountID.Int64)
		t.AccountID = &id
	}
	if categoryID.Valid {
		id := int(categoryID.Int64)
		t.CategoryID = &id
	}
	t.CreatedAt, _ = time.Parse("2006-01-02 15:04:05", createdAt)
	t.UpdatedAt, _ = time.Parse("2006-01-02 15:04:05", updatedAt)
	return t, nil
}

func (r *SQLiteTransactionRepository) List(ctx context.Context, filter model.TransactionFilter) ([]model.Transaction, error) {
	query := "SELECT " + txnColumns + " FROM transactions WHERE 1=1"
	var args []any

	if filter.DateFrom != "" {
		query += " AND yyyy_mm_dd >= ?"
		args = append(args, filter.DateFrom)
	}
	if filter.DateTo != "" {
		query += " AND yyyy_mm_dd <= ?"
		args = append(args, filter.DateTo)
	}
	if filter.Label != "" {
		query += " AND label LIKE ?"
		args = append(args, "%"+filter.Label+"%")
	}
	if len(filter.AccountIDs) > 0 {
		query += " AND account_id IN (" + placeholders(len(filter.AccountIDs)) + ")"
		for _, id := range filter.AccountIDs {
			args = append(args, id)
		}
	}
	if len(filter.CategoryIDs) > 0 {
		query += " AND category_id IN (" + placeholders(len(filter.CategoryIDs)) + ")"
		for _, id := range filter.CategoryIDs {
			args = append(args, id)
		}
	}
	if filter.AccountType != "" {
		query += " AND account_id IN (SELECT id FROM accounts WHERE account_type = ?)"
		args = append(args, filter.AccountType)
	}
	query += " ORDER BY yyyy_mm_dd DESC, id DESC"

	rows, err := r.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var txns []model.Transaction
	for rows.Next() {
		t, err := scanTransaction(rows)
		if err != nil {
			return nil, err
		}
		txns = append(txns, t)
	}
	return txns, rows.Err()
}

func (r *SQLiteTransactionRepository) GetByID(ctx context.Context, id int) (model.Transaction, error) {
	row := r.db.QueryRowContext(ctx, "SELECT "+txnColumns+" FROM transactions WHERE id = ?", id)
	t, err := scanTransaction(row)
	if err == sql.ErrNoRows {
		return model.Transaction{}, fmt.Errorf("transaction %d not found", id)
	}
	return t, err
}

func (r *SQLiteTransactionRepository) Create(ctx context.Context, p model.CreateTransactionParams) (model.Transaction, error) {
	res, err := r.db.ExecContext(ctx, `
		INSERT INTO transactions (iso8601, yyyy_mm_dd, amount, label, account_id, account_label, category_id, category_label)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
		p.ISO8601, p.Date, p.Amount, p.Label,
		nullableInt(p.AccountID), p.AccountLabel,
		nullableInt(p.CategoryID), p.CategoryLabel,
	)
	if err != nil {
		return model.Transaction{}, err
	}
	id, err := res.LastInsertId()
	if err != nil {
		return model.Transaction{}, err
	}
	return r.GetByID(ctx, int(id))
}

func (r *SQLiteTransactionRepository) UpdateAmount(ctx context.Context, id int, amount int) error {
	_, err := r.db.ExecContext(ctx,
		"UPDATE transactions SET amount = ?, updated_at = datetime('now') WHERE id = ?", amount, id)
	return err
}

func (r *SQLiteTransactionRepository) UpdateLabel(ctx context.Context, id int, label string) error {
	_, err := r.db.ExecContext(ctx,
		"UPDATE transactions SET label = ?, updated_at = datetime('now') WHERE id = ?", label, id)
	return err
}

func (r *SQLiteTransactionRepository) UpdateAccount(ctx context.Context, id int, accountID *int, accountLabel string) error {
	_, err := r.db.ExecContext(ctx,
		"UPDATE transactions SET account_id = ?, account_label = ?, updated_at = datetime('now') WHERE id = ?",
		nullableInt(accountID), accountLabel, id)
	return err
}

func (r *SQLiteTransactionRepository) UpdateCategory(ctx context.Context, id int, categoryID *int, categoryLabel string) error {
	_, err := r.db.ExecContext(ctx,
		"UPDATE transactions SET category_id = ?, category_label = ?, updated_at = datetime('now') WHERE id = ?",
		nullableInt(categoryID), categoryLabel, id)
	return err
}

func (r *SQLiteTransactionRepository) UpdateDate(ctx context.Context, id int, iso8601, date string) error {
	_, err := r.db.ExecContext(ctx,
		"UPDATE transactions SET iso8601 = ?, yyyy_mm_dd = ?, updated_at = datetime('now') WHERE id = ?",
		iso8601, date, id)
	return err
}

func (r *SQLiteTransactionRepository) Delete(ctx context.Context, id int) error {
	_, err := r.db.ExecContext(ctx, "DELETE FROM transactions WHERE id = ?", id)
	return err
}

func (r *SQLiteTransactionRepository) SumByMonth(ctx context.Context, accountType model.AccountType, dateFrom, dateTo string) ([]model.MonthSum, error) {
	query := `
		SELECT replace(substr(t.yyyy_mm_dd, 1, 7), '_', '-') AS month, SUM(t.amount) AS total
		FROM transactions t
		JOIN accounts a ON t.account_id = a.id
		WHERE a.account_type = ?`
	args := []any{accountType}

	if dateFrom != "" {
		query += " AND t.yyyy_mm_dd >= ?"
		args = append(args, dateFrom)
	}
	if dateTo != "" {
		query += " AND t.yyyy_mm_dd <= ?"
		args = append(args, dateTo)
	}
	query += " GROUP BY month ORDER BY month DESC"

	rows, err := r.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var sums []model.MonthSum
	for rows.Next() {
		var s model.MonthSum
		if err := rows.Scan(&s.Month, &s.Amount); err != nil {
			return nil, err
		}
		sums = append(sums, s)
	}
	return sums, rows.Err()
}

func (r *SQLiteTransactionRepository) BalancesByMonth(ctx context.Context, accountIDs []int) ([]model.AccountMonthBalance, error) {
	if len(accountIDs) == 0 {
		return nil, nil
	}

	query := `
		SELECT account_id, account_label, replace(substr(yyyy_mm_dd, 1, 7), '_', '-') AS month, SUM(amount) AS monthly_sum
		FROM transactions
		WHERE account_id IN (` + placeholders(len(accountIDs)) + `)
		GROUP BY account_id, month
		ORDER BY account_id, month`

	args := make([]any, len(accountIDs))
	for i, id := range accountIDs {
		args[i] = id
	}

	rows, err := r.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	// Collect monthly sums, then compute cumulative per account.
	type row struct {
		accountID    int
		accountLabel string
		month        string
		monthlySum   int
	}
	var rawRows []row
	for rows.Next() {
		var rw row
		if err := rows.Scan(&rw.accountID, &rw.accountLabel, &rw.month, &rw.monthlySum); err != nil {
			return nil, err
		}
		rawRows = append(rawRows, rw)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}

	cumulative := make(map[int]int)
	var result []model.AccountMonthBalance
	for _, rw := range rawRows {
		cumulative[rw.accountID] += rw.monthlySum
		result = append(result, model.AccountMonthBalance{
			AccountID:    rw.accountID,
			AccountLabel: rw.accountLabel,
			Month:        rw.month,
			Balance:      cumulative[rw.accountID],
		})
	}
	return result, nil
}

func (r *SQLiteTransactionRepository) SyncAccountLabel(ctx context.Context, accountID int, label string) error {
	_, err := r.db.ExecContext(ctx,
		"UPDATE transactions SET account_label = ?, updated_at = datetime('now') WHERE account_id = ?",
		label, accountID)
	return err
}

func (r *SQLiteTransactionRepository) SyncCategoryLabel(ctx context.Context, categoryID int, label string) error {
	_, err := r.db.ExecContext(ctx,
		"UPDATE transactions SET category_label = ?, updated_at = datetime('now') WHERE category_id = ?",
		label, categoryID)
	return err
}

// placeholders returns a comma-separated string of n "?" placeholders.
func placeholders(n int) string {
	p := make([]string, n)
	for i := range p {
		p[i] = "?"
	}
	return strings.Join(p, ", ")
}

// nullableInt converts *int to a value suitable for a nullable SQL column.
func nullableInt(v *int) any {
	if v == nil {
		return nil
	}
	return *v
}
