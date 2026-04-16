package handler

import (
	"encoding/csv"
	"fmt"
	"html/template"
	"math"
	"net/http"
	"sort"
	"strconv"
	"strings"
	"time"

	"cashcompass-server/internal/model"
	"cashcompass-server/internal/service"
)

type SettingsHandler struct {
	accounts service.AccountService
	cats     service.CategoryService
	txns     service.TransactionService
	tmpl     *template.Template
	devMode  bool
}

func NewSettingsHandler(accounts service.AccountService, cats service.CategoryService, txns service.TransactionService, tmpl *template.Template, devMode bool) *SettingsHandler {
	return &SettingsHandler{accounts: accounts, cats: cats, txns: txns, tmpl: tmpl, devMode: devMode}
}

func (h *SettingsHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("GET /settings", h.handlePage)
	mux.HandleFunc("POST /settings/import/expenses", h.handleImportExpenses)
	mux.HandleFunc("GET /settings/export/expenses", h.handleExportExpenses)
	mux.HandleFunc("POST /settings/import/accounts", h.handleImportAccounts)
	mux.HandleFunc("GET /settings/export/accounts", h.handleExportAccounts)
	mux.HandleFunc("POST /settings/reset-database", h.handleResetDatabase)
}

type settingsPageData struct {
	ImportedType  string // "expenses" | "accounts" | ""
	ImportedCount int
	ErrorMsg      string
	DevMode       bool
	Reset         bool
}

func (h *SettingsHandler) handlePage(w http.ResponseWriter, r *http.Request) {
	data := settingsPageData{
		ImportedType: r.URL.Query().Get("imported"),
		ErrorMsg:     r.URL.Query().Get("error"),
		DevMode:      h.devMode,
		Reset:        r.URL.Query().Get("reset") == "1",
	}
	if c := r.URL.Query().Get("count"); c != "" {
		data.ImportedCount, _ = strconv.Atoi(c)
	}
	renderPage(w, h.tmpl, "settings", "Settings", "10", "settings-content", data)
}

// parseAmount strips "$" and "," then returns cents (positive float input → positive cents).
func parseAmount(s string) (int, error) {
	s = strings.ReplaceAll(s, "$", "")
	s = strings.ReplaceAll(s, ",", "")
	s = strings.TrimSpace(s)
	f, err := strconv.ParseFloat(s, 64)
	if err != nil {
		return 0, fmt.Errorf("invalid amount %q: %w", s, err)
	}
	return int(math.Round(f * 100)), nil
}

// parseDate accepts an ISO8601 timestamp or plain yyyy-mm-dd string and returns
// (iso8601 string, yyyy_mm_dd string). For full timestamps the date is interpreted
// in the given IANA timezone (e.g. "America/Los_Angeles") so that a UTC timestamp
// recorded at local midnight or later in the day maps to the correct local date.
// Falls back to UTC if the timezone is empty or unrecognised.
func parseDate(s, timezone string) (string, string, error) {
	s = strings.TrimSpace(s)
	if len(s) < 10 {
		return "", "", fmt.Errorf("invalid date %q", s)
	}

	// Plain date — no timezone conversion needed.
	if len(s) == 10 {
		if _, err := time.Parse("2006-01-02", s); err != nil {
			return "", "", fmt.Errorf("invalid date %q", s)
		}
		return s, strings.ReplaceAll(s, "-", "_"), nil
	}

	// Full timestamp — parse then convert to local date in the given timezone.
	if s[10] != 'T' && s[10] != ' ' {
		return "", "", fmt.Errorf("invalid date %q", s)
	}
	t, err := time.Parse(time.RFC3339Nano, s)
	if err != nil {
		// Try without nanoseconds / Z suffix variants.
		for _, layout := range []string{"2006-01-02T15:04:05Z", "2006-01-02T15:04:05"} {
			t, err = time.Parse(layout, s)
			if err == nil {
				break
			}
		}
	}
	if err != nil {
		return "", "", fmt.Errorf("invalid date %q", s)
	}

	loc, locErr := time.LoadLocation(timezone)
	if timezone == "" || locErr != nil {
		loc = time.UTC
	}
	datePart := t.In(loc).Format("2006-01-02")
	return datePart, strings.ReplaceAll(datePart, "-", "_"), nil
}

// ensureCategory finds a category by label or creates it. catMap is updated in place.
func (h *SettingsHandler) ensureCategory(r *http.Request, label string, catMap map[string]model.Category) (model.Category, error) {
	if c, ok := catMap[label]; ok {
		return c, nil
	}
	c, err := h.cats.Create(r.Context(), label)
	if err != nil {
		return model.Category{}, err
	}
	catMap[label] = c
	return c, nil
}

func (h *SettingsHandler) handleImportExpenses(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseMultipartForm(32 << 20); err != nil {
		http.Redirect(w, r, "/settings?error="+urlEncode("failed to parse form"), http.StatusSeeOther)
		return
	}
	timezone := r.FormValue("timezone")
	file, _, err := r.FormFile("file")
	if err != nil {
		http.Redirect(w, r, "/settings?error="+urlEncode("no file uploaded"), http.StatusSeeOther)
		return
	}
	defer file.Close()

	csvReader := csv.NewReader(file)
	csvReader.TrimLeadingSpace = true
	records, err := csvReader.ReadAll()
	if err != nil {
		http.Redirect(w, r, "/settings?error="+urlEncode("invalid CSV: "+err.Error()), http.StatusSeeOther)
		return
	}
	if len(records) < 2 {
		http.Redirect(w, r, "/settings?imported=expenses&count=0", http.StatusSeeOther)
		return
	}

	// Map header columns
	header := records[0]
	colIdx := map[string]int{}
	for i, h := range header {
		colIdx[strings.TrimSpace(h)] = i
	}
	for _, required := range []string{"Amount", "Category", "Date", "Description"} {
		if _, ok := colIdx[required]; !ok {
			http.Redirect(w, r, "/settings?error="+urlEncode("missing column: "+required), http.StatusSeeOther)
			return
		}
	}

	ctx := r.Context()

	// Create import account
	importAccount, err := h.accounts.Create(ctx, "Imported Expenses "+time.Now().Format(time.RFC3339), model.AccountTypeExpenses)
	if err != nil {
		http.Redirect(w, r, "/settings?error="+urlEncode(err.Error()), http.StatusSeeOther)
		return
	}

	// Load existing categories into map
	catList, err := h.cats.List(ctx)
	if err != nil {
		http.Redirect(w, r, "/settings?error="+urlEncode(err.Error()), http.StatusSeeOther)
		return
	}
	catMap := make(map[string]model.Category, len(catList))
	for _, c := range catList {
		catMap[c.Label] = c
	}

	count := 0
	for _, row := range records[1:] {
		if len(row) == 0 {
			continue
		}
		amtStr := row[colIdx["Amount"]]
		catLabel := strings.TrimSpace(row[colIdx["Category"]])
		dateStr := strings.TrimSpace(row[colIdx["Date"]])
		desc := strings.TrimSpace(row[colIdx["Description"]])

		if dateStr == "" {
			continue
		}

		cents, err := parseAmount(amtStr)
		if err != nil {
			continue
		}
		// Expenses are always debits (negative)
		cents = -int(math.Abs(float64(cents)))

		iso8601, yyyymmdd, err := parseDate(dateStr, timezone)
		if err != nil {
			continue
		}

		cat, err := h.ensureCategory(r, catLabel, catMap)
		if err != nil {
			http.Redirect(w, r, "/settings?error="+urlEncode(err.Error()), http.StatusSeeOther)
			return
		}

		catID := cat.ID
		p := model.CreateTransactionParams{
			ISO8601:       iso8601,
			Date:          yyyymmdd,
			Label:         desc,
			Amount:        cents,
			AccountID:     &importAccount.ID,
			AccountLabel:  importAccount.Label,
			CategoryID:    &catID,
			CategoryLabel: cat.Label,
		}
		if _, err := h.txns.Create(ctx, p); err != nil {
			http.Redirect(w, r, "/settings?error="+urlEncode(err.Error()), http.StatusSeeOther)
			return
		}
		count++
	}

	http.Redirect(w, r, fmt.Sprintf("/settings?imported=expenses&count=%d", count), http.StatusSeeOther)
}

func (h *SettingsHandler) handleExportExpenses(w http.ResponseWriter, r *http.Request) {
	txns, err := h.txns.List(r.Context(), model.TransactionFilter{AccountType: model.AccountTypeExpenses})
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "text/csv")
	w.Header().Set("Content-Disposition", `attachment; filename="expenses.csv"`)

	cw := csv.NewWriter(w)
	_ = cw.Write([]string{"Amount", "Category", "Date", "Description"})
	for _, t := range txns {
		amt := fmt.Sprintf("%.2f", math.Abs(float64(t.Amount))/100)
		cat := t.CategoryLabel
		if cat == "" {
			cat = "Uncategorized"
		}
		_ = cw.Write([]string{amt, cat, t.ISO8601, t.Label})
	}
	cw.Flush()
}

func (h *SettingsHandler) handleImportAccounts(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseMultipartForm(32 << 20); err != nil {
		http.Redirect(w, r, "/settings?error="+urlEncode("failed to parse form"), http.StatusSeeOther)
		return
	}
	timezone := r.FormValue("timezone")
	file, _, err := r.FormFile("file")
	if err != nil {
		http.Redirect(w, r, "/settings?error="+urlEncode("no file uploaded"), http.StatusSeeOther)
		return
	}
	defer file.Close()

	csvReader := csv.NewReader(file)
	csvReader.TrimLeadingSpace = true
	records, err := csvReader.ReadAll()
	if err != nil {
		http.Redirect(w, r, "/settings?error="+urlEncode("invalid CSV: "+err.Error()), http.StatusSeeOther)
		return
	}
	if len(records) < 2 {
		http.Redirect(w, r, "/settings?imported=accounts&count=0", http.StatusSeeOther)
		return
	}

	header := records[0]
	colIdx := map[string]int{}
	for i, h := range header {
		colIdx[strings.TrimSpace(h)] = i
	}
	for _, required := range []string{"Account", "Date", "Balance"} {
		if _, ok := colIdx[required]; !ok {
			http.Redirect(w, r, "/settings?error="+urlEncode("missing column: "+required), http.StatusSeeOther)
			return
		}
	}

	ctx := r.Context()

	// Ensure Reconciliation category
	catList, err := h.cats.List(ctx)
	if err != nil {
		http.Redirect(w, r, "/settings?error="+urlEncode(err.Error()), http.StatusSeeOther)
		return
	}
	catMap := make(map[string]model.Category, len(catList))
	for _, c := range catList {
		catMap[c.Label] = c
	}
	reconcileCat, err := h.ensureCategory(r, "Reconciliation", catMap)
	if err != nil {
		http.Redirect(w, r, "/settings?error="+urlEncode(err.Error()), http.StatusSeeOther)
		return
	}

	// Load existing net_worth accounts
	allAccounts, err := h.accounts.List(ctx)
	if err != nil {
		http.Redirect(w, r, "/settings?error="+urlEncode(err.Error()), http.StatusSeeOther)
		return
	}
	acctMap := make(map[string]model.Account)
	for _, a := range allAccounts {
		if a.AccountType == model.AccountTypeNetWorth {
			acctMap[a.Label] = a
		}
	}

	// Group rows by account
	type csvRow struct{ date, balance string }
	grouped := map[string][]csvRow{}
	for _, row := range records[1:] {
		if len(row) == 0 {
			continue
		}
		acctLabel := strings.TrimSpace(row[colIdx["Account"]])
		dateStr := strings.TrimSpace(row[colIdx["Date"]])
		balStr := strings.TrimSpace(row[colIdx["Balance"]])
		if acctLabel == "" || dateStr == "" {
			continue
		}
		grouped[acctLabel] = append(grouped[acctLabel], csvRow{date: dateStr, balance: balStr})
	}

	// Sort account names for deterministic order
	acctNames := make([]string, 0, len(grouped))
	for name := range grouped {
		acctNames = append(acctNames, name)
	}
	sort.Strings(acctNames)

	count := 0
	for _, acctLabel := range acctNames {
		rows := grouped[acctLabel]

		// Ensure account exists
		acct, ok := acctMap[acctLabel]
		if !ok {
			acct, err = h.accounts.Create(ctx, acctLabel, model.AccountTypeNetWorth)
			if err != nil {
				http.Redirect(w, r, "/settings?error="+urlEncode(err.Error()), http.StatusSeeOther)
				return
			}
			acctMap[acctLabel] = acct
		}

		// Sort rows by date ascending
		sort.Slice(rows, func(i, j int) bool {
			return rows[i].date < rows[j].date
		})

		prevBalance := 0
		for _, row := range rows {
			cents, err := parseAmount(row.balance)
			if err != nil {
				continue
			}
			delta := cents - prevBalance
			if delta == 0 {
				prevBalance = cents
				continue
			}

			iso8601, yyyymmdd, err := parseDate(row.date, timezone)
			if err != nil {
				continue
			}

			reconcileID := reconcileCat.ID
			p := model.CreateTransactionParams{
				ISO8601:       iso8601,
				Date:          yyyymmdd,
				Label:         "Reconciliation",
				Amount:        delta,
				AccountID:     &acct.ID,
				AccountLabel:  acct.Label,
				CategoryID:    &reconcileID,
				CategoryLabel: reconcileCat.Label,
			}
			if _, err := h.txns.Create(ctx, p); err != nil {
				http.Redirect(w, r, "/settings?error="+urlEncode(err.Error()), http.StatusSeeOther)
				return
			}
			count++
			prevBalance = cents
		}
	}

	http.Redirect(w, r, fmt.Sprintf("/settings?imported=accounts&count=%d", count), http.StatusSeeOther)
}

func (h *SettingsHandler) handleExportAccounts(w http.ResponseWriter, r *http.Request) {
	allAccounts, err := h.accounts.List(r.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "text/csv")
	w.Header().Set("Content-Disposition", `attachment; filename="accounts.csv"`)

	cw := csv.NewWriter(w)
	_ = cw.Write([]string{"Account", "Date", "Balance"})

	for _, acct := range allAccounts {
		if acct.AccountType != model.AccountTypeNetWorth {
			continue
		}
		txns, err := h.txns.List(r.Context(), model.TransactionFilter{AccountIDs: []int{acct.ID}})
		if err != nil {
			continue
		}
		// txns are DESC by date; reverse to replay in ASC order
		for i, j := 0, len(txns)-1; i < j; i, j = i+1, j-1 {
			txns[i], txns[j] = txns[j], txns[i]
		}

		// Cumulative balance per date (last transaction on a date wins)
		type dateBalance struct {
			date    string
			balance int
		}
		var dates []string
		balMap := map[string]int{}
		cumulative := 0
		for _, t := range txns {
			cumulative += t.Amount
			d := t.ISO8601
			if len(d) > 10 {
				d = d[:10]
			}
			if _, seen := balMap[d]; !seen {
				dates = append(dates, d)
			}
			balMap[d] = cumulative
		}

		for _, d := range dates {
			bal := fmt.Sprintf("%.2f", float64(balMap[d])/100)
			_ = cw.Write([]string{acct.Label, d, bal})
		}
	}

	cw.Flush()
}

func (h *SettingsHandler) handleResetDatabase(w http.ResponseWriter, r *http.Request) {
	if !h.devMode {
		http.Error(w, "not available", http.StatusForbidden)
		return
	}
	ctx := r.Context()

	allTxns, err := h.txns.List(ctx, model.TransactionFilter{})
	if err != nil {
		http.Redirect(w, r, "/settings?error="+urlEncode(err.Error()), http.StatusSeeOther)
		return
	}
	for _, t := range allTxns {
		if err := h.txns.Delete(ctx, t.ID); err != nil {
			http.Redirect(w, r, "/settings?error="+urlEncode(err.Error()), http.StatusSeeOther)
			return
		}
	}

	allCats, err := h.cats.List(ctx)
	if err != nil {
		http.Redirect(w, r, "/settings?error="+urlEncode(err.Error()), http.StatusSeeOther)
		return
	}
	for _, c := range allCats {
		if err := h.cats.Delete(ctx, c.ID); err != nil {
			http.Redirect(w, r, "/settings?error="+urlEncode(err.Error()), http.StatusSeeOther)
			return
		}
	}

	allAccts, err := h.accounts.List(ctx)
	if err != nil {
		http.Redirect(w, r, "/settings?error="+urlEncode(err.Error()), http.StatusSeeOther)
		return
	}
	for _, a := range allAccts {
		if err := h.accounts.Delete(ctx, a.ID); err != nil {
			http.Redirect(w, r, "/settings?error="+urlEncode(err.Error()), http.StatusSeeOther)
			return
		}
	}

	http.Redirect(w, r, "/settings?reset=1", http.StatusSeeOther)
}

func urlEncode(s string) string {
	return strings.ReplaceAll(s, " ", "+")
}
