# 实体说明：点云主流程（pointcloud-pipeline）

## FilterTaskAggregate（PostgreSQL）

| 字段 | 语义 |
|------|------|
| `taskIdUuid` | 业务 PK |
| `ownerUserForeignKeyUuid` | 拥有者账号 |
| `inputLasAbsolutePathRestrictedServerSide` | 仅服务端进程的绝对 LAS 路径（不可透出浏览器原始串）|
| `outputLasAbsolutePathRestrictedServerSide` | 产出 LAS；若走 PCD 预览则并行记录 `FILTERED_PREVIEW` 角色 |

## StoredFileArtifactDescriptor（对齐 file-metadata）

| 枚举 role | path | 示例 |
|-----------|------|------|
| `SOURCE_LAS` | 指向原始归档 | *.las |
| `FILTERED_LAS` | 算法输出 LAS | *.las |
| `SOURCE_PREVIEW` / `FILTERED_PREVIEW` | PLY/PCD LOD | *.ply （后续 Python 滤波附加产物）|

## OfflineFilterJobExecutionSnapshot（对齐将来 Python REST）

嵌入式 JSON blob / 视图字段：`methodToken`=`sor|ror`、`sorK`、`sorStdRatio`、`rorRadius`、`rorMinNeighbors`、`pointCountOriginalInteger`、`pointCountFilteredInteger`、`wallClockSecondsAggregateFloat`、`timingDecodeSeconds`、`timingFilterSeconds`、`timingWriteSeconds`。

与仓库 `python_filter.pipeline.process(...)` metrics dict 对齐（键名可按 snake_case/OpenAPI camelCase 二择一但必须前后端同源）。
