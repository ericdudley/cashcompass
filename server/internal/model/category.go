package model

import "time"

type Category struct {
	ID        int
	Label     string
	CreatedAt time.Time
	UpdatedAt time.Time
}
