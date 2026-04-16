package model

import "time"

// AccountType represents the two valid account classifications.
type AccountType string

const (
	AccountTypeExpenses AccountType = "expenses"
	AccountTypeNetWorth AccountType = "net_worth"
)

// IsValid reports whether at is a recognised AccountType.
func (at AccountType) IsValid() bool {
	return at == AccountTypeExpenses || at == AccountTypeNetWorth
}

type Account struct {
	ID          int
	Label       string
	AccountType AccountType
	IsArchived  bool
	CreatedAt   time.Time
	UpdatedAt   time.Time
}
