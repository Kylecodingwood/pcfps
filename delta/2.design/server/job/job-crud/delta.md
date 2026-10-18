# job-crud

> 与 [1.req/requirements.md](../../../../1.req/requirements.md) v0.2、[3.coding/specification.md](../../../../3.coding/specification.md) 一致。

## 服务能力（草案）

- 创建任务、按 ID 查询、列表分页、更新状态（调度器与 Python 轮询路径调用）。
- **事务**：创建任务与初始元数据写入同事务（边界实现时定稿）。
- **并发**：任务行 **乐观锁**（`version`）与全局 RUNNING 上限协同。
