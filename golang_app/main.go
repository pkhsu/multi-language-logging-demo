package main

import (
	"fmt"
	"io"
	"net/http"
	"time"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

func main() {
	// 1) 建立自訂 Zap Config
	cfg := zap.NewProductionConfig()
	// 自訂 EncoderConfig 讓欄位與時間格式對齊需求
	cfg.EncoderConfig.TimeKey = "timestamp"
	cfg.EncoderConfig.EncodeTime = zapcore.TimeEncoderOfLayout(time.RFC3339) // e.g. 2025-03-12T02:16:02+00:00
	cfg.EncoderConfig.LevelKey = "level"
	cfg.EncoderConfig.MessageKey = "message"
	cfg.EncoderConfig.NameKey = "service"
	// 預設不會有 instance, correlationId, context，需自行帶 Field

	logger, _ := cfg.Build()
	defer logger.Sync()

	// 2) 定義 Handler: /go-hello
	http.HandleFunc("/go-hello", func(w http.ResponseWriter, r *http.Request) {
		// 从 header 获取 correlationId
		correlationId := r.Header.Get("X-Correlation-ID")
		if correlationId == "" {
			correlationId = "unknown"
		}

		logger.Info("Received GET /go-hello request",
			zap.String("service", "golang-workshop"),
			zap.String("instance", "golang-workshop-01"),
			zap.String("correlationId", correlationId),
			zap.Any("context", map[string]interface{}{
				"headers": r.Header,
			}),
		)

		// 创建请求并传递 correlationId
		req, _ := http.NewRequest("GET", "http://javaapp:8080/java-hello", nil)
		req.Header.Set("X-Correlation-ID", correlationId)
		javaResp, err := http.DefaultClient.Do(req)
		if err != nil {
			logger.Error("Error calling Java App",
				zap.String("service", "golang-workshop"),
				zap.String("instance", "golang-workshop-01"),
				zap.String("correlationId", correlationId),
				zap.Any("context", map[string]interface{}{
					"error":  err.Error(),
					"target": "javaapp:8080/java-hello",
				}),
			)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Error calling Java: %v", err)
			return
		}
		defer javaResp.Body.Close()

		body, _ := io.ReadAll(javaResp.Body)
		logger.Info("Java responded: "+string(body),
			zap.String("service", "golang-workshop"),
			zap.String("instance", "golang-workshop-01"),
			zap.String("correlationId", correlationId),
			zap.Any("context", map[string]interface{}{
				"response": string(body),
			}),
		)

		// 最終回傳給 Node.js
		fmt.Fprintf(w, "Hello from Golang App + Java says: %s", body)
	})

	port := "4000"
	// 啟動服務時也 Log 一筆
	logger.Info("Golang app listening on port "+port,
		zap.String("service", "golang-workshop"),
		zap.String("instance", "golang-workshop-01"),
	)

	http.ListenAndServe("0.0.0.0:"+port, nil)
}
