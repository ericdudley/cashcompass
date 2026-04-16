package model_test

import (
	"testing"

	"cashcompass-server/internal/model"
)

func TestAccountType_IsValid(t *testing.T) {
	cases := []struct {
		input model.AccountType
		want  bool
	}{
		{model.AccountTypeExpenses, true},
		{model.AccountTypeNetWorth, true},
		{"", false},
		{"invalid", false},
		{"EXPENSES", false},
		{"NET_WORTH", false},
	}
	for _, tc := range cases {
		got := tc.input.IsValid()
		if got != tc.want {
			t.Errorf("AccountType(%q).IsValid() = %v, want %v", tc.input, got, tc.want)
		}
	}
}
