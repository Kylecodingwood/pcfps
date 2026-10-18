# job-model

> 与 [1.req/requirements.md](../../../../1.req/requirements.md) v0.2、`job-workflow-filter` 一致。

## 实体要点（草案）

- **FilterTask**（名称可调整）：`id`、`status`（PENDING/RUNNING/SUCCEEDED/FAILED）、`externalPythonJobId`（可空）、错误信息、时间戳、与输入文件引用关联。
- 与 `file-metadata`：**一对多** 资产（SOURCE / FILTERED / PREVIEW）通过 `taskId` 关联。
