.PHONY: dev pw pw-ui

dev:
	CASHCOMPASS_DEV=true .venv/bin/python -m uvicorn src.main:app --port 8080 --reload

pw:
	rm -f /tmp/cashcompass_py_test.db
	npx playwright test --config playwright.pyserver.config.ts --reporter=list

pw-ui:
	npx playwright test --config playwright.pyserver.config.ts --ui
