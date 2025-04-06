# 技術上下文更新 - 2025-04-04

## 日誌系統架構
- 使用Grafana + Loki + Promtail實現集中式日誌管理
- 所有微服務日誌通過Promtail收集並發送到Loki
- Grafana作為日誌可視化界面

## Python Loguru App配置
- 日誌格式：純JSON輸出
- 必需字段：
  - timestamp: ISO 8601格式
  - level: 日誌級別
  - service: 服務名稱
  - correlationId: 請求追蹤ID
  - message: 日誌消息
  - context: 上下文信息

## Promtail配置
- 自動提取correlationId作為標籤
- 支持多種ID字段格式(correlationId/correlation_id/trace_id)
- 過濾無效correlationId的日誌
