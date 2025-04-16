FROM golang:1.23.5-alpine AS builder

# зависимости для sqlite3
RUN apk add --no-cache gcc musl-dev && apk add --no-cache sqlite

WORKDIR /app

COPY . .
RUN go mod download && go build -o main .
EXPOSE 8080

CMD ["./main"]
