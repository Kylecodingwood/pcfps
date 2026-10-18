# job-api

> 与 [1.req/requirements.md](../../../../1.req/requirements.md) v0.2、`3.coding/specification.md` 对齐。

## REST（草案）

| 说明 | 方法 | 路径（示例） | 备注 |
|------|------|----------------|------|
| 创建滤波任务 | POST | `/api/v1/tasks` | 请求体含输入 LAS 逻辑引用/ID；**扩展（2026-05）**：可携带 `filterMethod` 及 SOR/ROR 参数（UI 仍不调参，由前端写死或后端默认模板下发）；可选 `Idempotency-Key` |
| 查询任务详情 | GET | `/api/v1/tasks/{taskId}` | 含状态、错误信息、关联文件 ID |
| 任务列表（可选） | GET | `/api/v1/tasks` | 分页，见 specification |
| 双窗口聚合 | GET | `/api/v1/tasks/{taskId}/comparison-bundle` | 返回原始/结果/预览元数据与受控下载引用 |

前端 `pointcloud-comparison/api.md` 应与本表一致。
