package handler

import (
	"context"
	"html/template"
	"net/http"
	"strconv"
)

// parseID extracts and converts the "{id}" path segment.
func parseID(r *http.Request) (int, error) {
	return strconv.Atoi(r.PathValue("id"))
}

// renderCard fetches an entity by ID using fetch, writes a 404 on error,
// and executes tmplName against the result on success.
func renderCard[T any](
	w http.ResponseWriter,
	r *http.Request,
	tmpl *template.Template,
	tmplName string,
	fetch func(ctx context.Context, id int) (T, error),
	id int,
) {
	entity, err := fetch(r.Context(), id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}
	if err := tmpl.ExecuteTemplate(w, tmplName, entity); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}
