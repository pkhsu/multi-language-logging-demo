# 技術上下文

## 技術棧
| 組件 | 技術選擇 |
|------|----------|
| 日誌收集 | Fluentd |
| 日誌存儲 | Elasticsearch |
| 可視化 | Kibana |
| 監控告警 | Prometheus + Alertmanager |

## 各語言實現方案
### Python
- 標準庫: `logging` + `python-json-logger`
- 替代方案: `loguru`
- 關鍵配置: 自訂JSON格式器

### Java
- 框架: `logback` + `logstash-logback-encoder`
- 配置: `logback-spring.xml`
- 特性: 支援MDC上下文

### Node.js
- 庫: `winston`
- 配置: 自訂JSON格式
- 特性: 多transport支持

### Golang
- 庫: `zap`
- 配置: 高性能JSON編碼
- 特性: 結構化日誌原生支持

## 開發環境
- Kubernetes: Microk8s
- 本地開發: Docker Compose
- 日誌收集: 本地Filebeat

## 依賴管理
- Python: requirements.txt
- Java: Maven (pom.xml)
- Node.js: package.json
- Golang: go.mod
