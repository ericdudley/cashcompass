package service_test

import (
	"context"
	"fmt"
	"testing"

	"cashcompass-server/internal/model"
	"cashcompass-server/internal/service"
)

// MockTransactionRepository implements repository.TransactionRepository for unit tests.
type MockTransactionRepository struct {
	txns          []model.Transaction
	nextID        int
	syncAccLabels map[int]string
	syncCatLabels map[int]string
	listErr       error
	createErr     error
}

func newMockTxn(initial ...model.Transaction) *MockTransactionRepository {
	m := &MockTransactionRepository{
		nextID:        1,
		syncAccLabels: make(map[int]string),
		syncCatLabels: make(map[int]string),
	}
	m.txns = append(m.txns, initial...)
	if len(initial) > 0 {
		m.nextID = initial[len(initial)-1].ID + 1
	}
	return m
}

func (m *MockTransactionRepository) List(_ context.Context, _ model.TransactionFilter) ([]model.Transaction, error) {
	return m.txns, m.listErr
}

func (m *MockTransactionRepository) GetByID(_ context.Context, id int) (model.Transaction, error) {
	for _, t := range m.txns {
		if t.ID == id {
			return t, nil
		}
	}
	return model.Transaction{}, fmt.Errorf("transaction %d not found", id)
}

func (m *MockTransactionRepository) Create(_ context.Context, p model.CreateTransactionParams) (model.Transaction, error) {
	if m.createErr != nil {
		return model.Transaction{}, m.createErr
	}
	t := model.Transaction{
		ID: m.nextID, ISO8601: p.ISO8601, Date: p.Date, Amount: p.Amount,
		Label: p.Label, AccountID: p.AccountID, AccountLabel: p.AccountLabel,
		CategoryID: p.CategoryID, CategoryLabel: p.CategoryLabel,
	}
	m.nextID++
	m.txns = append(m.txns, t)
	return t, nil
}

func (m *MockTransactionRepository) UpdateAmount(_ context.Context, id int, amount int) error {
	for i, t := range m.txns {
		if t.ID == id {
			m.txns[i].Amount = amount
			return nil
		}
	}
	return fmt.Errorf("not found")
}

func (m *MockTransactionRepository) UpdateLabel(_ context.Context, id int, label string) error {
	for i, t := range m.txns {
		if t.ID == id {
			m.txns[i].Label = label
			return nil
		}
	}
	return fmt.Errorf("not found")
}

func (m *MockTransactionRepository) UpdateAccount(_ context.Context, id int, accountID *int, accountLabel string) error {
	for i, t := range m.txns {
		if t.ID == id {
			m.txns[i].AccountID = accountID
			m.txns[i].AccountLabel = accountLabel
			return nil
		}
	}
	return fmt.Errorf("not found")
}

func (m *MockTransactionRepository) UpdateCategory(_ context.Context, id int, categoryID *int, categoryLabel string) error {
	for i, t := range m.txns {
		if t.ID == id {
			m.txns[i].CategoryID = categoryID
			m.txns[i].CategoryLabel = categoryLabel
			return nil
		}
	}
	return fmt.Errorf("not found")
}

func (m *MockTransactionRepository) UpdateDate(_ context.Context, id int, iso8601, date string) error {
	for i, t := range m.txns {
		if t.ID == id {
			m.txns[i].ISO8601 = iso8601
			m.txns[i].Date = date
			return nil
		}
	}
	return fmt.Errorf("not found")
}

func (m *MockTransactionRepository) Delete(_ context.Context, id int) error {
	for i, t := range m.txns {
		if t.ID == id {
			m.txns = append(m.txns[:i], m.txns[i+1:]...)
			return nil
		}
	}
	return fmt.Errorf("not found")
}

func (m *MockTransactionRepository) SumByMonth(_ context.Context, _ model.AccountType, _, _ string) ([]model.MonthSum, error) {
	return nil, nil
}

func (m *MockTransactionRepository) BalancesByMonth(_ context.Context, _ []int) ([]model.AccountMonthBalance, error) {
	return nil, nil
}

func (m *MockTransactionRepository) SyncAccountLabel(_ context.Context, accountID int, label string) error {
	m.syncAccLabels[accountID] = label
	return nil
}

func (m *MockTransactionRepository) SyncCategoryLabel(_ context.Context, categoryID int, label string) error {
	m.syncCatLabels[categoryID] = label
	return nil
}

// --- TransactionService tests ---

func TestTxnService_List(t *testing.T) {
	mock := newMockTxn(
		model.Transaction{ID: 1, Amount: -100},
		model.Transaction{ID: 2, Amount: -200},
	)
	svc := service.NewTransactionService(mock)

	txns, err := svc.List(context.Background(), model.TransactionFilter{})
	if err != nil {
		t.Fatal(err)
	}
	if len(txns) != 2 {
		t.Errorf("expected 2, got %d", len(txns))
	}
}

func TestTxnService_Create(t *testing.T) {
	mock := newMockTxn()
	svc := service.NewTransactionService(mock)

	txn, err := svc.Create(context.Background(), model.CreateTransactionParams{
		ISO8601: "2026-03-01T00:00:00Z",
		Date:    "2026-03-01",
		Amount:  -500,
		Label:   "Bus fare",
	})
	if err != nil {
		t.Fatal(err)
	}
	if txn.Amount != -500 {
		t.Errorf("amount: got %d", txn.Amount)
	}
}

func TestTxnService_UpdateAmount(t *testing.T) {
	mock := newMockTxn(model.Transaction{ID: 1, Amount: -100})
	svc := service.NewTransactionService(mock)

	if err := svc.UpdateAmount(context.Background(), 1, -999); err != nil {
		t.Fatal(err)
	}
	if mock.txns[0].Amount != -999 {
		t.Errorf("amount: got %d", mock.txns[0].Amount)
	}
}

func TestTxnService_Delete(t *testing.T) {
	mock := newMockTxn(model.Transaction{ID: 1, Amount: -100})
	svc := service.NewTransactionService(mock)

	if err := svc.Delete(context.Background(), 1); err != nil {
		t.Fatal(err)
	}
	if len(mock.txns) != 0 {
		t.Errorf("expected 0 transactions, got %d", len(mock.txns))
	}
}

// --- AccountService sync tests using MockTransactionRepository ---

func TestAccountService_UpdateLabel_SyncsTransactions(t *testing.T) {
	accMock := newMock(model.Account{ID: 1, Label: "Old", AccountType: model.AccountTypeNetWorth})
	txnMock := newMockTxn()
	svc := service.NewAccountService(accMock, txnMock)

	if err := svc.UpdateLabel(context.Background(), 1, "New"); err != nil {
		t.Fatal(err)
	}
	if txnMock.syncAccLabels[1] != "New" {
		t.Errorf("sync account label: got %q, want %q", txnMock.syncAccLabels[1], "New")
	}
}

// --- CategoryService tests ---

func TestCategoryService_UpdateLabel_SyncsTransactions(t *testing.T) {
	catMock := &MockCategoryRepository{
		categories: []model.Category{{ID: 1, Label: "Old Cat"}},
	}
	txnMock := newMockTxn()
	svc := service.NewCategoryService(catMock, txnMock)

	if err := svc.UpdateLabel(context.Background(), 1, "New Cat"); err != nil {
		t.Fatal(err)
	}
	if txnMock.syncCatLabels[1] != "New Cat" {
		t.Errorf("sync category label: got %q, want %q", txnMock.syncCatLabels[1], "New Cat")
	}
}

func TestCategoryService_List(t *testing.T) {
	catMock := &MockCategoryRepository{
		categories: []model.Category{
			{ID: 1, Label: "Food"},
			{ID: 2, Label: "Transport"},
		},
	}
	svc := service.NewCategoryService(catMock, nil)

	cats, err := svc.List(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if len(cats) != 2 {
		t.Errorf("expected 2, got %d", len(cats))
	}
}

func TestCategoryService_Create(t *testing.T) {
	catMock := &MockCategoryRepository{}
	svc := service.NewCategoryService(catMock, nil)

	c, err := svc.Create(context.Background(), "Groceries")
	if err != nil {
		t.Fatal(err)
	}
	if c.Label != "Groceries" {
		t.Errorf("label: got %q", c.Label)
	}
}

func TestCategoryService_Delete(t *testing.T) {
	catMock := &MockCategoryRepository{
		categories: []model.Category{{ID: 1, Label: "Food"}},
	}
	svc := service.NewCategoryService(catMock, nil)

	if err := svc.Delete(context.Background(), 1); err != nil {
		t.Fatal(err)
	}
	if len(catMock.categories) != 0 {
		t.Errorf("expected 0 categories, got %d", len(catMock.categories))
	}
}

// MockCategoryRepository implements repository.CategoryRepository for unit tests.
type MockCategoryRepository struct {
	categories []model.Category
	nextID     int
	updateErr  error
}

func (m *MockCategoryRepository) List(_ context.Context) ([]model.Category, error) {
	return m.categories, nil
}

func (m *MockCategoryRepository) GetByID(_ context.Context, id int) (model.Category, error) {
	for _, c := range m.categories {
		if c.ID == id {
			return c, nil
		}
	}
	return model.Category{}, fmt.Errorf("category %d not found", id)
}

func (m *MockCategoryRepository) Create(_ context.Context, label string) (model.Category, error) {
	m.nextID++
	c := model.Category{ID: m.nextID, Label: label}
	m.categories = append(m.categories, c)
	return c, nil
}

func (m *MockCategoryRepository) UpdateLabel(_ context.Context, id int, label string) error {
	if m.updateErr != nil {
		return m.updateErr
	}
	for i, c := range m.categories {
		if c.ID == id {
			m.categories[i].Label = label
			return nil
		}
	}
	return fmt.Errorf("category %d not found", id)
}

func (m *MockCategoryRepository) Delete(_ context.Context, id int) error {
	for i, c := range m.categories {
		if c.ID == id {
			m.categories = append(m.categories[:i], m.categories[i+1:]...)
			return nil
		}
	}
	return fmt.Errorf("category %d not found", id)
}
