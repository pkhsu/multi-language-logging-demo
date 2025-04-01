FROM golang:1.23-alpine

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN go build -o golang-app

EXPOSE 4000
CMD ["./golang-app"]
