# 设计总检（design-check）

> 对照规范附录 C：跨域缺口、未覆盖 UC、与外部系统（Python REST）未对齐点。

## 与需求对齐（`1.req/requirements.md` v0.2）

以下项已在需求 **决议草案** 中落地，设计实现须与之一致或显式记录偏差：

- **TBD-01**：参数在 Python 配置侧；Java 不传参字典。
- **TBD-02**：REST 轮询、超时与重试策略、FAILED 落库。
- **TBD-03**：全局 RUNNING=1（可配 2）、FIFO PENDING。
- **TBD-04**：无自助注册；预置/手工账号。
- **TBD-05**：聚合接口 `comparison-bundle`（路径名可调整）、预览点数上限 500k、单级 LOD。
- **TBD-06**：无 SLA、日志与密钥、路径不直出浏览器。

## 仍须在设计与契约中细化的项

1. **Python REST 契约**：具体 path、JSON 字段名、错误码枚举 — 在 `server/python-gateway/` 与 `1.req/integration-python/` 用 OpenAPI 或表格定稿。
2. **comparison-bundle 响应模型**：字段列表与 `file-metadata` / `job` 聚合方式 — 在 `job-api` 或独立 BFF 域定稿（当前草案归 `job` 或 `file-metadata` 之一，实现前二选一）。
3. **任务状态机**：`job-workflow-filter` 须与需求中 PENDING/RUNNING/FAILED/SUCCEEDED（及超时）一致。
4. **UC 编号与矩阵**：`pages.md`、各 `usecase-desc.md` 仍待冻结 UC 后勾选。

## 待办

- [ ] 冻结 UC 后更新本列表并消解缺口
- [ ] 各域 `delta-check.md` 与 `component-*.puml` 对齐后复核
