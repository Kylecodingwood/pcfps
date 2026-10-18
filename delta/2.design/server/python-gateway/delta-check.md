# 域内核对：python-gateway（附录 F 骨架）

## 基准摘要

- 触发源：`job` 服务、调度器。
- 核心能力：**HTTP 客户端**、DTO、错误映射；**超时与重试** 见 `python-gateway-crud/delta.md` 与 `specification.md`（与需求 v0.2 一致）。
- 下游：外部 **Python REST**。

## 流程/架构一致性

- 无用户向 workflow；重试在 client 层实现。

## 与外部系统

- 契约已与 `1.req/integration-python/` 表格字段对齐；OpenAPI YAML 仍待导出。
- 算法行为与仓库 `python_filter/` CLI smoke 测试结果一致：`N_*` / 分段 timings 字段存在。

## 结论

见 `python-gateway-crud/delta.md`、`python-gateway-model/delta.md`。
