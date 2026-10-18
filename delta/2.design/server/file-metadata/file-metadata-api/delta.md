# file-metadata-api

> 与 [1.req/requirements.md](../../../../1.req/requirements.md) v0.2（路径安全、comparison-bundle）、`job-api/delta.md` 对齐。

## 职责（草案）

- **登记**：任务完成或上传完成后写入 **FileAsset**（逻辑名、存储键、类型：SOURCE_LAS / FILTERED_LAS / PREVIEW 等）。`FILTERED_LAS` 主要来自 `python_filter` subset 写回路径；若仅生成预览 PCD，可降级登记为 `FILTERED_PREVIEW`（与根 README 「PLY 预览」章节一致）。
- **查询**：按 `taskId` 列出关联资产；供 **comparison-bundle** 组装响应。
- **下载**：对外通过 **受控接口** 输出流（见 `3.coding/specification.md`），响应中不暴露服务器绝对路径。

## 与前端

- `pointcloud-comparison/api.md` 中的文件 URL 与本域及 job 聚合契约一致。
