# 后端设计总览（server）

## 系统上下文（已确认）

- **Spring Boot**：鉴权、任务调度、PostgreSQL、文件路径记录。
- **Python REST**：LAS 读取、滤波算法、预览点云生成；Java 通过 **HTTP** 调用；**超时/重试/轮询** 见 [1.req/requirements.md](../../1.req/requirements.md) v0.2 与 [3.coding/specification.md](../../3.coding/specification.md)。

## 业务域清单

| 域 | 职责 |
|----|------|
| `auth` | 登录与会话（单角色；JWT 见 specification） |
| `job` | 滤波任务生命周期、调度、**comparison-bundle** 聚合（职责边界实现前可微调） |
| `file-metadata` | LAS/产物/预览的元数据与受控下载 |
| `python-gateway` | Python REST 客户端、DTO、错误映射（契约表见 `design-check` 待办与 `integration-python`） |

## 引用

- 各域：`*/delta-check.md`、`component-*.puml`、`*-model`、`*-crud`、`*-api`、（job）`*-workflow-*`
