# auth-api

> 与 [3.coding/specification.md](../../../../3.coding/specification.md)、前端 `pointcloud-comparison/api.md` 对齐。

## REST（草案）

| 说明 | 方法 | 路径（示例） |
|------|------|----------------|
| 登录 | POST | `/api/v1/auth/login` |
| 当前主体（可选） | GET | `/api/v1/auth/me` |

## 响应与安全

- 登录成功返回 **JWT**；后续请求 `Authorization: Bearer <token>`。
- 错误体格式见 `specification.md`。
