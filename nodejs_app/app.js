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
      context: { response: goResp.data }
    });

    // 回傳 JSON
    return res.json({
      node_app: "Hello from Node.js!",
      go_response: goResp.data
    });
  } catch (err) {
    logger.error('Error calling Golang', {
      service: 'nodejs-workshop',
      correlationId: correlationId,
      context: { error: err.message }
    });
    return res.status(500).json({ error: err.message });
  }
});

// 啟動伺服器
const PORT = 3000;
app.listen(PORT, () => {
  logger.info(`Node.js app listening on port ${PORT}`, {
    service: 'nodejs-workshop'
  });
});
