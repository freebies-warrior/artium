## Artium Backend

### Installation and Run Instructions

1. Install `Go` by referring to the official documentation [here](https://go.dev/doc/install).
2. Install all the dependencies
```sh
go mod tidy
```
3. Setup `.env`
```
DATABASE_URI=<YOUR_POSTGRESQL_DATABASE_URI>
JWT_SECRET=<YOUR_SECRET_KEY>
APP_BASE_URL=<YOUR_BASE_URL>
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