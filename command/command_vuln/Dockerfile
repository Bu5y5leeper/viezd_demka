# Стадия сборки (builder) на Alpine
FROM golang:1.23.5-alpine AS builder

RUN apk add --no-cache git  # Устанавливаем git для зависимостей Go

WORKDIR /app
COPY . .
RUN go build -o main .

# Финальная стадия на Alpine
FROM alpine:latest

RUN apk add --no-cache \
    busybox-extras \
    bash \
    coreutils \
    curl

WORKDIR /app
COPY --from=builder /app/main .
COPY --from=builder /app/templates ./templates
COPY --from=builder /app/static ./static

EXPOSE 8080
CMD ["./main"]
