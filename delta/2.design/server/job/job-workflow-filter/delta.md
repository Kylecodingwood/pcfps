# job-workflow-filter

> 与 [1.req/requirements.md](../../../../1.req/requirements.md) v0.2 一致。

## 状态与事件（草案）

| 状态 | 含义 |
|------|------|
| PENDING | 已创建，等待调度（FIFO；受全局 RUNNING 上限约束） |
| RUNNING | 已提交 Python 且处理中（或轮询显示进行中） |
| SUCCEEDED | Python 成功，输出与预览路径已登记 |
| FAILED | 业务失败、不可重试错误、或超时/重试耗尽 |

## 迁移（与 `workflow-job-filter.puml` 一致）

- PENDING → RUNNING：调度器出队且 `submitJob` 成功（或收到 Python 已接受响应）。
- RUNNING → SUCCEEDED：`fetchStatus` 表明完成且文件元数据写入成功。
- RUNNING → FAILED：Python 4xx 业务错误、明确失败状态、或超时策略触发。
- PENDING 不直接 FAILED：除非创建即非法参数（校验失败）。

## 角色

- **调度器**（Spring `@Scheduled` 或等价）：推进 PENDING → RUNNING、轮询 RUNNING。
- **用户**：通过 API 创建任务、查询状态；不直接触发 Python。
