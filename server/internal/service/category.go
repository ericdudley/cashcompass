package service

import (
	"context"

	"cashcompass-server/internal/model"
	"cashcompass-server/internal/repository"
)

type CategoryService interface {
	List(ctx context.Context) ([]model.Category, error)
	GetByID(ctx context.Context, id int) (model.Category, error)
	Create(ctx context.Context, label string) (model.Category, error)
	UpdateLabel(ctx context.Context, id int, label string) error
	Delete(ctx context.Context, id int) error
}

type CategoryServiceImpl struct {
	categories   repository.CategoryRepository
	transactions repository.TransactionRepository
}

func NewCategoryService(categories repository.CategoryRepository, transactions repository.TransactionRepository) *CategoryServiceImpl {
	return &CategoryServiceImpl{categories: categories, transactions: transactions}
}

func (s *CategoryServiceImpl) List(ctx context.Context) ([]model.Category, error) {
	return s.categories.List(ctx)
}

func (s *CategoryServiceImpl) GetByID(ctx context.Context, id int) (model.Category, error) {
	return s.categories.GetByID(ctx, id)
}

func (s *CategoryServiceImpl) Create(ctx context.Context, label string) (model.Category, error) {
	return s.categories.Create(ctx, label)
}

func (s *CategoryServiceImpl) UpdateLabel(ctx context.Context, id int, label string) error {
	if err := s.categories.UpdateLabel(ctx, id, label); err != nil {
		return err
	}
	if s.transactions != nil {
		return s.transactions.SyncCategoryLabel(ctx, id, label)
	}
	return nil
}

func (s *CategoryServiceImpl) Delete(ctx context.Context, id int) error {
	return s.categories.Delete(ctx, id)
}
