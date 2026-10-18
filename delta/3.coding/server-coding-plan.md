# 后端编码计划

- **模块**：单模块 Spring Boot 或父 POM 多模块；包前缀与 [README.md](README.md) 域表一致。
- **PostgreSQL**：`backend/db/schema/init_schema.sql` 建表；种子数据独立脚本 `db/seed/`（见 `specification.md`）。
- **python-gateway**：`WebClient` 或 `RestTemplate` + `PYTHON_SERVICE_BASE_URL`；超时/重试见 `specification.md`。算法真值：`python_filter` →（后续）HTTP thin-wrapper。
- **调度**：毕设默认 **Spring `@Scheduled`** 推进 PENDING 与轮询 RUNNING；Quartz 仅在有复杂 Cron 需求时引入。
- **测试**：服务层单测（Mockito）；新增「算法 CLI 冒烟」脚本（可选 GitHub Actions `matrix: python 3.10`）；一条集成测覆盖「创建任务 → Mock Python → 状态变迁」，后续升级为「真实嵌入式 Python 容器」契约测可选。

## Milestone 增补（2026-05）

1. ✅ CLI 冒烟：随机 LAS 小样（CI 可选用固定 fixture）。
2. ✅ **Web 预览 JSON**：`POST /api/v1/files/{fileId}/preview-points`（包 `com.pcfps.preview` + classpath `las_preview_sample.py`）；详见 [`backend/README.md`](../../backend/README.md) 与 [3.coding/README.md](README.md)。
3. ☐ FastAPI 包装 `/jobs`、`/jobs/{id}` — DTO mirror `integration-python`.
4. ☐ `PythonGatewayWebClientBean` stub → 实装。
