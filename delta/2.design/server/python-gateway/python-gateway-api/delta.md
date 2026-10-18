# python-gateway-api

> 说明：本域为 **Java 进程 → Python 算法服务（HTTP）** 的 **内部集成 API**；浏览器不直连。  
> 路径与 JSON 键名可随 OpenAPI 正式发布调整，但语义需与 `python_filter` CLI 等价。

## REST 契约（草案）

| 端点 | 方法 | 语义 | 关键请求体 | 关键响应 |
|------|------|------|------------|-----------|
| `/jobs` | `POST` | 创建异步滤波作业 | `PythonJobSubmissionPayloadContract`（参见 `1.req/integration-python/entity.md`） | `202` + `{ "external_python_job_uuid": UUID }` |
| `/jobs/{externalPythonJobUuid}` | `GET` | 轮询执行状态 | path param | `{ "lifecycle_state_machine_token": "...", "metrics_bundle": { ... }, "artifact_path_dictionary": { ... }}}` |

## 错误语义

对齐 `3.coding/specification.md`：HTTP layer 映射到 `{code, message, traceId}`；算法业务错误建议使用稳定 `error_code`：`FILTER_PAYLOAD_INVALID`、`LAS_IO_PATH_UNREADABLE`、`LAS_PARSE_ERROR`、`FILTER_ARGUMENT_INVALID`、`FILTER_OOM`。

## TLS / Host

默认 **内网 http://python:8000/**；生产可加 mTLS——毕设省略。
