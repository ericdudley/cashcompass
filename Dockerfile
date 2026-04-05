FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY server/go.mod server/go.sum ./
RUN go mod download
COPY server/ .
RUN CGO_ENABLED=0 GOOS=linux go build -o /cashcompass-server ./cmd/server

FROM alpine:3.20
WORKDIR /app
RUN apk add --no-cache ca-certificates tzdata
COPY --from=builder /cashcompass-server /app/cashcompass-server
COPY --from=builder /app/static /app/static
VOLUME /data
ENV CASHCOMPASS_DB_PATH=/data/cashcompass.db
ENV CASHCOMPASS_PORT=8080
EXPOSE 8080
CMD ["/app/cashcompass-server"]
