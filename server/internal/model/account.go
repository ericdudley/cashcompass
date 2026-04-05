package model

import "time"

type Account struct {
	ID          int
	Label       string
	AccountType string // "expenses" | "net_worth"
	IsArchived  bool
	CreatedAt   time.Time
	UpdatedAt   time.Time
}
