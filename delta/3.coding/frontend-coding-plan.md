# 前端编码计划

- **工程**：Vite + React + TypeScript（毕设默认，可改为 CRA）。
- **路由**：React Router；**登录态** 存内存+`sessionStorage` 或 httpOnly Cookie（与后端 JWT 方案一致）。
- **Three.js**：双 `PointCloudViewport`；资源来自 `comparison-bundle` 返回的受控 URL；预览点数上限见 [1.req/requirements.md](../1.req/requirements.md) v0.2。
- **联调顺序**：auth → 创建/查询任务 → comparison-bundle → 文件下载流。
