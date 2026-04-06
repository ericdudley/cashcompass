package handler

import (
	"bytes"
	"html/template"
	"net/http"
)

// PageData is passed to the "layout" template for every full-page render.
type PageData struct {
	Title   string        // browser tab title (e.g. "Accounts")
	Nav     string        // active nav key passed to the nav partial
	MainGap string        // Tailwind gap value for <main> (e.g. "10" or "6")
	Body    template.HTML // pre-rendered inner content
}

// renderPage pre-renders contentTmpl with data, then wraps it in the shared layout.
func renderPage(w http.ResponseWriter, tmpl *template.Template, nav, title, gap, contentTmpl string, data any) {
	var buf bytes.Buffer
	if err := tmpl.ExecuteTemplate(&buf, contentTmpl, data); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	if err := tmpl.ExecuteTemplate(w, "layout", PageData{
		Title:   title,
		Nav:     nav,
		MainGap: gap,
		Body:    template.HTML(buf.String()),
	}); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}
