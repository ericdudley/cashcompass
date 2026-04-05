package repository

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"cashcompass-server/internal/model"
)

type CategoryRepository interface {
	List(ctx context.Context) ([]model.Category, error)
	GetByID(ctx context.Context, id int) (model.Category, error)
	Create(ctx context.Context, label string) (model.Category, error)
	UpdateLabel(ctx context.Context, id int, label string) error
	Delete(ctx context.Context, id int) error
}

type SQLiteCategoryRepository struct {
	db *sql.DB
}

func NewSQLiteCategoryRepository(db *sql.DB) *SQLiteCategoryRepository {
	return &SQLiteCategoryRepository{db: db}
}

const categoryColumns = "id, label, created_at, updated_at"

func scanCategory(s rowScanner) (model.Category, error) {
	var c model.Category
	var createdAt, updatedAt string
	if err := s.Scan(&c.ID, &c.Label, &createdAt, &updatedAt); err != nil {
		return model.Category{}, err
	}
	c.CreatedAt, _ = time.Parse("2006-01-02 15:04:05", createdAt)
	c.UpdatedAt, _ = time.Parse("2006-01-02 15:04:05", updatedAt)
	return c, nil
}

func (r *SQLiteCategoryRepository) List(ctx context.Context) ([]model.Category, error) {
	rows, err := r.db.QueryContext(ctx,
		"SELECT "+categoryColumns+" FROM categories ORDER BY label ASC")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var categories []model.Category
	for rows.Next() {
		c, err := scanCategory(rows)
		if err != nil {
			return nil, err
		}
		categories = append(categories, c)
	}
	return categories, rows.Err()
}

func (r *SQLiteCategoryRepository) GetByID(ctx context.Context, id int) (model.Category, error) {
	row := r.db.QueryRowContext(ctx,
		"SELECT "+categoryColumns+" FROM categories WHERE id = ?", id)
	c, err := scanCategory(row)
	if err == sql.ErrNoRows {
		return model.Category{}, fmt.Errorf("category %d not found", id)
	}
	return c, err
}

func (r *SQLiteCategoryRepository) Create(ctx context.Context, label string) (model.Category, error) {
	res, err := r.db.ExecContext(ctx,
		"INSERT INTO categories (label) VALUES (?)", label)
	if err != nil {
		return model.Category{}, err
	}
	id, err := res.LastInsertId()
	if err != nil {
		return model.Category{}, err
	}
	return r.GetByID(ctx, int(id))
}

func (r *SQLiteCategoryRepository) UpdateLabel(ctx context.Context, id int, label string) error {
	_, err := r.db.ExecContext(ctx,
		"UPDATE categories SET label = ?, updated_at = datetime('now') WHERE id = ?", label, id)
	return err
}

func (r *SQLiteCategoryRepository) Delete(ctx context.Context, id int) error {
	_, err := r.db.ExecContext(ctx, "DELETE FROM categories WHERE id = ?", id)
	return err
}
