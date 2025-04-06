const express = require('express');
const winston = require('winston');
const axios = require('axios');

const app = express();

// 自訂 Winston Format
const customLogFormat = winston.format((info) => {
  if (info.timestamp) {
    // 把 +00:00 => Z (簡化示例)
    info.timestamp = info.timestamp.replace(/\+.*/, 'Z');
  }
  info.level = info.level.toUpperCase();

  if (!info.instance) {
    info.instance = "nodejs-workshop-01";
  }
  if (!info.context) {
    info.context = {};
  }
  return info;
});

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    customLogFormat(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console()
  ]
});

// /node-hello 路由：同時呼叫 Golang
app.get('/node-hello', async (req, res) => {
  // 從 header 獲取 correlationId
  const correlationId = req.headers['x-correlation-id'] || 'unknown';
  
  // 先記錄 Node.js 收到的請求
  logger.info('Received GET /node-hello request', {
    service: 'nodejs-workshop',
    correlationId: correlationId,
    context: { headers: req.headers }
  });

  try {
    // 呼叫 Golang 服務並傳遞 correlationId
    const goResp = await axios.get('http://golang_app:4000/go-hello', {
      headers: { 'X-Correlation-ID': correlationId }
    });

    logger.info(`Golang responded: ${goResp.data}`, {
      service: 'nodejs-workshop',
      correlationId: correlationId,
      // Log the parsed response object
      context: { response: goResp.data }
    });

    // 回傳新的 JSON 結構
    return res.json({
      nodejs_app: "Hello from Node.js!",
      downstream_response: goResp.data // Golang's response is already in the desired nested format
    });
  } catch (err) {
    // Improved error handling
    let errorMessage = 'Error calling Golang';
    let errorDetails = err.message;
    let statusCode = 500;

    if (err.response) {
      // Error from downstream service (Golang)
      errorMessage = `Downstream Golang service error: ${err.response.status}`;
      errorDetails = err.response.data || err.message; // Use response data if available
      statusCode = err.response.status >= 500 ? 500 : 400; // Keep 5xx as 500, map 4xx to 400 (or keep 500 for simplicity)
      // For simplicity as requested earlier, let's stick to 500 for all errors
      statusCode = 500;
    } else if (err.request) {
      // Request made but no response received (e.g., timeout, connection refused)
      errorMessage = 'No response received from downstream Golang service';
    }

    logger.error(errorMessage, {
      service: 'nodejs-workshop',
      correlationId: correlationId,
      context: { error: errorDetails, axios_error_code: err.code }
    });
    // Return standardized error JSON with status 500
    return res.status(statusCode).json({ error: errorMessage, details: errorDetails });
  }
});

// 啟動伺服器
const PORT = 3000;
app.listen(PORT, () => {
  logger.info(`Node.js app listening on port ${PORT}`, {
    service: 'nodejs-workshop'
  });
});
