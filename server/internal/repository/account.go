package repository

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"cashcompass-server/internal/model"
)

type AccountRepository interface {
	List(ctx context.Context) ([]model.Account, error)
	GetByID(ctx context.Context, id int) (model.Account, error)
	Create(ctx context.Context, label string, accountType model.AccountType) (model.Account, error)
	UpdateLabel(ctx context.Context, id int, label string) error
	UpdateType(ctx context.Context, id int, accountType model.AccountType) error
	SetArchived(ctx context.Context, id int, archived bool) error
	Delete(ctx context.Context, id int) error
}

type SQLiteAccountRepository struct {
	db *sql.DB
}

func NewSQLiteAccountRepository(db *sql.DB) *SQLiteAccountRepository {
	return &SQLiteAccountRepository{db: db}
}

type rowScanner interface {
	Scan(dest ...any) error
}

const accountColumns = "id, label, account_type, is_archived, created_at, updated_at"

func scanAccount(s rowScanner) (model.Account, error) {
	var a model.Account
	var isArchived int
	var createdAt, updatedAt string
	var accountTypeStr string
	if err := s.Scan(&a.ID, &a.Label, &accountTypeStr, &isArchived, &createdAt, &updatedAt); err != nil {
		return model.Account{}, err
	}
	a.AccountType = model.AccountType(accountTypeStr)
	a.IsArchived = isArchived == 1
	a.CreatedAt, _ = time.Parse("2006-01-02 15:04:05", createdAt)
	a.UpdatedAt, _ = time.Parse("2006-01-02 15:04:05", updatedAt)
	return a, nil
}

func (r *SQLiteAccountRepository) List(ctx context.Context) ([]model.Account, error) {
	rows, err := r.db.QueryContext(ctx,
		"SELECT "+accountColumns+" FROM accounts ORDER BY is_archived ASC, label ASC")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var accounts []model.Account
	for rows.Next() {
		a, err := scanAccount(rows)
		if err != nil {
			return nil, err
		}
		accounts = append(accounts, a)
	}
	return accounts, rows.Err()
}

func (r *SQLiteAccountRepository) GetByID(ctx context.Context, id int) (model.Account, error) {
	row := r.db.QueryRowContext(ctx,
		"SELECT "+accountColumns+" FROM accounts WHERE id = ?", id)
	a, err := scanAccount(row)
	if err == sql.ErrNoRows {
		return model.Account{}, fmt.Errorf("account %d not found", id)
	}
	return a, err
}

func (r *SQLiteAccountRepository) Create(ctx context.Context, label string, accountType model.AccountType) (model.Account, error) {
	res, err := r.db.ExecContext(ctx,
		"INSERT INTO accounts (label, account_type) VALUES (?, ?)", label, accountType)
	if err != nil {
		return model.Account{}, err
	}
	id, err := res.LastInsertId()
	if err != nil {
		return model.Account{}, err
	}
	return r.GetByID(ctx, int(id))
}

func (r *SQLiteAccountRepository) UpdateLabel(ctx context.Context, id int, label string) error {
	_, err := r.db.ExecContext(ctx,
		"UPDATE accounts SET label = ?, updated_at = datetime('now') WHERE id = ?", label, id)
	return err
}

func (r *SQLiteAccountRepository) UpdateType(ctx context.Context, id int, accountType model.AccountType) error {
	_, err := r.db.ExecContext(ctx,
		"UPDATE accounts SET account_type = ?, updated_at = datetime('now') WHERE id = ?", accountType, id)
	return err
}

func (r *SQLiteAccountRepository) SetArchived(ctx context.Context, id int, archived bool) error {
	v := 0
	if archived {
		v = 1
	}
	_, err := r.db.ExecContext(ctx,
		"UPDATE accounts SET is_archived = ?, updated_at = datetime('now') WHERE id = ?", v, id)
	return err
}

func (r *SQLiteAccountRepository) Delete(ctx context.Context, id int) error {
	_, err := r.db.ExecContext(ctx, "DELETE FROM accounts WHERE id = ?", id)
	return err
}
