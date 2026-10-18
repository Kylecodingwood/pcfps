# 域内核对：auth（附录 F 骨架）

## 基准摘要

- 触发源：浏览器登录请求。
- **令牌**：**Bearer JWT**（与 [3.coding/specification.md](../../../3.coding/specification.md) 一致）。
- 核心能力：认证、签发访问令牌、（可选）刷新策略由实现定稿。

## 流程/架构一致性

- 无独立 workflow 目录：**无 timer / 无 workflow**（除非后续加会话清理定时任务）。

## 逐项核对

| 检查项 | 状态 | 说明 |
|--------|------|------|
| model / crud / api 与 `component-auth.puml` 对齐 | ⬜ | |
| 实体覆盖 API 请求/响应 | ⬜ | |
| UC → API 可闭环 | ⬜ | |

## 结论

骨架阶段；路径与 DTO 见 `auth-api/delta.md`。
