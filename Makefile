.PHONY: dev test-go test-e2e test docker-build-server docker-push-server

DOCKER_IMAGE := ghcr.io/ericdudley/cashcompass
DOCKER_TAG   ?= latest

dev:
	cd server && CASHCOMPASS_DEV=true go run ./cmd/server

test-go:
	cd server && go test ./internal/...

test-e2e:
	rm -f /tmp/cashcompass_test.db
	npx playwright test --config playwright.server.config.ts --reporter=list

test: test-go test-e2e

docker-build-server:
	docker build --build-arg VERSION=$(DOCKER_TAG) -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-push-server:
	docker push $(DOCKER_IMAGE):$(DOCKER_TAG)
