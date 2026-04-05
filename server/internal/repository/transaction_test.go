package repository_test

import (
	"context"
	"testing"

	"cashcompass-server/internal/model"
	"cashcompass-server/internal/repository"
)

func newTxnRepo(t *testing.T) *repository.SQLiteTransactionRepository {
	t.Helper()
	return repository.NewSQLiteTransactionRepository(setupTestDB(t))
}

func seedAccount(t *testing.T, db interface {
	ExecContext(context.Context, string, ...any) (interface{ LastInsertId() (int64, error) }, error)
}) {
	t.Helper()
}

// createTestAccount inserts an account and returns its ID.
func createTestAccount(t *testing.T, repo *repository.SQLiteAccountRepository, label, typ string) int {
	t.Helper()
	a, err := repo.Create(context.Background(), label, typ)
	if err != nil {
		t.Fatalf("create account: %v", err)
	}
	return a.ID
}

func makeParams(accountID *int, accountLabel string) model.CreateTransactionParams {
	return model.CreateTransactionParams{
		ISO8601:      "2026-03-01T10:00:00Z",
		Date:         "2026-03-01",
		Amount:       -1000,
		Label:        "Test txn",
		AccountID:    accountID,
		AccountLabel: accountLabel,
	}
}

func TestTxnList_Empty(t *testing.T) {
	repo := newTxnRepo(t)
	txns, err := repo.List(context.Background(), model.TransactionFilter{})
	if err != nil {
		t.Fatal(err)
	}
	if len(txns) != 0 {
		t.Errorf("expected 0, got %d", len(txns))
	}
}

func TestTxnCreate_And_GetByID(t *testing.T) {
	sqlDB := setupTestDB(t)
	repo := repository.NewSQLiteTransactionRepository(sqlDB)
	accRepo := repository.NewSQLiteAccountRepository(sqlDB)
	accID := createTestAccount(t, accRepo, "Checking", "net_worth")

	p := model.CreateTransactionParams{
		ISO8601:      "2026-03-01T10:00:00Z",
		Date:         "2026-03-01",
		Amount:       -5000,
		Label:        "Groceries run",
		AccountID:    &accID,
		AccountLabel: "Checking",
	}
	txn, err := repo.Create(context.Background(), p)
	if err != nil {
		t.Fatal(err)
	}
	if txn.ID == 0 {
		t.Error("expected non-zero ID")
	}
	if txn.Amount != -5000 {
		t.Errorf("amount: got %d, want -5000", txn.Amount)
	}
	if txn.AccountLabel != "Checking" {
		t.Errorf("account_label: got %q", txn.AccountLabel)
	}

	got, err := repo.GetByID(context.Background(), txn.ID)
	if err != nil {
		t.Fatal(err)
	}
	if got.Label != "Groceries run" {
		t.Errorf("label: got %q", got.Label)
	}
}

func TestTxnGetByID_NotFound(t *testing.T) {
	repo := newTxnRepo(t)
	_, err := repo.GetByID(context.Background(), 9999)
	if err == nil {
		t.Error("expected error for missing transaction, got nil")
	}
}

func TestTxnList_FilterByDate(t *testing.T) {
	repo := newTxnRepo(t)
	ctx := context.Background()

	for _, date := range []string{"2026-01-15", "2026-02-15", "2026-03-15"} {
		_, err := repo.Create(ctx, model.CreateTransactionParams{
			ISO8601: date + "T00:00:00Z",
			Date:    date,
			Amount:  -100,
			Label:   "txn " + date,
		})
		if err != nil {
			t.Fatal(err)
		}
	}

	txns, err := repo.List(ctx, model.TransactionFilter{DateFrom: "2026-02-01", DateTo: "2026-02-28"})
	if err != nil {
		t.Fatal(err)
	}
	if len(txns) != 1 {
		t.Errorf("expected 1, got %d", len(txns))
	}
	if txns[0].Date != "2026-02-15" {
		t.Errorf("date: got %q", txns[0].Date)
	}
}

func TestTxnList_FilterByLabel(t *testing.T) {
	repo := newTxnRepo(t)
	ctx := context.Background()

	for _, label := range []string{"electric bill", "grocery store", "electric meter"} {
		_, _ = repo.Create(ctx, model.CreateTransactionParams{
			ISO8601: "2026-03-01T00:00:00Z", Date: "2026-03-01", Amount: -100, Label: label,
		})
	}

	txns, err := repo.List(ctx, model.TransactionFilter{Label: "electric"})
	if err != nil {
		t.Fatal(err)
	}
	if len(txns) != 2 {
		t.Errorf("expected 2, got %d", len(txns))
	}
}

func TestTxnList_FilterByAccountIDs(t *testing.T) {
	sqlDB := setupTestDB(t)
	repo := repository.NewSQLiteTransactionRepository(sqlDB)
	accRepo := repository.NewSQLiteAccountRepository(sqlDB)

	acc1 := createTestAccount(t, accRepo, "A", "net_worth")
	acc2 := createTestAccount(t, accRepo, "B", "net_worth")

	ctx := context.Background()
	_, _ = repo.Create(ctx, model.CreateTransactionParams{ISO8601: "2026-03-01T00:00:00Z", Date: "2026-03-01", Amount: -100, AccountID: &acc1, AccountLabel: "A"})
	_, _ = repo.Create(ctx, model.CreateTransactionParams{ISO8601: "2026-03-01T00:00:00Z", Date: "2026-03-01", Amount: -200, AccountID: &acc2, AccountLabel: "B"})
	_, _ = repo.Create(ctx, model.CreateTransactionParams{ISO8601: "2026-03-01T00:00:00Z", Date: "2026-03-01", Amount: -300, AccountID: nil})

	txns, err := repo.List(ctx, model.TransactionFilter{AccountIDs: []int{acc1}})
	if err != nil {
		t.Fatal(err)
	}
	if len(txns) != 1 {
		t.Errorf("expected 1, got %d", len(txns))
	}
}

func TestTxnUpdateAmount(t *testing.T) {
	repo := newTxnRepo(t)
	ctx := context.Background()

	txn, _ := repo.Create(ctx, model.CreateTransactionParams{ISO8601: "2026-03-01T00:00:00Z", Date: "2026-03-01", Amount: -100})
	if err := repo.UpdateAmount(ctx, txn.ID, -999); err != nil {
		t.Fatal(err)
	}
	got, _ := repo.GetByID(ctx, txn.ID)
	if got.Amount != -999 {
		t.Errorf("amount: got %d, want -999", got.Amount)
	}
}

func TestTxnUpdateLabel(t *testing.T) {
	repo := newTxnRepo(t)
	ctx := context.Background()

	txn, _ := repo.Create(ctx, model.CreateTransactionParams{ISO8601: "2026-03-01T00:00:00Z", Date: "2026-03-01", Amount: -100, Label: "old"})
	if err := repo.UpdateLabel(ctx, txn.ID, "new"); err != nil {
		t.Fatal(err)
	}
	got, _ := repo.GetByID(ctx, txn.ID)
	if got.Label != "new" {
		t.Errorf("label: got %q, want %q", got.Label, "new")
	}
}

func TestTxnUpdateDate(t *testing.T) {
	repo := newTxnRepo(t)
	ctx := context.Background()

	txn, _ := repo.Create(ctx, model.CreateTransactionParams{ISO8601: "2026-03-01T00:00:00Z", Date: "2026-03-01", Amount: -100})
	if err := repo.UpdateDate(ctx, txn.ID, "2026-04-01T00:00:00Z", "2026-04-01"); err != nil {
		t.Fatal(err)
	}
	got, _ := repo.GetByID(ctx, txn.ID)
	if got.Date != "2026-04-01" {
		t.Errorf("date: got %q", got.Date)
	}
}

func TestTxnDelete(t *testing.T) {
	repo := newTxnRepo(t)
	ctx := context.Background()

	txn, _ := repo.Create(ctx, model.CreateTransactionParams{ISO8601: "2026-03-01T00:00:00Z", Date: "2026-03-01", Amount: -100})
	if err := repo.Delete(ctx, txn.ID); err != nil {
		t.Fatal(err)
	}
	_, err := repo.GetByID(ctx, txn.ID)
	if err == nil {
		t.Error("expected error after delete, got nil")
	}
}

func TestTxnSumByMonth(t *testing.T) {
	sqlDB := setupTestDB(t)
	repo := repository.NewSQLiteTransactionRepository(sqlDB)
	accRepo := repository.NewSQLiteAccountRepository(sqlDB)

	acc := createTestAccount(t, accRepo, "Checking", "expenses")
	ctx := context.Background()

	for _, tc := range []struct {
		date   string
		amount int
	}{
		{"2026-01-10", -1000},
		{"2026-01-20", -2000},
		{"2026-02-05", -500},
	} {
		_, _ = repo.Create(ctx, model.CreateTransactionParams{
			ISO8601: tc.date + "T00:00:00Z", Date: tc.date, Amount: tc.amount,
			AccountID: &acc, AccountLabel: "Checking",
		})
	}

	sums, err := repo.SumByMonth(ctx, "expenses", "", "")
	if err != nil {
		t.Fatal(err)
	}
	if len(sums) != 2 {
		t.Fatalf("expected 2 months, got %d", len(sums))
	}
	// Ordered DESC
	if sums[0].Month != "2026-02" {
		t.Errorf("month[0]: got %q", sums[0].Month)
	}
	if sums[0].Amount != -500 {
		t.Errorf("sum[0]: got %d", sums[0].Amount)
	}
	if sums[1].Month != "2026-01" {
		t.Errorf("month[1]: got %q", sums[1].Month)
	}
	if sums[1].Amount != -3000 {
		t.Errorf("sum[1]: got %d", sums[1].Amount)
	}
}

func TestTxnBalancesByMonth(t *testing.T) {
	sqlDB := setupTestDB(t)
	repo := repository.NewSQLiteTransactionRepository(sqlDB)
	accRepo := repository.NewSQLiteAccountRepository(sqlDB)

	acc := createTestAccount(t, accRepo, "Savings", "net_worth")
	ctx := context.Background()

	for _, tc := range []struct {
		date   string
		amount int
	}{
		{"2026-01-10", 1000},
		{"2026-02-10", 500},
		{"2026-03-10", -200},
	} {
		_, _ = repo.Create(ctx, model.CreateTransactionParams{
			ISO8601: tc.date + "T00:00:00Z", Date: tc.date, Amount: tc.amount,
			AccountID: &acc, AccountLabel: "Savings",
		})
	}

	balances, err := repo.BalancesByMonth(ctx, []int{acc})
	if err != nil {
		t.Fatal(err)
	}
	if len(balances) != 3 {
		t.Fatalf("expected 3, got %d", len(balances))
	}
	if balances[0].Balance != 1000 {
		t.Errorf("balance[0]: got %d, want 1000", balances[0].Balance)
	}
	if balances[1].Balance != 1500 {
		t.Errorf("balance[1]: got %d, want 1500", balances[1].Balance)
	}
	if balances[2].Balance != 1300 {
		t.Errorf("balance[2]: got %d, want 1300", balances[2].Balance)
	}
}

func TestTxnBalancesByMonth_Empty(t *testing.T) {
	repo := newTxnRepo(t)
	balances, err := repo.BalancesByMonth(context.Background(), nil)
	if err != nil {
		t.Fatal(err)
	}
	if len(balances) != 0 {
		t.Errorf("expected 0, got %d", len(balances))
	}
}

func TestTxnSyncAccountLabel(t *testing.T) {
	sqlDB := setupTestDB(t)
	repo := repository.NewSQLiteTransactionRepository(sqlDB)
	accRepo := repository.NewSQLiteAccountRepository(sqlDB)

	acc := createTestAccount(t, accRepo, "Old Name", "net_worth")
	ctx := context.Background()

	txn, _ := repo.Create(ctx, model.CreateTransactionParams{
		ISO8601: "2026-03-01T00:00:00Z", Date: "2026-03-01", Amount: -100,
		AccountID: &acc, AccountLabel: "Old Name",
	})

	if err := repo.SyncAccountLabel(ctx, acc, "New Name"); err != nil {
		t.Fatal(err)
	}
	got, _ := repo.GetByID(ctx, txn.ID)
	if got.AccountLabel != "New Name" {
		t.Errorf("account_label: got %q, want %q", got.AccountLabel, "New Name")
	}
}

func TestTxnSyncCategoryLabel(t *testing.T) {
	sqlDB := setupTestDB(t)
	repo := repository.NewSQLiteTransactionRepository(sqlDB)
	catRepo := repository.NewSQLiteCategoryRepository(sqlDB)
	ctx := context.Background()

	cat, _ := catRepo.Create(ctx, "Old Cat")
	txn, _ := repo.Create(ctx, model.CreateTransactionParams{
		ISO8601: "2026-03-01T00:00:00Z", Date: "2026-03-01", Amount: -100,
		CategoryID: &cat.ID, CategoryLabel: "Old Cat",
	})

	if err := repo.SyncCategoryLabel(ctx, cat.ID, "New Cat"); err != nil {
		t.Fatal(err)
	}
	got, _ := repo.GetByID(ctx, txn.ID)
	if got.CategoryLabel != "New Cat" {
		t.Errorf("category_label: got %q, want %q", got.CategoryLabel, "New Cat")
	}
}
