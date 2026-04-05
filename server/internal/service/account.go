package service

import (
	"context"

	"cashcompass-server/internal/model"
	"cashcompass-server/internal/repository"
)

type AccountService interface {
	List(ctx context.Context) ([]model.Account, error)
	GetByID(ctx context.Context, id int) (model.Account, error)
	Create(ctx context.Context, label, accountType string) (model.Account, error)
	UpdateLabel(ctx context.Context, id int, label string) error
	UpdateType(ctx context.Context, id int, accountType string) error
	ToggleArchived(ctx context.Context, id int) (model.Account, error)
	Delete(ctx context.Context, id int) error
}

type AccountServiceImpl struct {
	accounts     repository.AccountRepository
	transactions repository.TransactionRepository
}

func NewAccountService(accounts repository.AccountRepository, transactions repository.TransactionRepository) *AccountServiceImpl {
	return &AccountServiceImpl{accounts: accounts, transactions: transactions}
}

func (s *AccountServiceImpl) List(ctx context.Context) ([]model.Account, error) {
	return s.accounts.List(ctx)
}

func (s *AccountServiceImpl) GetByID(ctx context.Context, id int) (model.Account, error) {
	return s.accounts.GetByID(ctx, id)
}

func (s *AccountServiceImpl) Create(ctx context.Context, label, accountType string) (model.Account, error) {
	return s.accounts.Create(ctx, label, accountType)
}

func (s *AccountServiceImpl) UpdateLabel(ctx context.Context, id int, label string) error {
	if err := s.accounts.UpdateLabel(ctx, id, label); err != nil {
		return err
	}
	if s.transactions != nil {
		return s.transactions.SyncAccountLabel(ctx, id, label)
	}
	return nil
}

func (s *AccountServiceImpl) UpdateType(ctx context.Context, id int, accountType string) error {
	return s.accounts.UpdateType(ctx, id, accountType)
}

func (s *AccountServiceImpl) ToggleArchived(ctx context.Context, id int) (model.Account, error) {
	a, err := s.accounts.GetByID(ctx, id)
	if err != nil {
		return model.Account{}, err
	}
	if err := s.accounts.SetArchived(ctx, id, !a.IsArchived); err != nil {
		return model.Account{}, err
	}
	return s.accounts.GetByID(ctx, id)
}

func (s *AccountServiceImpl) Delete(ctx context.Context, id int) error {
	return s.accounts.Delete(ctx, id)
}
