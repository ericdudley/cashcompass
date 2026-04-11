package service_test

import (
	"context"
	"fmt"
	"testing"

	"cashcompass-server/internal/model"
	"cashcompass-server/internal/service"
)

// MockAccountRepository implements repository.AccountRepository for unit tests.
type MockAccountRepository struct {
	accounts []model.Account
	nextID   int
	// injectable errors
	listErr    error
	getErr     error
	createErr  error
	updateErr  error
	archiveErr error
	deleteErr  error
}

func newMock(initial ...model.Account) *MockAccountRepository {
	m := &MockAccountRepository{nextID: 1}
	m.accounts = append(m.accounts, initial...)
	if len(initial) > 0 {
		m.nextID = initial[len(initial)-1].ID + 1
	}
	return m
}

func (m *MockAccountRepository) List(_ context.Context) ([]model.Account, error) {
	return m.accounts, m.listErr
}

func (m *MockAccountRepository) GetByID(_ context.Context, id int) (model.Account, error) {
	if m.getErr != nil {
		return model.Account{}, m.getErr
	}
	for _, a := range m.accounts {
		if a.ID == id {
			return a, nil
		}
	}
	return model.Account{}, fmt.Errorf("account %d not found", id)
}

func (m *MockAccountRepository) Create(_ context.Context, label string, accountType model.AccountType) (model.Account, error) {
	if m.createErr != nil {
		return model.Account{}, m.createErr
	}
	a := model.Account{ID: m.nextID, Label: label, AccountType: accountType}
	m.nextID++
	m.accounts = append(m.accounts, a)
	return a, nil
}

func (m *MockAccountRepository) UpdateLabel(_ context.Context, id int, label string) error {
	if m.updateErr != nil {
		return m.updateErr
	}
	for i, a := range m.accounts {
		if a.ID == id {
			m.accounts[i].Label = label
			return nil
		}
	}
	return fmt.Errorf("account %d not found", id)
}

func (m *MockAccountRepository) UpdateType(_ context.Context, id int, accountType model.AccountType) error {
	if m.updateErr != nil {
		return m.updateErr
	}
	for i, a := range m.accounts {
		if a.ID == id {
			m.accounts[i].AccountType = accountType
			return nil
		}
	}
	return fmt.Errorf("account %d not found", id)
}

func (m *MockAccountRepository) SetArchived(_ context.Context, id int, archived bool) error {
	if m.archiveErr != nil {
		return m.archiveErr
	}
	for i, a := range m.accounts {
		if a.ID == id {
			m.accounts[i].IsArchived = archived
			return nil
		}
	}
	return fmt.Errorf("account %d not found", id)
}

func (m *MockAccountRepository) Delete(_ context.Context, id int) error {
	if m.deleteErr != nil {
		return m.deleteErr
	}
	for i, a := range m.accounts {
		if a.ID == id {
			m.accounts = append(m.accounts[:i], m.accounts[i+1:]...)
			return nil
		}
	}
	return fmt.Errorf("account %d not found", id)
}

func TestService_List(t *testing.T) {
	mock := newMock(
		model.Account{ID: 1, Label: "A", AccountType: model.AccountTypeNetWorth},
		model.Account{ID: 2, Label: "B", AccountType: model.AccountTypeExpenses},
	)
	svc := service.NewAccountService(mock, nil)

	accounts, err := svc.List(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if len(accounts) != 2 {
		t.Errorf("expected 2, got %d", len(accounts))
	}
}

func TestService_List_PropagatesError(t *testing.T) {
	mock := newMock()
	mock.listErr = fmt.Errorf("db error")
	svc := service.NewAccountService(mock, nil)

	_, err := svc.List(context.Background())
	if err == nil {
		t.Error("expected error, got nil")
	}
}

func TestService_Create(t *testing.T) {
	mock := newMock()
	svc := service.NewAccountService(mock, nil)

	a, err := svc.Create(context.Background(), "Checking", model.AccountTypeNetWorth)
	if err != nil {
		t.Fatal(err)
	}
	if a.Label != "Checking" {
		t.Errorf("label: got %q, want %q", a.Label, "Checking")
	}
}

func TestService_UpdateLabel(t *testing.T) {
	mock := newMock(model.Account{ID: 1, Label: "Old", AccountType: model.AccountTypeNetWorth})
	svc := service.NewAccountService(mock, nil)

	if err := svc.UpdateLabel(context.Background(), 1, "New"); err != nil {
		t.Fatal(err)
	}
	if mock.accounts[0].Label != "New" {
		t.Errorf("label: got %q, want %q", mock.accounts[0].Label, "New")
	}
}

func TestService_UpdateType(t *testing.T) {
	mock := newMock(model.Account{ID: 1, Label: "A", AccountType: model.AccountTypeNetWorth})
	svc := service.NewAccountService(mock, nil)

	if err := svc.UpdateType(context.Background(), 1, model.AccountTypeExpenses); err != nil {
		t.Fatal(err)
	}
	if mock.accounts[0].AccountType != model.AccountTypeExpenses {
		t.Errorf("type: got %q, want %q", mock.accounts[0].AccountType, model.AccountTypeExpenses)
	}
}

func TestService_ToggleArchived_Archives(t *testing.T) {
	mock := newMock(model.Account{ID: 1, Label: "A", AccountType: model.AccountTypeNetWorth, IsArchived: false})
	svc := service.NewAccountService(mock, nil)

	a, err := svc.ToggleArchived(context.Background(), 1)
	if err != nil {
		t.Fatal(err)
	}
	if !a.IsArchived {
		t.Error("expected IsArchived=true after toggle")
	}
}

func TestService_ToggleArchived_Unarchives(t *testing.T) {
	mock := newMock(model.Account{ID: 1, Label: "A", AccountType: model.AccountTypeNetWorth, IsArchived: true})
	svc := service.NewAccountService(mock, nil)

	a, err := svc.ToggleArchived(context.Background(), 1)
	if err != nil {
		t.Fatal(err)
	}
	if a.IsArchived {
		t.Error("expected IsArchived=false after toggle")
	}
}

func TestService_ToggleArchived_NotFound(t *testing.T) {
	mock := newMock()
	svc := service.NewAccountService(mock, nil)

	_, err := svc.ToggleArchived(context.Background(), 999)
	if err == nil {
		t.Error("expected error for missing account, got nil")
	}
}

func TestService_Delete(t *testing.T) {
	mock := newMock(model.Account{ID: 1, Label: "A", AccountType: model.AccountTypeNetWorth})
	svc := service.NewAccountService(mock, nil)

	if err := svc.Delete(context.Background(), 1); err != nil {
		t.Fatal(err)
	}
	if len(mock.accounts) != 0 {
		t.Errorf("expected 0 accounts after delete, got %d", len(mock.accounts))
	}
}

func TestService_Delete_PropagatesError(t *testing.T) {
	mock := newMock()
	mock.deleteErr = fmt.Errorf("db error")
	svc := service.NewAccountService(mock, nil)

	err := svc.Delete(context.Background(), 1)
	if err == nil {
		t.Error("expected error, got nil")
	}
}
