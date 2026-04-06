package handler

import (
	"html/template"
	"net/http"
	"strconv"

	"cashcompass-server/internal/service"
)

type CategoryHandler struct {
	svc  service.CategoryService
	tmpl *template.Template
}

func NewCategoryHandler(svc service.CategoryService, tmpl *template.Template) *CategoryHandler {
	return &CategoryHandler{svc: svc, tmpl: tmpl}
}

func (h *CategoryHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("GET /categories", h.handleList)
	mux.HandleFunc("POST /categories", h.handleCreate)
	mux.HandleFunc("PUT /categories/{id}/label", h.handleUpdateLabel)
	mux.HandleFunc("DELETE /categories/{id}", h.handleDelete)
	mux.HandleFunc("GET /partials/categories", h.handleListPartial)
	mux.HandleFunc("GET /partials/categories/{id}", h.handleCardPartial)
	mux.HandleFunc("GET /partials/categories/{id}/edit", h.handleCardEditPartial)
}

func (h *CategoryHandler) parseID(r *http.Request) (int, error) {
	return strconv.Atoi(r.PathValue("id"))
}

func (h *CategoryHandler) renderCard(w http.ResponseWriter, r *http.Request, id int) {
	c, err := h.svc.GetByID(r.Context(), id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}
	if err := h.tmpl.ExecuteTemplate(w, "category-card", c); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func (h *CategoryHandler) renderList(w http.ResponseWriter, r *http.Request) {
	categories, err := h.svc.List(r.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	if err := h.tmpl.ExecuteTemplate(w, "categories-list", categories); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func (h *CategoryHandler) handleList(w http.ResponseWriter, r *http.Request) {
	categories, err := h.svc.List(r.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	renderPage(w, h.tmpl, "categories", "Categories", "10", "categories-content", categories)
}

func (h *CategoryHandler) handleListPartial(w http.ResponseWriter, r *http.Request) {
	h.renderList(w, r)
}

func (h *CategoryHandler) handleCreate(w http.ResponseWriter, r *http.Request) {
	label := r.FormValue("label")
	if _, err := h.svc.Create(r.Context(), label); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	h.renderList(w, r)
}

func (h *CategoryHandler) handleUpdateLabel(w http.ResponseWriter, r *http.Request) {
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

func (h *CategoryHandler) handleDelete(w http.ResponseWriter, r *http.Request) {
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

func (h *CategoryHandler) handleCardPartial(w http.ResponseWriter, r *http.Request) {
	id, err := h.parseID(r)
	if err != nil {
		http.Error(w, "invalid id", http.StatusBadRequest)
		return
	}
	h.renderCard(w, r, id)
}

func (h *CategoryHandler) handleCardEditPartial(w http.ResponseWriter, r *http.Request) {
	id, err := h.parseID(r)
	if err != nil {
		http.Error(w, "invalid id", http.StatusBadRequest)
		return
	}
	c, err := h.svc.GetByID(r.Context(), id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}
	if err := h.tmpl.ExecuteTemplate(w, "category-card-edit", c); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}
