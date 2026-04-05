package service

import (
	"context"

	"cashcompass-server/internal/model"
	"cashcompass-server/internal/repository"
)

type TransactionService interface {
	List(ctx context.Context, filter model.TransactionFilter) ([]model.Transaction, error)
	GetByID(ctx context.Context, id int) (model.Transaction, error)
	Create(ctx context.Context, p model.CreateTransactionParams) (model.Transaction, error)
	UpdateAmount(ctx context.Context, id int, amount int) error
	UpdateLabel(ctx context.Context, id int, label string) error
	UpdateAccount(ctx context.Context, id int, accountID *int, accountLabel string) error
	UpdateCategory(ctx context.Context, id int, categoryID *int, categoryLabel string) error
	UpdateDate(ctx context.Context, id int, iso8601, date string) error
	Delete(ctx context.Context, id int) error
	SumByMonth(ctx context.Context, accountType, dateFrom, dateTo string) ([]model.MonthSum, error)
	BalancesByMonth(ctx context.Context, accountIDs []int) ([]model.AccountMonthBalance, error)
}

type TransactionServiceImpl struct {
	transactions repository.TransactionRepository
}

func NewTransactionService(repo repository.TransactionRepository) *TransactionServiceImpl {
	return &TransactionServiceImpl{transactions: repo}
}

func (s *TransactionServiceImpl) List(ctx context.Context, filter model.TransactionFilter) ([]model.Transaction, error) {
	return s.transactions.List(ctx, filter)
}

func (s *TransactionServiceImpl) GetByID(ctx context.Context, id int) (model.Transaction, error) {
	return s.transactions.GetByID(ctx, id)
}

func (s *TransactionServiceImpl) Create(ctx context.Context, p model.CreateTransactionParams) (model.Transaction, error) {
	return s.transactions.Create(ctx, p)
}

func (s *TransactionServiceImpl) UpdateAmount(ctx context.Context, id int, amount int) error {
	return s.transactions.UpdateAmount(ctx, id, amount)
}

func (s *TransactionServiceImpl) UpdateLabel(ctx context.Context, id int, label string) error {
	return s.transactions.UpdateLabel(ctx, id, label)
}

func (s *TransactionServiceImpl) UpdateAccount(ctx context.Context, id int, accountID *int, accountLabel string) error {
	return s.transactions.UpdateAccount(ctx, id, accountID, accountLabel)
}

func (s *TransactionServiceImpl) UpdateCategory(ctx context.Context, id int, categoryID *int, categoryLabel string) error {
	return s.transactions.UpdateCategory(ctx, id, categoryID, categoryLabel)
}

func (s *TransactionServiceImpl) UpdateDate(ctx context.Context, id int, iso8601, date string) error {
	return s.transactions.UpdateDate(ctx, id, iso8601, date)
}

func (s *TransactionServiceImpl) Delete(ctx context.Context, id int) error {
	return s.transactions.Delete(ctx, id)
}

func (s *TransactionServiceImpl) SumByMonth(ctx context.Context, accountType, dateFrom, dateTo string) ([]model.MonthSum, error) {
	return s.transactions.SumByMonth(ctx, accountType, dateFrom, dateTo)
}

func (s *TransactionServiceImpl) BalancesByMonth(ctx context.Context, accountIDs []int) ([]model.AccountMonthBalance, error) {
	return s.transactions.BalancesByMonth(ctx, accountIDs)
}
