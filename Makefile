.PHONY: dev pw pw-ui check push

PUSH_MESSAGE := $(strip $(or $(MESSAGE),$(msg),$(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))))

ifneq (,$(filter push,$(MAKECMDGOALS)))
$(eval $(PUSH_MESSAGE):;@:)
endif

dev:
	CASHCOMPASS_DEV=true .venv/bin/python -m uvicorn src.main:app --port 8080 --reload

pw:
	rm -f /tmp/cashcompass_py_test.db
	npx playwright test --config playwright.pyserver.config.ts --reporter=list

pw-ui:
	npx playwright test --config playwright.pyserver.config.ts --ui

check: pw

push: check
	@if [ -z "$(PUSH_MESSAGE)" ]; then \
		echo 'Usage: make push MESSAGE="commit message"'; \
		echo '   or: make push commit message'; \
		exit 1; \
	fi
	git add -A
	git commit -m "feat: $(PUSH_MESSAGE)"
	git push
