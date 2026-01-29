# -------- build stage --------
FROM golang:1.25.6-alpine AS builder
WORKDIR /src

# Install git (needed for some go module fetches)
RUN apk add --no-cache git

# Cache deps
COPY go.mod go.sum ./
RUN go mod download

# Copy source
COPY . .

# Allow overriding where your main package lives
# Example: ./cmd/server, ./cmd/api, or just ./ (if main.go at root)
ARG MAIN_PKG=.
ARG BIN_NAME=server

# Build
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /out/${BIN_NAME} ${MAIN_PKG}

# -------- runtime stage --------
FROM alpine:3.20
WORKDIR /app

# Optional: ca-certs if you call HTTPS APIs
RUN apk add --no-cache ca-certificates

ARG BIN_NAME=server
COPY --from=builder /out/${BIN_NAME} /app/server

# App config via env
ENV PORT=8080
EXPOSE 8080

# Run
CMD ["/app/server"]
