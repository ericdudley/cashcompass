package repository_test

import (
	"context"
	"database/sql"
	"testing"

	"cashcompass-server/internal/db"
	"cashcompass-server/internal/repository"
)

func setupTestDB(t *testing.T) *sql.DB {
	t.Helper()
	sqlDB, err := db.Open(":memory:")
	if err != nil {
		t.Fatalf("open db: %v", err)
	}
	if _, err := db.Migrate(sqlDB); err != nil {
		t.Fatalf("migrate: %v", err)
	}
	t.Cleanup(func() { sqlDB.Close() })
	return sqlDB
}

func TestList_Empty(t *testing.T) {
	repo := repository.NewSQLiteAccountRepository(setupTestDB(t))
	accounts, err := repo.List(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if len(accounts) != 0 {
		t.Errorf("expected 0 accounts, got %d", len(accounts))
	}
}

func TestCreate_And_List(t *testing.T) {
	repo := repository.NewSQLiteAccountRepository(setupTestDB(t))
	ctx := context.Background()

	a, err := repo.Create(ctx, "Checking", "net_worth")
	if err != nil {
		t.Fatal(err)
	}
	if a.ID == 0 {
		t.Error("expected non-zero ID after create")
	}
	if a.Label != "Checking" {
		t.Errorf("label: got %q, want %q", a.Label, "Checking")
	}
	if a.AccountType != "net_worth" {
		t.Errorf("account_type: got %q, want %q", a.AccountType, "net_worth")
	}

	accounts, err := repo.List(ctx)
	if err != nil {
		t.Fatal(err)
	}
	if len(accounts) != 1 {
		t.Errorf("expected 1 account, got %d", len(accounts))
	}
}

func TestCreate_InvalidType(t *testing.T) {
	repo := repository.NewSQLiteAccountRepository(setupTestDB(t))
	_, err := repo.Create(context.Background(), "X", "invalid_type")
	if err == nil {
		t.Error("expected error for invalid account_type, got nil")
	}
}

func TestGetByID_Found(t *testing.T) {
	repo := repository.NewSQLiteAccountRepository(setupTestDB(t))
	ctx := context.Background()

	created, _ := repo.Create(ctx, "Savings", "net_worth")
	got, err := repo.GetByID(ctx, created.ID)
	if err != nil {
		t.Fatal(err)
	}
	if got.Label != "Savings" {
		t.Errorf("label: got %q, want %q", got.Label, "Savings")
	}
}

func TestGetByID_NotFound(t *testing.T) {
	repo := repository.NewSQLiteAccountRepository(setupTestDB(t))
	_, err := repo.GetByID(context.Background(), 9999)
	if err == nil {
		t.Error("expected error for missing account, got nil")
	}
}

func TestUpdateLabel(t *testing.T) {
	repo := repository.NewSQLiteAccountRepository(setupTestDB(t))
	ctx := context.Background()

	a, _ := repo.Create(ctx, "Old", "net_worth")
	if err := repo.UpdateLabel(ctx, a.ID, "New"); err != nil {
		t.Fatal(err)
	}
	got, _ := repo.GetByID(ctx, a.ID)
	if got.Label != "New" {
		t.Errorf("label: got %q, want %q", got.Label, "New")
	}
}

func TestUpdateType(t *testing.T) {
	repo := repository.NewSQLiteAccountRepository(setupTestDB(t))
	ctx := context.Background()

	a, _ := repo.Create(ctx, "Test", "net_worth")
	if err := repo.UpdateType(ctx, a.ID, "expenses"); err != nil {
		t.Fatal(err)
	}
	got, _ := repo.GetByID(ctx, a.ID)
	if got.AccountType != "expenses" {
		t.Errorf("account_type: got %q, want %q", got.AccountType, "expenses")
	}
}

func TestSetArchived(t *testing.T) {
	repo := repository.NewSQLiteAccountRepository(setupTestDB(t))
	ctx := context.Background()

	a, _ := repo.Create(ctx, "Test", "net_worth")
	if err := repo.SetArchived(ctx, a.ID, true); err != nil {
		t.Fatal(err)
	}
	got, _ := repo.GetByID(ctx, a.ID)
	if !got.IsArchived {
		t.Error("expected IsArchived=true")
	}

	_ = repo.SetArchived(ctx, a.ID, false)
	got, _ = repo.GetByID(ctx, a.ID)
	if got.IsArchived {
		t.Error("expected IsArchived=false after unarchive")
	}
}

func TestDelete(t *testing.T) {
	repo := repository.NewSQLiteAccountRepository(setupTestDB(t))
	ctx := context.Background()

	a, _ := repo.Create(ctx, "ToDelete", "expenses")
	if err := repo.Delete(ctx, a.ID); err != nil {
		t.Fatal(err)
	}
	_, err := repo.GetByID(ctx, a.ID)
	if err == nil {
		t.Error("expected error after delete, got nil")
	}
}

func TestList_OrderedByArchivedThenLabel(t *testing.T) {
	repo := repository.NewSQLiteAccountRepository(setupTestDB(t))
	ctx := context.Background()

	b, _ := repo.Create(ctx, "Beta", "net_worth")
	a, _ := repo.Create(ctx, "Alpha", "net_worth")
	_, _ = repo.Create(ctx, "Zeta", "net_worth")
	_ = repo.SetArchived(ctx, b.ID, true)
	_ = repo.SetArchived(ctx, a.ID, true)

	accounts, _ := repo.List(ctx)
	if len(accounts) != 3 {
		t.Fatalf("expected 3 accounts, got %d", len(accounts))
	}
	// First: Zeta (active), then Alpha, Beta (archived, sorted by label)
	if accounts[0].Label != "Zeta" {
		t.Errorf("accounts[0]: got %q, want %q", accounts[0].Label, "Zeta")
	}
	if accounts[1].Label != "Alpha" {
		t.Errorf("accounts[1]: got %q, want %q", accounts[1].Label, "Alpha")
	}
	if accounts[2].Label != "Beta" {
		t.Errorf("accounts[2]: got %q, want %q", accounts[2].Label, "Beta")
	}
}
