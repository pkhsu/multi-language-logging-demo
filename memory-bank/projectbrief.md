# 專案概述

## 目標
在Kubernetes (Microk8s)環境中實現多語言應用的統一結構化日誌管理

## 核心需求
1. 標準化JSON日誌格式
2. 跨語言一致性
3. 高效能日誌收集
4. 敏感資訊保護

## 日誌規範
| 欄位名稱 | 說明 | 範例 |
|----------|------|------|
| timestamp | ISO8601格式, UTC | 2025-03-11T10:20:30Z |
| level | 日誌級別 | DEBUG, INFO, WARN, ERROR |
| service | 服務名稱 | order-service |
| instance | 服務實例或Pod ID | order-service-01 |
| correlationId | 跨服務追蹤ID | abc123xyz |
| message | 日誌訊息 | Order created |
| context | 附加上下文 | {"orderId":"ORD123"} |

## 技術要求
- 支援Python/Java/Node.js/Golang
- 輕量級實現
- 與Kubernetes日誌收集系統整合
