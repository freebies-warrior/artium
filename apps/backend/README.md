## Artium Backend

### Installation and Run Instructions

1. Install `Go` by referring to the official documentation [here](https://go.dev/doc/install).
2. Install all the dependencies
```sh
go mod tidy
```
3. Setup `.env`
```
DATABASE_URL=postgresql://<DB_USER>:<DB_PASSWORD>@localhost:5435/<DB_NAME>
JWT_SECRET=<JWT_SECRET>
APP_BASE_URL=http://localhost:3000
BACKEND_BASE_URL=http://localhost:8080
AI_BASE_URL=http://localhost:8000

ITEM_STATUS_SWEEPER_INTERVAL=1m

R2_ACCOUNT_ID=<R2_ACCOUNT_ID>
R2_ACCESS_KEY_ID=<R2_ACCESS_KEY_ID>
R2_SECRET_ACCESS_KEY=<R2_SECRET_ACCESS_KEY>
R2_BUCKET=<R2_BUCKET_NAME>

AI_SERVICE_TOKEN=<AI_SERVICE_TOKEN>

SMTP_HOST=<SMTP_HOST>
SMTP_PORT=1025
SMTP_USERNAME=
SMTP_PASSWORD=
EMAIL_FROM_NAME=Artium Local
EMAIL_FROM_ADDRESS=no-reply@artium.local
```
4. Initialize/Reset Database (run on first setup or reset)
```sh
go run cmd/dbreset/main.go
```
5. Run the project, by default it is live on `localhost:8080`
```
go run .
```

### Testing

To run tests, use the following command:
```sh
go test ./... -cover -coverprofile=coverage.out -tags=unit
```