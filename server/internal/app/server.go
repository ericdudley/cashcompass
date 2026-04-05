package app

import (
	"database/sql"
	"html/template"
	"net/http"

	"cashcompass-server/internal/handler"
	"cashcompass-server/internal/repository"
	"cashcompass-server/internal/service"
)

type Server struct {
	DB        *sql.DB
	Templates *template.Template
	DevMode   bool
}

func (s *Server) Routes() http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("GET /{$}", s.handleIndex)
	mux.HandleFunc("GET /healthz", s.handleHealth)
	mux.Handle("/static/", http.StripPrefix("/static/", http.FileServer(http.Dir("./static"))))

	txnRepo := repository.NewSQLiteTransactionRepository(s.DB)

	accountRepo := repository.NewSQLiteAccountRepository(s.DB)
	accountSvc := service.NewAccountService(accountRepo, txnRepo)
	accountHandler := handler.NewAccountHandler(accountSvc, s.Templates)
	accountHandler.RegisterRoutes(mux)

	categoryRepo := repository.NewSQLiteCategoryRepository(s.DB)
	categorySvc := service.NewCategoryService(categoryRepo, txnRepo)
	categoryHandler := handler.NewCategoryHandler(categorySvc, s.Templates)
	categoryHandler.RegisterRoutes(mux)

	txnSvc := service.NewTransactionService(txnRepo)
	txnHandler := handler.NewTransactionHandler(txnSvc, accountSvc, categorySvc, s.Templates)
	txnHandler.RegisterRoutes(mux)

	settingsHandler := handler.NewSettingsHandler(accountSvc, categorySvc, txnSvc, s.Templates, s.DevMode)
	settingsHandler.RegisterRoutes(mux)

	dashboardHandler := handler.NewDashboardHandler(accountSvc, categorySvc, txnSvc, s.Templates)
	dashboardHandler.RegisterRoutes(mux)

	devHandler := handler.NewDevHandler(s.DB, s.DevMode)
	devHandler.RegisterRoutes(mux)

	return mux
}

func (s *Server) handleIndex(w http.ResponseWriter, r *http.Request) {
	http.Redirect(w, r, "/dashboard", http.StatusFound)
}

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte("ok"))
}
