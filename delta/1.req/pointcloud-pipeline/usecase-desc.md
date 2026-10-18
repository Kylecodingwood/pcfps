# 用例说明：点云主流程（pointcloud-pipeline）

> 每条用例均需对照 `requirements.md` v0.2 与非功能增补。

## UC-PCF-001 离线验证—SOR 滤波

- **前置**：LAS 可读；单机 RAM 可容纳解码后 XYZ 矩阵（MVP）。
- **主成功流**：
  1. 调用 `PYTHONPATH=. python -m python_filter --input SRC.las --output DST.las --method sor --k 20 --std_ratio 1.0`.
  2. 控制台打印 `N_before/N_after`/耗时；`DST.las` 点数减少且 header 与原文件 point_format 一致。
- **异常**：LAS 破损 → `[las-filter] ERROR` stderr + 退出码≠0。

## UC-PCF-002 离线验证—ROR 滤波

- **主成功流**：`--method ror --radius R --min_neighbors M`。
- **验证**：点数下降或保持（极端分布）但必须无 crash；可按论文附统计表。

## UC-PCF-003 ASCII PCD 导出

- **主成功流**：输出扩展名 `.pcd`。
- **验证**：七点式 header + `DATA ascii`，可用 MeshLab/CloudCompare 打开。

## UC-PCF-004（未来 REST）后端发起滤波作业

待 `python-gateway` OpenAPI & Spring `WebClient` 对接后：**POST /jobs** 等价 CLI 载荷；成功后任务 `RUNNING→SUCCEEDED` 并回填 `FILTERED_LAS`。

## UC-PCF-005（未来）comparison-bundle

成功路径需 **SOURCE_PREVIEW≠FILTER_PREVIEW** — 独立于算法模块，占位。
