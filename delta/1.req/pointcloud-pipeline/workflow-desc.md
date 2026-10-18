# 流程说明：点云主流程（pointcloud-pipeline）

与 [requirements.md](../requirements.md)、[integration-python/workflow-desc.md](../integration-python/workflow-desc.md) 一致；本节补充 **算法离线阶段**。

## Happy path（端到端）

1. 用户在 Web UI 或使用运维脚本提交 **滤波任务**：注册 **LAS 输入路径 + 产物输出路径前缀**。
2. `job` 域持久化 `FilterTask`，状态迁移 `PENDING`。
3. 调度器在全局 `RUNNING` 配额约束下 **POST `/jobs`** 至 Python REST（占位：当前仓库仍可由人工调用 `python_filter` CLI 验证算法）。
4. Python 异步执行离线管线  
   （当前实现：`laspy chunked read XYZ → kd-tree/SOR/ROR → subset LAS 写回 或 ASCII PCD`）。
5. 成功 → `PythonJobStatusView` 携带 `FILTERED_LAS` 及其它角色路径；Java 回填 `file-metadata`；任务 `SUCCEEDED`。
6. 前端聚合 `comparison-bundle`，双窗口载入 `SOURCE_PREVIEW/FILTER_PREVIEW` **PLY** 资源渲染。

### 离线算法子流程（已实现模块）

```
┌ LAS source path ─► las_io.load_las ─► XYZ float64 Nx3
│                                        │
└────────────── kd-tree neighbours ─────┴──► sor|ror retention mask boolean[N]
                                                  │
subset writer ◄────────────────────── chunked laspy traversal + header copy
                                                  │
filtered LAS / ascii PCD output path ─────────────┘
```

## 度量与日志

离线 CLI 输出的 `N_before / N_after / timing_*` **必须写入** eventual REST `/jobs/{id}` 载荷，供前端展示与论文附图。

## 异常分类（需求粒度）

| 语义 | Java 是否需要重试 | Python 语义 |
|------|------------------|--------------|
| 路径不可读（权限/OS） | 否 | FAILED + `LAS_IO_PATH_UNREADABLE` |
| LAS corrupt / magic | 否 | FAILED + `LAS_PARSE_ERROR` |
| 参数非法（radius<=0 等） | 否 | FAILED + `FILTER_ARGUMENT_INVALID` |
| 点数导致 OOM | 可选人工 | FAILED + `FILTER_OOM`; **不向用户自动重试** |
| Python 崩溃 | 可按 TBD-02 视为可重试 | FAILED + generic `PYTHON_PROCESS_EXIT` |
