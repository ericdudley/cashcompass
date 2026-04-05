package model

import "time"

type Transaction struct {
	ID            int
	ISO8601       string
	Date          string // yyyy_mm_dd
	Amount        int    // cents; negative = debit
	Label         string
	AccountID     *int
	AccountLabel  string
	CategoryID    *int
	CategoryLabel string
	CreatedAt     time.Time
	UpdatedAt     time.Time
}

// TransactionFilter is passed to TransactionRepository.List.
type TransactionFilter struct {
	DateFrom    string // yyyy_mm_dd, inclusive; empty = no lower bound
	DateTo      string // yyyy_mm_dd, inclusive; empty = no upper bound
	Label       string // substring match; empty = no filter
	AccountIDs  []int  // empty = no filter
	CategoryIDs []int  // empty = no filter
	AccountType string // "expenses" | "net_worth"; empty = no filter
}

// CreateTransactionParams holds inputs for creating a transaction.
type CreateTransactionParams struct {
	ISO8601       string
	Date          string // yyyy_mm_dd
	Amount        int
	Label         string
	AccountID     *int
	AccountLabel  string
	CategoryID    *int
	CategoryLabel string
}

// MonthSum is returned by TransactionRepository.SumByMonth.
type MonthSum struct {
	Month  string // "yyyy-mm"
	Amount int    // sum of amounts for that month
}

// AccountMonthBalance is returned by TransactionRepository.BalancesByMonth.
type AccountMonthBalance struct {
	AccountID    int
	AccountLabel string
	Month        string // "yyyy-mm"
	Balance      int    // cumulative balance through end of this month
}
