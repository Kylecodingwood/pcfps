# 域内核对：job（附录 F 骨架）

## 基准摘要

- 触发源：用户创建任务 API、**调度器**（Spring `@Scheduled` 为毕设默认，见 `server-coding-plan.md`）。
- 核心能力：任务 CRUD、状态迁移、调用 `python-gateway`、组装 **comparison-bundle**。
- 下游：PostgreSQL、`python-gateway`。

## 流程/架构一致性

- `job-workflow-filter` 与 [1.req/requirements.md](../../../../1.req/requirements.md) v0.2 及 `workflow-job-filter.puml` 一致。

## 逐项核对

| 检查项 | 状态 |
|--------|------|
| model / crud / api / workflow 与 `component-job.puml` 对齐 | ⬜ |

## 结论

见 `job-api/delta.md`、`job-workflow-filter/delta.md`。
