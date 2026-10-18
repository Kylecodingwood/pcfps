# API：pointcloud-comparison

> 与 `2.design/server` 及 [1.req/requirements.md](../../../../1.req/requirements.md) v0.2 对齐。

## 本页调用（草案）

| 说明 | 方法 | 路径 | 域 |
|------|------|------|-----|
| 登录 | POST | `/api/v1/auth/login`（示例） | auth |
| 当前用户/会话 | GET | `/api/v1/auth/me`（可选） | auth |
| 双窗口聚合数据 | GET | `/api/v1/tasks/{taskId}/comparison-bundle` | job（或 BFF，与 `job-api/delta.md` 一致） |
| 受控文件流/签名下载 | GET | `/api/v1/files/...` 或响应内嵌 URL | file-metadata / 网关 |

## 响应要点（comparison-bundle）

- 含 **原始 LAS**、**滤波输出**、**预览** 的元数据（文件名、大小、MIME、**非**服务器绝对路径）。
- 浏览器通过返回的 **受控 URL** 或 token 化引用加载 Three.js 资源；预览点数与 LOD 见 [requirements.md](../../../../1.req/requirements.md) v0.2（默认 500k、单级 LOD）。
