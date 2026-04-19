.PHONY: dev dev-py dev-go test test-e2e test-e2e-py test-e2e-go test-go docker-build-server docker-push-server

DOCKER_IMAGE := ghcr.io/ericdudley/cashcompass
DOCKER_TAG   ?= latest

dev: dev-py

dev-py:
	CASHCOMPASS_DEV=true .venv/bin/python -m uvicorn src.main:app --port 8080 --reload

dev-go:
	cd server && CASHCOMPASS_DEV=true go run ./cmd/server

test: test-e2e-py

test-e2e: test-e2e-py

test-go:
	cd server && go test ./internal/...

test-e2e-go:
	rm -f /tmp/cashcompass_test.db
	npx playwright test --config playwright.server.config.ts --reporter=list

test-e2e-py:
	rm -f /tmp/cashcompass_py_test.db
	npx playwright test --config playwright.pyserver.config.ts --reporter=list

test-e2e-ui-py:
	npx playwright test --config playwright.pyserver.config.ts --ui

docker-build-server:
	docker build --build-arg VERSION=$(DOCKER_TAG) -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-push-server:
	docker push $(DOCKER_IMAGE):$(DOCKER_TAG)
