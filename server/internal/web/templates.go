package web

import (
	"embed"
	"html/template"
	"strings"
	"time"

	"cashcompass-server/internal/format"
)

//go:embed templates/*.html templates/partials/*.html
var templatesFS embed.FS

type presetOption struct {
	Value string
	Label string
}

func ParseTemplates() (*template.Template, error) {
	funcs := template.FuncMap{
		"divf": func(a, b int) float64 {
			if b == 0 {
				return 0
			}
			return float64(a) / float64(b)
		},
		"fmtDate": func(yyyyMMdd string) string {
			s := strings.ReplaceAll(yyyyMMdd, "_", "-")
			t, err := time.Parse("2006-01-02", s)
			if err != nil {
				return yyyyMMdd
			}
			return t.Format("Jan 02, 2006")
		},
		"isSelected": func(ids []int, id int) bool {
			for _, v := range ids {
				if v == id {
					return true
				}
			}
			return false
		},
		"centsToDecimal": format.CentsInput,
		"derefInt": func(p *int) int {
			if p == nil {
				return 0
			}
			return *p
		},
		"absInt": func(n int) int {
			if n < 0 {
				return -n
			}
			return n
		},
		"formatCents": format.Cents,
		"presetOptions": func() []presetOption {
			return []presetOption{
				{"this_month", "This Month"},
				{"last_month", "Last Month"},
				{"this_year", "This Year"},
				{"all_time", "All Time"},
			}
		},
		"isoDateValue": func(s string) string {
			// Convert "2026_03_01" or "2026-03-01T00:00:00Z" to "2026-03-01"
			s = strings.ReplaceAll(s, "_", "-")
			if len(s) > 10 {
				s = s[:10]
			}
			return s
		},
	}
	return template.New("base").Funcs(funcs).ParseFS(templatesFS, "templates/*.html", "templates/partials/*.html")
}
