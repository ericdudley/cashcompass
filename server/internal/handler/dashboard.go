package handler

import (
	"fmt"
	"html/template"
	"math"
	"net/http"
	"sort"
	"strings"
	"time"

	"cashcompass-server/internal/format"
	"cashcompass-server/internal/model"
	"cashcompass-server/internal/service"
)

type DashboardHandler struct {
	accounts service.AccountService
	cats     service.CategoryService
	txns     service.TransactionService
	tmpl     *template.Template
}

func NewDashboardHandler(accounts service.AccountService, cats service.CategoryService, txns service.TransactionService, tmpl *template.Template) *DashboardHandler {
	return &DashboardHandler{accounts: accounts, cats: cats, txns: txns, tmpl: tmpl}
}

func (h *DashboardHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("GET /dashboard", h.handlePage)
}

// ---- template data types ----

type expenseBar struct {
	Month       string
	AmtFmt      string
	HeightStyle template.CSS
}

type catMonthRow struct {
	Category string
	Totals   []string
	Total    string
}

type netWorthLine struct {
	Label  string
	Points string       // SVG polyline points "x1,y1 x2,y2 ..."
	Color  template.CSS // safe CSS color value
}

type netWorthTableRow struct {
	Label    string
	Balances []string
}

type dashboardPageData struct {
	ThisMonthExpenses  string
	ExpenseChangePct   string
	ExpenseChangePos   bool
	AvgMonthlyExpenses string
	CurrentNetWorth    string

	ExpenseBars   []expenseBar
	ExpenseMonths []string

	CatMonths    []string
	CatMonthRows []catMonthRow

	NetWorthMonths    []string
	NetWorthTableRows []netWorthTableRow
	NetWorthLines     []netWorthLine
}

var dashNetWorthColors = []template.CSS{
	"#34d399", // emerald-400
	"#60a5fa", // blue-400
	"#f472b6", // pink-400
	"#fbbf24", // amber-400
	"#a78bfa", // violet-400
	"#fb923c", // orange-400
}


func dashMonthLabel(yyyyMM string) string {
	t, err := time.Parse("2006-01", yyyyMM)
	if err != nil {
		return yyyyMM
	}
	return t.Format("Jan '06")
}

func (h *DashboardHandler) handlePage(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	now := time.Now()
	thisMonth := now.Format("2006-01")
	prevMonth := now.AddDate(0, -1, 0).Format("2006-01")

	// --- Expenses by month ---
	expSums, err := h.txns.SumByMonth(ctx, model.AccountTypeExpenses, "", "")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// amounts are negative cents; negate to positive for display
	expMap := make(map[string]int, len(expSums))
	for _, s := range expSums {
		expMap[s.Month] = -s.Amount
	}

	// Summary stats
	thisMonthExp := expMap[thisMonth]
	prevMonthExp := expMap[prevMonth]

	var changeStr string
	changePos := false
	if prevMonthExp > 0 {
		pct := float64(thisMonthExp-prevMonthExp) / float64(prevMonthExp) * 100
		if pct >= 0 {
			changeStr = fmt.Sprintf("+%.0f%%", pct)
		} else {
			changeStr = fmt.Sprintf("%.0f%%", pct)
			changePos = true // lower spending is positive
		}
	}

	var avgSum, avgCount int
	for _, s := range expSums {
		if s.Month < thisMonth {
			avgSum += -s.Amount
			avgCount++
		}
	}
	avgStr := "$0.00"
	if avgCount > 0 {
		avgStr = format.CentsAbs(avgSum / avgCount)
	}

	// Sorted month list for bar chart (last 12)
	allExpMonths := make([]string, 0, len(expMap))
	for m := range expMap {
		allExpMonths = append(allExpMonths, m)
	}
	sort.Strings(allExpMonths)
	if len(allExpMonths) > 12 {
		allExpMonths = allExpMonths[len(allExpMonths)-12:]
	}

	maxExp := 1
	for _, m := range allExpMonths {
		if expMap[m] > maxExp {
			maxExp = expMap[m]
		}
	}

	expBars := make([]expenseBar, len(allExpMonths))
	expMonthLabels := make([]string, len(allExpMonths))
	for i, m := range allExpMonths {
		amt := expMap[m]
		pct := float64(amt) / float64(maxExp) * 100
		expBars[i] = expenseBar{
			Month:       dashMonthLabel(m),
			AmtFmt:      format.CentsAbs(amt),
			HeightStyle: template.CSS(fmt.Sprintf("height:%.1f%%", pct)),
		}
		expMonthLabels[i] = dashMonthLabel(m)
	}

	// --- Category-by-month table (last 6 available months) ---
	catMonths := allExpMonths
	if len(catMonths) > 6 {
		catMonths = catMonths[len(catMonths)-6:]
	}

	var catRows []catMonthRow
	catMonthLabels := make([]string, len(catMonths))
	for i, m := range catMonths {
		catMonthLabels[i] = dashMonthLabel(m)
	}

	if len(catMonths) > 0 {
		endOfLastMonth := func() string {
			t, err := time.Parse("2006-01", catMonths[len(catMonths)-1])
			if err != nil {
				return ""
			}
			return t.AddDate(0, 1, -1).Format("2006_01_02")
		}()

		txnList, err := h.txns.List(ctx, model.TransactionFilter{
			AccountType: model.AccountTypeExpenses,
			DateFrom:    strings.ReplaceAll(catMonths[0], "-", "_") + "_01",
			DateTo:      endOfLastMonth,
		})
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		type catMonthKey struct{ cat, month string }
		catMonthMap := map[catMonthKey]int{}
		catTotals := map[string]int{}
		catOrder := []string{}
		catSeen := map[string]bool{}

		for _, t := range txnList {
			cat := t.CategoryLabel
			if cat == "" {
				cat = "Uncategorized"
			}
			m := ""
			if len(t.Date) >= 7 {
				m = strings.ReplaceAll(t.Date[:7], "_", "-")
			}
			catMonthMap[catMonthKey{cat, m}] += -t.Amount
			catTotals[cat] += -t.Amount
			if !catSeen[cat] {
				catSeen[cat] = true
				catOrder = append(catOrder, cat)
			}
		}

		sort.Slice(catOrder, func(i, j int) bool {
			return catTotals[catOrder[i]] > catTotals[catOrder[j]]
		})

		catRows = make([]catMonthRow, len(catOrder))
		for i, c := range catOrder {
			totals := make([]string, len(catMonths))
			for j, m := range catMonths {
				amt := catMonthMap[catMonthKey{c, m}]
				if amt == 0 {
					totals[j] = "—"
				} else {
					totals[j] = format.CentsAbs(amt)
				}
			}
			catRows[i] = catMonthRow{
				Category: c,
				Totals:   totals,
				Total:    format.CentsAbs(catTotals[c]),
			}
		}
	}

	// --- Net worth ---
	allAccounts, err := h.accounts.List(ctx)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	var nwAccountIDs []int
	for _, a := range allAccounts {
		if a.AccountType == model.AccountTypeNetWorth && !a.IsArchived {
			nwAccountIDs = append(nwAccountIDs, a.ID)
		}
	}

	balances, err := h.txns.BalancesByMonth(ctx, nwAccountIDs)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	nwMonthSet := map[string]struct{}{}
	nwMap := map[int]map[string]int{}
	nwLabelMap := map[int]string{}
	for _, b := range balances {
		nwMonthSet[b.Month] = struct{}{}
		if nwMap[b.AccountID] == nil {
			nwMap[b.AccountID] = map[string]int{}
		}
		nwMap[b.AccountID][b.Month] = b.Balance
		nwLabelMap[b.AccountID] = b.AccountLabel
	}

	nwMonths := make([]string, 0, len(nwMonthSet))
	for m := range nwMonthSet {
		nwMonths = append(nwMonths, m)
	}
	sort.Strings(nwMonths)

	var totalNW int
	if len(nwMonths) > 0 {
		latestMonth := nwMonths[len(nwMonths)-1]
		for _, id := range nwAccountIDs {
			if mb, ok := nwMap[id]; ok {
				// walk up to latestMonth carrying forward last known balance
				prev := 0
				for _, m := range nwMonths {
					if b, ok := mb[m]; ok {
						prev = b
					}
					if m == latestMonth {
						break
					}
				}
				totalNW += prev
			}
		}
	}

	nwMonthLabels := make([]string, len(nwMonths))
	for i, m := range nwMonths {
		nwMonthLabels[i] = dashMonthLabel(m)
	}

	// Net worth table rows (carry forward last known balance for missing months)
	var nwTableRows []netWorthTableRow
	for _, id := range nwAccountIDs {
		mb := nwMap[id]
		if mb == nil {
			continue
		}
		balStr := make([]string, len(nwMonths))
		prev := 0
		for i, m := range nwMonths {
			if b, ok := mb[m]; ok {
				prev = b
			}
			balStr[i] = format.CentsDollars(prev)
		}
		nwTableRows = append(nwTableRows, netWorthTableRow{
			Label:    nwLabelMap[id],
			Balances: balStr,
		})
	}

	// SVG line chart (viewBox 400×150, padding 10/10/10/20)
	const (
		svgW = 400.0
		svgH = 150.0
		padL = 10.0
		padR = 10.0
		padT = 10.0
		padB = 20.0
	)

	var nwLines []netWorthLine
	if len(nwMonths) >= 2 {
		minBal, maxBal := math.MaxInt32, math.MinInt32
		for _, id := range nwAccountIDs {
			mb := nwMap[id]
			if mb == nil {
				continue
			}
			prev := 0
			for _, m := range nwMonths {
				if b, ok := mb[m]; ok {
					prev = b
				}
				if prev < minBal {
					minBal = prev
				}
				if prev > maxBal {
					maxBal = prev
				}
			}
		}
		if minBal == maxBal {
			maxBal = minBal + 1
		}

		for ci, id := range nwAccountIDs {
			mb := nwMap[id]
			if mb == nil {
				continue
			}
			pts := make([]string, len(nwMonths))
			prev := 0
			for i, m := range nwMonths {
				if b, ok := mb[m]; ok {
					prev = b
				}
				x := padL + float64(i)/float64(len(nwMonths)-1)*(svgW-padL-padR)
				y := padT + (1-float64(prev-minBal)/float64(maxBal-minBal))*(svgH-padT-padB)
				pts[i] = fmt.Sprintf("%.1f,%.1f", x, y)
			}
			color := dashNetWorthColors[ci%len(dashNetWorthColors)]
			nwLines = append(nwLines, netWorthLine{
				Label:  nwLabelMap[id],
				Points: strings.Join(pts, " "),
				Color:  color,
			})
		}
	}

	data := dashboardPageData{
		ThisMonthExpenses:  format.CentsAbs(thisMonthExp),
		ExpenseChangePct:   changeStr,
		ExpenseChangePos:   changePos,
		AvgMonthlyExpenses: avgStr,
		CurrentNetWorth:    format.CentsDollars(totalNW),
		ExpenseBars:        expBars,
		ExpenseMonths:      expMonthLabels,
		CatMonths:          catMonthLabels,
		CatMonthRows:       catRows,
		NetWorthMonths:     nwMonthLabels,
		NetWorthTableRows:  nwTableRows,
		NetWorthLines:      nwLines,
	}

	renderPage(w, h.tmpl, "dashboard", "Dashboard", "10", "dashboard-content", data)
}
