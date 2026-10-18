# 前端页面总览

## 信息架构

| 页面 slug | 路径（建议） | 说明 | 关联 UC |
|-----------|--------------|------|---------|
| pointcloud-comparison | `/compare/:taskId`（示例） | React + Three.js 双窗口点云对比 | 待 `1.req` UC 编号 |

## 需求跟踪矩阵（UC ↔ 页面）

| UC 编号 | 页面 | 状态 |
|---------|------|------|
| 待编 | `pointcloud-pipeline/pointcloud-comparison/` | 用例冻结后填写 |

## 与 server 域关系

- **auth**：登录与会话 API（JWT，见 `3.coding/specification.md`）。
- **job**：任务创建、状态查询、**comparison-bundle**。
- **file-metadata**：资产元数据与受控下载；由 bundle 或专用文件接口暴露。
- **python-gateway**：不直接对浏览器；经 Java 聚合。

## 权威需求

- 双窗口数据形态与接口名：[1.req/requirements.md](../../1.req/requirements.md) v0.2。
