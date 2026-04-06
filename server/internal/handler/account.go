package handler

import (
	"html/template"
	"net/http"
	"strconv"

	"cashcompass-server/internal/model"
	"cashcompass-server/internal/service"
)

type AccountHandler struct {
	svc  service.AccountService
	tmpl *template.Template
}

func NewAccountHandler(svc service.AccountService, tmpl *template.Template) *AccountHandler {
	return &AccountHandler{svc: svc, tmpl: tmpl}
}

func (h *AccountHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("GET /accounts", h.handleList)
	mux.HandleFunc("POST /accounts", h.handleCreate)
	mux.HandleFunc("PUT /accounts/{id}/label", h.handleUpdateLabel)
	mux.HandleFunc("PUT /accounts/{id}/type", h.handleUpdateType)
	mux.HandleFunc("PUT /accounts/{id}/archive", h.handleToggleArchive)
	mux.HandleFunc("DELETE /accounts/{id}", h.handleDelete)
	mux.HandleFunc("GET /partials/accounts", h.handleListPartial)
	mux.HandleFunc("GET /partials/accounts/{id}", h.handleCardPartial)
	mux.HandleFunc("GET /partials/accounts/{id}/edit", h.handleCardEditPartial)
}

type AccountsListData struct {
	Active   []model.Account
	Archived []model.Account
}

func splitAccounts(accounts []model.Account) AccountsListData {
	data := AccountsListData{}
	for _, a := range accounts {
		if a.IsArchived {
			data.Archived = append(data.Archived, a)
		} else {
			data.Active = append(data.Active, a)
		}
	}
	return data
}

func (h *AccountHandler) handleList(w http.ResponseWriter, r *http.Request) {
	accounts, err := h.svc.List(r.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	renderPage(w, h.tmpl, "accounts", "Accounts", "10", "accounts-content", splitAccounts(accounts))
}

func (h *AccountHandler) handleListPartial(w http.ResponseWriter, r *http.Request) {
	accounts, err := h.svc.List(r.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	if err := h.tmpl.ExecuteTemplate(w, "accounts-list", splitAccounts(accounts)); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func (h *AccountHandler) handleCreate(w http.ResponseWriter, r *http.Request) {
	label := r.FormValue("label")
	accountType := r.FormValue("account_type")
	if _, err := h.svc.Create(r.Context(), label, accountType); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	accounts, err := h.svc.List(r.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	if err := h.tmpl.ExecuteTemplate(w, "accounts-list", splitAccounts(accounts)); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func (h *AccountHandler) parseID(r *http.Request) (int, error) {
	return strconv.Atoi(r.PathValue("id"))
}

func (h *AccountHandler) renderCard(w http.ResponseWriter, r *http.Request, id int) {
	a, err := h.svc.GetByID(r.Context(), id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}
	if err := h.tmpl.ExecuteTemplate(w, "account-card", a); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func (h *AccountHandler) handleUpdateLabel(w http.ResponseWriter, r *http.Request) {
	id, err := h.parseID(r)
	if err != nil {
		http.Error(w, "invalid id", http.StatusBadRequest)
		return
	}
	if err := h.svc.UpdateLabel(r.Context(), id, r.FormValue("label")); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	h.renderCard(w, r, id)
}

func (h *AccountHandler) handleUpdateType(w http.ResponseWriter, r *http.Request) {
	id, err := h.parseID(r)
	if err != nil {
		http.Error(w, "invalid id", http.StatusBadRequest)
		return
	}
	if err := h.svc.UpdateType(r.Context(), id, r.FormValue("account_type")); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	h.renderCard(w, r, id)
}

func (h *AccountHandler) handleToggleArchive(w http.ResponseWriter, r *http.Request) {
	id, err := h.parseID(r)
	if err != nil {
		http.Error(w, "invalid id", http.StatusBadRequest)
		return
	}
	if _, err := h.svc.ToggleArchived(r.Context(), id); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	accounts, err := h.svc.List(r.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	if err := h.tmpl.ExecuteTemplate(w, "accounts-list", splitAccounts(accounts)); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func (h *AccountHandler) handleDelete(w http.ResponseWriter, r *http.Request) {
	id, err := h.parseID(r)
	if err != nil {
		http.Error(w, "invalid id", http.StatusBadRequest)
		return
	}
	if err := h.svc.Delete(r.Context(), id); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusOK)
}

func (h *AccountHandler) handleCardPartial(w http.ResponseWriter, r *http.Request) {
	id, err := h.parseID(r)
	if err != nil {
		http.Error(w, "invalid id", http.StatusBadRequest)
		return
	}
	h.renderCard(w, r, id)
}

func (h *AccountHandler) handleCardEditPartial(w http.ResponseWriter, r *http.Request) {
	id, err := h.parseID(r)
	if err != nil {
		http.Error(w, "invalid id", http.StatusBadRequest)
		return
	}
	a, err := h.svc.GetByID(r.Context(), id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}
	if err := h.tmpl.ExecuteTemplate(w, "account-card-edit", a); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}
