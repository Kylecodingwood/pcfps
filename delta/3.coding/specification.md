# 横切实现规约（specification）

> 与 [1.req/requirements.md](../1.req/requirements.md) v0.2 **决议草案**对齐；冲突时以需求为准并回写 `design-check.md`。

## API

- **版本**：URL 前缀 `/api/v1`（可调整，全项目一致即可）。
- **错误体**：JSON `{ "code": string, "message": string, "traceId": string }`；`code` 为稳定业务/系统码（文档维护枚举表）。
- **分页**：与 **Spring Data** 默认对齐：`page`（0-based）、`size`；响应字段 `content`、`totalElements`（或 `Page` JSON 惯例）。
- **聚合接口**：`GET /api/v1/tasks/{taskId}/comparison-bundle` — 返回双窗口所需元数据与受控资源引用（见 [requirements.md](../1.req/requirements.md) v0.2 双窗口节）。
- **文件下载**：`GET /api/v1/files/{fileId}/content` — 校验归属后流式返回磁盘文件（不暴露绝对路径给未授权方）。
- **预览点 JSON**：`POST /api/v1/files/{fileId}/preview-points` — 请求体 JSON（如 `{"maxPoints":12000}` 或 `{}` 用服务端默认）；响应为服务端解码并抽稀后的点集，供 Web 渲染。LAS/LAZ 依赖运行时 **Python3 + laspy**（脚本见 `backend` 资源）；ASCII PLY 由 Java 解析。错误码示例：`PREVIEW_FILE_TOO_LARGE`（413）、`LAS_PREVIEW_FAILED`（503）、`PREVIEW_UNSUPPORTED_FORMAT`（400）。详见 [`backend/README.md`](../../backend/README.md)。
- **路径预览（无 FileAsset）**：`POST /api/v1/preview/las-path` — body `{"lasPath":"/abs/path.las","maxPoints":…}`；`POST /api/v1/preview/las-path/dual` — body `{"sourceLasPath":"…","filteredLasPath":"…","maxPoints":…}`。路径须为 **绝对路径** 且规范化后为 **普通文件**（扩展名 las/laz/ply）；需 **JWT**；无输出根前缀限制（与建任务填绝对路径同一信任模型）。用于预览页「仅填服务器路径」模式；任务内对比仍以 **fileId + preview-points** 为主。
- **幂等**：任务创建可使用 `Idempotency-Key` 请求头（UUID）；重复提交返回同一任务（实现可选，文档先占位）。

## 安全

- **鉴权**：**Bearer JWT**（毕设默认）；访问聚合与下载接口必须带有效令牌。
- **敏感配置**：数据库、JWT 密钥、Python 基址等仅 **环境变量** 或外部配置，**禁止**提交仓库。
- **下载与预览**：浏览器不接收服务器绝对路径；使用 **受控路径**（`GET /api/v1/files/{fileId}/content`）与 **预览 JSON**（`POST /api/v1/files/{fileId}/preview-points`）由服务端校验 JWT 与 `file_asset` 归属后再读盘。路径型预览接口在 **可信部署** 下由服务端在校验 JWT 后按 **绝对路径 + 普通文件** 读盘（与任务路径输入同一模型，不宜对公网开放）。

## 数据

- **迁移**：仅 DDL/结构；**种子/演示数据** 独立脚本或 `spring.sql.init` 分环境开关（与用户规则一致）。

## 并发与一致

- **任务状态**：更新任务状态时采用 **乐观锁**（`version` 列）或等价机制，避免并发调度写乱状态。
- **全局并行**：RUNNING 上限默认 **1**（配置可 2），与调度器一致。
- **重复提交**：若实现 `Idempotency-Key`（请求头 UUID），相同键返回已有任务；否则依赖前端防抖 + 可选 DB 唯一约束（如 `(user_id, input_asset_id)` 实现阶段定是否启用）。

## 可靠性

- **Python REST**（与 [requirements.md](../1.req/requirements.md) v0.2 任务失败与重试节一致）：
  - 连接超时 **5s**；提交读超时 **60s**；状态查询读超时 **15s**。
  - 网络/5xx/超时：**最多 3 次** 重试，间隔 **1s / 2s / 4s**；**4xx** 不重试。
- **熔断**：毕设可选；未上前在日志中显式记录连续失败次数。

## 可观测性

- **traceId / requestId**：每个 HTTP 请求生成并放入日志 MDC；错误响应带回 `traceId`。
- **业务键**：日志中记录 **taskId**、（若有）**externalPythonJobId**。

## 配置

- **清单**（示例）：`SPRING_DATASOURCE_*`、`JWT_SECRET`、`PYTHON_SERVICE_BASE_URL`、`FILTER_MAX_CONCURRENT_RUNNING`、`pcfps.preview.*`（`PCFPS_PREVIEW_MAX_POINTS`、`PCFPS_PREVIEW_PYTHON`、`PCFPS_PREVIEW_LAS_ENABLED`、`PCFPS_PREVIEW_PROCESS_TIMEOUT_SEC` 等，见 [`backend/README.md`](../../backend/README.md)）；环境差异写在 `README` 或部署说明。

## Python 离线滤波模块交付规约（仓库 `python_filter/`）

用于 **Spring Boot Mock 仍为默认**阶段的算法真值底座；下一阶段由薄 FastAPI/shim 封装相同 `process(...)`。

- **源码树**：[`python_filter/`](../../python_filter/)（顶层包名 `python_filter`）。
- **依赖锁定**：参见 [`python_filter/requirements.txt`](../../python_filter/requirements.txt) — `numpy`, `laspy`, `scipy`, `scikit-learn`。
- **执行入口**：
  - `PYTHONPATH=. python -m python_filter --input SRC.las --output DST{.las|.laz|.pcd}`。
  - 亦可在集成测试中 `from python_filter import process`.
- **退出码**：`0` 成功；`1` 任何未捕获异常 / 校验失败。`stderr` 单行前缀 `[las-filter] ERROR:` 便于抓取。
- **指标字段 JSON 对齐**：HTTP 封装时应将离线 dict 映射为 camelCase：`N_before → originalPointRowCount`、`N_after → filteredPointRowCount`、`timing_*` 同上；保持 **单一枚举源**。（当前 Python dict 仍为论文友好 PascalCase/snake_mix — 网关层映射。）
