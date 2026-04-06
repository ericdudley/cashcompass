package handler

import (
	"fmt"
	"html/template"
	"math"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"

	"cashcompass-server/internal/model"
	"cashcompass-server/internal/service"
)

type TransactionHandler struct {
	svc      service.TransactionService
	accounts service.AccountService
	cats     service.CategoryService
	tmpl     *template.Template
}

func NewTransactionHandler(svc service.TransactionService, accounts service.AccountService, cats service.CategoryService, tmpl *template.Template) *TransactionHandler {
	return &TransactionHandler{svc: svc, accounts: accounts, cats: cats, tmpl: tmpl}
}

func (h *TransactionHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("GET /transactions", h.handleList)
	mux.HandleFunc("POST /transactions", h.handleCreate)
	mux.HandleFunc("GET /partials/transactions", h.handleListPartial)
	mux.HandleFunc("GET /partials/transactions/{id}", h.handleRowPartial)
	mux.HandleFunc("GET /partials/transactions/{id}/edit", h.handleRowEditPartial)
	mux.HandleFunc("PUT /transactions/{id}", h.handleUpdate)
	mux.HandleFunc("DELETE /transactions/{id}", h.handleDelete)
}

// --- Data structs ---

type txnFilterState struct {
	DatePreset  string
	DateFrom    string
	DateTo      string
	Label       string
	CategoryIDs []int
	AccountType string // "expenses" | "net_worth"
}

type txnGroup struct {
	Date         string
	Transactions []model.Transaction
	Subtotal     int
}

type txnListData struct {
	Groups     []txnGroup
	Filter     txnFilterState
	Categories []model.Category
}

type txnFormData struct {
	Accounts    []model.Account
	Categories  []model.Category
	Today       string
	LastAccount int
	AccountType string // current mode, passed through for hidden input
}

type txnPageData struct {
	txnListData
	Form txnFormData
}

type txnRowEditData struct {
	Transaction model.Transaction
	Accounts    []model.Account
	Categories  []model.Category
}

// --- Helpers ---

func presetToDates(preset string) (from, to string) {
	now := time.Now()
	switch preset {
	case "this_month":
		from = time.Date(now.Year(), now.Month(), 1, 0, 0, 0, 0, time.UTC).Format("2006_01_02")
		to = time.Date(now.Year(), now.Month()+1, 0, 0, 0, 0, 0, time.UTC).Format("2006_01_02")
	case "last_month":
		first := time.Date(now.Year(), now.Month()-1, 1, 0, 0, 0, 0, time.UTC)
		last := time.Date(now.Year(), now.Month(), 0, 0, 0, 0, 0, time.UTC)
		from = first.Format("2006_01_02")
		to = last.Format("2006_01_02")
	case "this_year":
		from = time.Date(now.Year(), 1, 1, 0, 0, 0, 0, time.UTC).Format("2006_01_02")
		to = time.Date(now.Year(), 12, 31, 0, 0, 0, 0, time.UTC).Format("2006_01_02")
	}
	return
}

func filterToQueryString(f txnFilterState) string {
	params := url.Values{}
	params.Set("account_type", f.AccountType)
	if f.DatePreset != "" {
		params.Set("date_preset", f.DatePreset)
	}
	if f.DateFrom != "" {
		params.Set("date_from", f.DateFrom)
	}
	if f.DateTo != "" {
		params.Set("date_to", f.DateTo)
	}
	if f.Label != "" {
		params.Set("label", f.Label)
	}
	for _, id := range f.CategoryIDs {
		params.Add("category_id", strconv.Itoa(id))
	}
	return params.Encode()
}

func parseFilterFromQuery(r *http.Request) txnFilterState {
	q := r.URL.Query()
	// account_type may arrive as a query param (GET) or form body (POST from create form)
	accountType := q.Get("account_type")
	if accountType == "" {
		accountType = r.FormValue("account_type")
	}
	if accountType != "expenses" && accountType != "net_worth" {
		accountType = "expenses"
	}
	datePreset := q.Get("date_preset")
	// Default to "this_month" when no date filters are provided
	if datePreset == "" && q.Get("date_from") == "" && q.Get("date_to") == "" {
		datePreset = "this_month"
	}
	f := txnFilterState{
		DatePreset:  datePreset,
		DateFrom:    q.Get("date_from"),
		DateTo:      q.Get("date_to"),
		Label:       q.Get("label"),
		AccountType: accountType,
	}
	for _, s := range q["category_id"] {
		if id, err := strconv.Atoi(s); err == nil {
			f.CategoryIDs = append(f.CategoryIDs, id)
		}
	}
	return f
}

func filterToModelFilter(f txnFilterState) model.TransactionFilter {
	mf := model.TransactionFilter{
		Label:       f.Label,
		CategoryIDs: f.CategoryIDs,
		AccountType: f.AccountType,
	}

	from, to := f.DateFrom, f.DateTo
	if f.DatePreset != "" && f.DatePreset != "all_time" {
		from, to = presetToDates(f.DatePreset)
		// from/to are already in yyyy_mm_dd format from presetToDates
		mf.DateFrom = from
		mf.DateTo = to
		return mf
	}

	// Convert yyyy-mm-dd query params to yyyy_mm_dd
	if from != "" {
		mf.DateFrom = strings.ReplaceAll(from, "-", "_")
	}
	if to != "" {
		mf.DateTo = strings.ReplaceAll(to, "-", "_")
	}
	return mf
}

func groupTransactions(txns []model.Transaction) []txnGroup {
	var groups []txnGroup
	idx := map[string]int{}
	for _, t := range txns {
		date := strings.ReplaceAll(t.Date, "_", "-")
		if len(date) > 10 {
			date = date[:10]
		}
		i, ok := idx[date]
		if !ok {
			groups = append(groups, txnGroup{Date: date})
			i = len(groups) - 1
			idx[date] = i
		}
		groups[i].Transactions = append(groups[i].Transactions, t)
		groups[i].Subtotal += t.Amount
	}
	return groups
}

func (h *TransactionHandler) buildListData(r *http.Request) (txnListData, error) {
	f := parseFilterFromQuery(r)
	mf := filterToModelFilter(f)
	txns, err := h.svc.List(r.Context(), mf)
	if err != nil {
		return txnListData{}, err
	}
	cats, err := h.cats.List(r.Context())
	if err != nil {
		return txnListData{}, err
	}
	return txnListData{
		Groups:     groupTransactions(txns),
		Filter:     f,
		Categories: cats,
	}, nil
}

func (h *TransactionHandler) renderList(w http.ResponseWriter, data txnListData) {
	if err := h.tmpl.ExecuteTemplate(w, "transactions-list", data); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func (h *TransactionHandler) renderRow(w http.ResponseWriter, t model.Transaction) {
	if err := h.tmpl.ExecuteTemplate(w, "transaction-row", t); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

// --- Handlers ---

func (h *TransactionHandler) handleList(w http.ResponseWriter, r *http.Request) {
	listData, err := h.buildListData(r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	allAccts, err := h.accounts.List(r.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	var modeAccts []model.Account
	for _, a := range allAccts {
		if a.AccountType == listData.Filter.AccountType && !a.IsArchived {
			modeAccts = append(modeAccts, a)
		}
	}
	cats, err := h.cats.List(r.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	lastAcct := 0
	if c, err := r.Cookie("last_account_id"); err == nil {
		if id, err := strconv.Atoi(c.Value); err == nil {
			lastAcct = id
		}
	}
	pageData := txnPageData{
		txnListData: listData,
		Form: txnFormData{
			Accounts:    modeAccts,
			Categories:  cats,
			Today:       time.Now().Format("2006-01-02"),
			LastAccount: lastAcct,
			AccountType: listData.Filter.AccountType,
		},
	}
	renderPage(w, h.tmpl, "transactions", "Transactions", "6", "transactions-content", pageData)
}

func (h *TransactionHandler) handleListPartial(w http.ResponseWriter, r *http.Request) {
	data, err := h.buildListData(r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("HX-Push-Url", "/transactions?"+filterToQueryString(data.Filter))
	h.renderList(w, data)
}

func (h *TransactionHandler) handleRowPartial(w http.ResponseWriter, r *http.Request) {
	idStr := r.PathValue("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		http.Error(w, "invalid id", http.StatusBadRequest)
		return
	}
	t, err := h.svc.GetByID(r.Context(), id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	h.renderRow(w, t)
}

func (h *TransactionHandler) handleRowEditPartial(w http.ResponseWriter, r *http.Request) {
	idStr := r.PathValue("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		http.Error(w, "invalid id", http.StatusBadRequest)
		return
	}
	t, err := h.svc.GetByID(r.Context(), id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	accts, err := h.accounts.List(r.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	cats, err := h.cats.List(r.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	if err := h.tmpl.ExecuteTemplate(w, "transaction-row-edit", txnRowEditData{
		Transaction: t,
		Accounts:    accts,
		Categories:  cats,
	}); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func (h *TransactionHandler) handleDelete(w http.ResponseWriter, r *http.Request) {
	idStr := r.PathValue("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		http.Error(w, "invalid id", http.StatusBadRequest)
		return
	}
	if err := h.svc.Delete(r.Context(), id); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	data, err := h.buildListData(r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	h.renderList(w, data)
}

func (h *TransactionHandler) handleCreate(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	date := r.FormValue("date")         // yyyy-mm-dd
	label := r.FormValue("label")
	amtStr := r.FormValue("amount")     // decimal dollars
	mode := r.FormValue("amount_mode")  // "debit" | "credit"
	accountIDStr := r.FormValue("account_id")
	categoryIDStr := r.FormValue("category_id")

	amt, err := strconv.ParseFloat(amtStr, 64)
	if err != nil {
		http.Error(w, "invalid amount", http.StatusBadRequest)
		return
	}
	cents := int(math.Round(amt * 100))
	if mode == "debit" {
		cents = -int(math.Abs(float64(cents)))
	} else {
		cents = int(math.Abs(float64(cents)))
	}

	accountID, err := strconv.Atoi(accountIDStr)
	if err != nil {
		http.Error(w, "invalid account_id", http.StatusBadRequest)
		return
	}
	acct, err := h.accounts.GetByID(r.Context(), accountID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	categoryID, _ := strconv.Atoi(categoryIDStr)
	var catLabel string
	var catIDPtr *int
	if categoryID > 0 {
		cat, err := h.cats.GetByID(r.Context(), categoryID)
		if err == nil {
			catLabel = cat.Label
			catIDPtr = &categoryID
		}
	}

	// Convert yyyy-mm-dd to yyyy_mm_dd
	isoDate := strings.ReplaceAll(date, "-", "_")
	// ISO8601 format: yyyy-mm-dd
	iso8601 := date

	p := model.CreateTransactionParams{
		ISO8601:       iso8601,
		Date:          isoDate,
		Label:         label,
		Amount:        cents,
		AccountID:     &accountID,
		AccountLabel:  acct.Label,
		CategoryID:    catIDPtr,
		CategoryLabel: catLabel,
	}
	if _, err := h.svc.Create(r.Context(), p); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	http.SetCookie(w, &http.Cookie{
		Name:  "last_account_id",
		Value: accountIDStr,
		Path:  "/",
	})

	data, err := h.buildListData(r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	h.renderList(w, data)
}

func (h *TransactionHandler) handleUpdate(w http.ResponseWriter, r *http.Request) {
	idStr := r.PathValue("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		http.Error(w, "invalid id", http.StatusBadRequest)
		return
	}
	if err := r.ParseForm(); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	date := r.FormValue("date")
	label := r.FormValue("label")
	amtStr := r.FormValue("amount")
	mode := r.FormValue("amount_mode")
	accountIDStr := r.FormValue("account_id")
	categoryIDStr := r.FormValue("category_id")

	// Update date
	if date != "" {
		isoDate := strings.ReplaceAll(date, "-", "_")
		iso8601 := date
		if err := h.svc.UpdateDate(r.Context(), id, iso8601, isoDate); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
	}

	// Update label
	if label != "" {
		if err := h.svc.UpdateLabel(r.Context(), id, label); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
	}

	// Update amount
	if amtStr != "" {
		amt, err := strconv.ParseFloat(amtStr, 64)
		if err != nil {
			http.Error(w, "invalid amount", http.StatusBadRequest)
			return
		}
		cents := int(math.Round(amt * 100))
		if mode == "debit" {
			cents = -int(math.Abs(float64(cents)))
		} else {
			cents = int(math.Abs(float64(cents)))
		}
		if err := h.svc.UpdateAmount(r.Context(), id, cents); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
	}

	// Update account
	if accountIDStr != "" {
		accountID, err := strconv.Atoi(accountIDStr)
		if err != nil {
			http.Error(w, "invalid account_id", http.StatusBadRequest)
			return
		}
		acct, err := h.accounts.GetByID(r.Context(), accountID)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		if err := h.svc.UpdateAccount(r.Context(), id, &accountID, acct.Label); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
	}

	// Update category
	if categoryIDStr != "" {
		categoryID, err := strconv.Atoi(categoryIDStr)
		if err != nil {
			http.Error(w, "invalid category_id", http.StatusBadRequest)
			return
		}
		var catLabel string
		var catIDPtr *int
		if categoryID > 0 {
			cat, err := h.cats.GetByID(r.Context(), categoryID)
			if err == nil {
				catLabel = cat.Label
				catIDPtr = &categoryID
			}
		}
		if err := h.svc.UpdateCategory(r.Context(), id, catIDPtr, catLabel); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
	}

	// Re-fetch and render updated row
	t, err := h.svc.GetByID(r.Context(), id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	h.renderRow(w, t)
}

// centsDisplay returns a formatted string like "-$12.34" or "+$12.34"
func centsDisplay(cents int) string {
	sign := "+"
	if cents < 0 {
		sign = "-"
	}
	abs := math.Abs(float64(cents))
	return fmt.Sprintf("%s$%.2f", sign, abs/100)
}
