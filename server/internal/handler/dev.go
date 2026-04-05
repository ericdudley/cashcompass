package handler

import (
	"database/sql"
	"net/http"

	"cashcompass-server/internal/db"
)

type DevHandler struct {
	DB      *sql.DB
	DevMode bool
}

func NewDevHandler(database *sql.DB, devMode bool) *DevHandler {
	return &DevHandler{DB: database, DevMode: devMode}
}

func (h *DevHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("POST /dev/reset", h.handleReset)
}

func (h *DevHandler) handleReset(w http.ResponseWriter, r *http.Request) {
	if !h.DevMode {
		http.Error(w, "forbidden", http.StatusForbidden)
		return
	}
	for _, stmt := range []string{
		"DELETE FROM transactions",
		"DELETE FROM categories",
		"DELETE FROM accounts",
		"DELETE FROM sqlite_sequence WHERE name IN ('transactions','categories','accounts')",
	} {
		if _, err := h.DB.ExecContext(r.Context(), stmt); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
	}
	if _, err := db.SeedIfEmpty(h.DB); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte("ok"))
}
