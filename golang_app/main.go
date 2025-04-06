package main

import (
	"encoding/json" // Import encoding/json
	"fmt"
	"io"
	"net/http"
	"time"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

// Define response structure for success
type SuccessResponse struct {
	GolangApp          string      `json:"golang_app"`
	DownstreamResponse interface{} `json:"downstream_response"`
}

// Define response structure for error
type ErrorResponse struct {
	Error   string `json:"error"`
	Details string `json:"details,omitempty"`
}

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
		// Helper function for sending JSON error response
		sendError := func(statusCode int, errMsg string, details string) {
			logger.Error(errMsg, // Log the primary error message
				zap.String("service", "golang-workshop"),
				zap.String("instance", "golang-workshop-01"),
				zap.String("correlationId", r.Header.Get("X-Correlation-ID")), // Get correlationId again for safety
				zap.Any("context", map[string]interface{}{
					"error_details": details,
				}),
			)
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(statusCode)
			json.NewEncoder(w).Encode(ErrorResponse{Error: errMsg, Details: details})
		}

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
		req, err := http.NewRequest("GET", "http://javaapp:8080/java-hello", nil)
		if err != nil {
			sendError(http.StatusInternalServerError, "Failed to create request for Java service", err.Error())
			return
		}
		req.Header.Set("X-Correlation-ID", correlationId)

		javaResp, err := http.DefaultClient.Do(req)
		if err != nil {
			sendError(http.StatusInternalServerError, "Failed to call downstream Java service", err.Error())
			return
		}
		defer javaResp.Body.Close()

		// Read Java response body
		body, err := io.ReadAll(javaResp.Body)
		if err != nil {
			sendError(http.StatusInternalServerError, "Failed to read downstream Java response", err.Error())
			return
		}

		// Check Java status code
		if javaResp.StatusCode != http.StatusOK {
			errMsg := fmt.Sprintf("Downstream Java service returned error status %d", javaResp.StatusCode)
			// Log the error with body for context
			logger.Error(errMsg,
				zap.String("service", "golang-workshop"),
				zap.String("instance", "golang-workshop-01"),
				zap.String("correlationId", correlationId),
				zap.Any("context", map[string]interface{}{
					"status_code": javaResp.StatusCode,
					"response_body": string(body),
				}),
			)
			sendError(http.StatusInternalServerError, "Downstream Java service error", string(body))
			return
		}

		// Parse Java JSON response
		var javaJsonResponse map[string]interface{} // Use interface{} for flexibility
		err = json.Unmarshal(body, &javaJsonResponse)
		if err != nil {
			// Log the error with body for context
			logger.Error("Error unmarshalling Java JSON response",
				zap.String("service", "golang-workshop"),
				zap.String("instance", "golang-workshop-01"),
				zap.String("correlationId", correlationId),
				zap.Any("context", map[string]interface{}{
					"error":           err.Error(),
					"response_body": string(body),
				}),
			)
			sendError(http.StatusInternalServerError, "Invalid JSON response from downstream Java service", err.Error())
			return
		}

		// Log successful Java response
		logger.Info("Java responded successfully",
			zap.String("service", "golang-workshop"),
			zap.String("instance", "golang-workshop-01"),
			zap.String("correlationId", correlationId),
			zap.Any("context", map[string]interface{}{
				"response": javaJsonResponse, // Log the parsed map
			}),
		)

		// Construct and send Go JSON response
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK) // Explicitly set OK status
		response := SuccessResponse{
			GolangApp:          "Hello from Golang App",
			DownstreamResponse: javaJsonResponse,
		}
		err = json.NewEncoder(w).Encode(response)
		if err != nil {
			// Log encoding error, but can't send another response header here
			logger.Error("Error encoding success response",
				zap.String("service", "golang-workshop"),
				zap.String("instance", "golang-workshop-01"),
				zap.String("correlationId", correlationId),
				zap.Any("context", map[string]interface{}{
					"error": err.Error(),
				}),
			)
		}
	})

	port := "4000"
	// 啟動服務時也 Log 一筆
	logger.Info("Golang app listening on port "+port,
		zap.String("service", "golang-workshop"),
		zap.String("instance", "golang-workshop-01"),
	)

	http.ListenAndServe("0.0.0.0:"+port, nil)
}
