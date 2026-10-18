# 附录：PCFPS 核心点云算法源码说明

> 版本：与仓库 `pcfps` 同步；源码内已添加中文注释，可直接复制进 Word/LaTeX 附录。  
> 生成日期：2026-06

---

## 附录结构一览

| 附录编号 | 内容 | 源文件路径 | 行数约 |
|----------|------|------------|--------|
| **附录 A-1** | SOR / ROR 离群点滤波 | `python_filter/filters.py` | 130 |
| **附录 A-2** | LAS 掩码子集写出（保 scale/offset） | `python_filter/las_io.py` → `save_las_subset_by_mask_from_source` | 63–120 |
| **附录 B** | 空间分割（DBSCAN、区域生长） | `python_derived/pipeline.py` → `_run_euclidean_clustering`、`_run_region_growing`、`_write_segment_labels_to_las` | 377–460, 229–253 |
| **附录 C-1** | 地面分类 PMF-lite / CSF-lite | `python_derived/pipeline.py` → `_run_pmf_ground`、`_run_csf_ground` | 486–517 |
| **附录 C-2** | 校园规则四类语义 | `python_derived/pipeline.py` → `_run_rule_semantic_campus` | 70–126 |
| **附录 C-3** | 语义精简（删 3/4 + 地面体素） | `python_derived/pipeline.py` → `_run_semantic_prune` | 150–226 |
| **附录 C-4** | RF 有监督语义（特征 + 推断） | `python_rf_semantic/geometry_features.py`、`python_rf_semantic/infer_core.py` | 全文 |
| **附录 C-5**（可选） | 派生任务总入口 | `python_derived/pipeline.py` → `process_derived` | 256–374 |

大文件 **XY 分块滤波**（非 Web 默认路径）见 `python_filter/tiled_pipeline.py`，正文/摘要若单独论述分块可另列 **附录 A-3**。

---

## 依赖与环境

| 库 | 用途 |
|----|------|
| `numpy` | 点坐标与掩码 |
| `laspy` | LAS/LAZ 读写 |
| `scipy.spatial.cKDTree` | SOR k 近邻 |
| `sklearn.neighbors.BallTree` | ROR 半径查询 |
| `sklearn.cluster.DBSCAN` | 欧式聚类 |
| `sklearn.neighbors.NearestNeighbors` | 区域生长 / 平面度 |
| `sklearn.ensemble.RandomForestClassifier` | RF 语义（`train_cli.py`） |
| `scipy.ndimage` | PMF/CSF 格网滤波 |

---

## 附录 A：离群点滤波

### A-1 算法摘要

**SOR（统计离群点去除）**

1. 建 cKDTree，每点求 k 近邻平均距离 \(\bar d_i\)。
2. 全云 \(\bar d\) 的均值 \(\mu\)、标准差 \(\sigma\)。
3. 保留 \(\bar d_i \le \mu + \text{std\_ratio} \cdot \sigma\) 的点。

**ROR（半径离群点去除）**

1. BallTree 统计半径 `radius` 内点数，减 1 得邻点数。
2. 邻点数 ≥ `min_neighbors` 则保留。

### A-2 LAS 写出

`save_las_subset_by_mask_from_source` **复制源 header**，按掩码流式写点，保证 **比例尺与平移量不变**（laspy 自动处理 int×scale+offset）。

---

## 附录 B：空间分割

| 算法 | 标识 | 说明 |
|------|------|------|
| 欧式聚类 | `euclidean_cluster` | DBSCAN，`eps=cluster_tolerance` |
| 区域生长 | `region_growing` | kNN 法向 + 距离/夹角 BFS |

输出：`classification` 存簇号（0 噪声）；`user_data` 可选存 0–255 完整簇 id。

---

## 附录 C：分类与语义精简

### 语义标签约定（规则 / RF 一致）

| classification | 含义 |
|----------------|------|
| 1 | 地面 |
| 2 | 建筑 |
| 3 | 植被 |
| 4 | 其它 |

### C-1 地面二分类

- **PMF-lite**：格网 min-Z + 形态学最小值滤波 → 高程残差阈值。
- **CSF-lite**：简化布料下沉 → 与布高差阈值。

### C-2 校园规则语义

PMF 地面 → 非地面用 **平面度 + Z 标准差** 规则划分 2/3/4。

### C-3 语义精简

- 删除 class 3、4；
- class 2 全保留；
- class 1 在 XY 上 `ground_voxel_size_m`（默认 0.5 m）体素，**每格最低 Z 一点**；
- `compression_ratio = n_input / n_output`。

### C-4 RF 语义

- 训练：`python_rf_semantic/train_cli.py`，标注 LAS 见 `terra_las/cloud_house_language.las`。
- 特征 4～5 维：PMF 残差、平面度、Z_std、PMF 地面标志、（可选）强度。
- 推断：`apply_rf_semantic_to_las`。

---

## 导出为单一文本（便于粘贴 Word）

在仓库根目录执行：

```bash
cd /Users/kyle/Documents/点云毕设/pcfps

cat > docs/thesis/appendix_merged_source.txt << 'EOF'
========== 附录 A-1 python_filter/filters.py ==========
EOF
cat python_filter/filters.py >> docs/thesis/appendix_merged_source.txt

echo "" >> docs/thesis/appendix_merged_source.txt
echo "========== 附录 A-2 python_filter/las_io.py (save_las_subset) ==========" >> docs/thesis/appendix_merged_source.txt
sed -n '63,120p' python_filter/las_io.py >> docs/thesis/appendix_merged_source.txt

echo "" >> docs/thesis/appendix_merged_source.txt
echo "========== 附录 B/C python_derived/pipeline.py ==========" >> docs/thesis/appendix_merged_source.txt
cat python_derived/pipeline.py >> docs/thesis/appendix_merged_source.txt

echo "" >> docs/thesis/appendix_merged_source.txt
echo "========== 附录 C-4 python_rf_semantic/geometry_features.py ==========" >> docs/thesis/appendix_merged_source.txt
cat python_rf_semantic/geometry_features.py >> docs/thesis/appendix_merged_source.txt

echo "" >> docs/thesis/appendix_merged_source.txt
echo "========== 附录 C-4 python_rf_semantic/infer_core.py ==========" >> docs/thesis/appendix_merged_source.txt
cat python_rf_semantic/infer_core.py >> docs/thesis/appendix_merged_source.txt
```

合并结果：`docs/thesis/appendix_merged_source.txt`。

---

## LaTeX 引用示例

```latex
\appendix
\chapter{SOR与ROR滤波核心代码}
\lstinputlisting[language=Python, caption={统计/半径离群点滤波}]{python_filter/filters.py}

\chapter{分割与分类派生算法}
\lstinputlisting[language=Python]{python_derived/pipeline.py}
```

（将路径改为相对论文工程或绝对路径。）

---

## 与 Web 系统关系（正文可简述，附录不必展开）

```
原始 LAS → filters.py (SOR/ROR) → filtered.las
         → pipeline.py segment → segmented.las
         → pipeline.py classify → classified.las
         → pipeline.py semantic_prune → pruned.las
```

Spring Boot / FastAPI 仅调度上述 Python 模块；浏览器展示抽稀预览 JSON，全量指标见任务 `runMetrics` / `derivedMetrics`。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-06 | 源码增加中文注释；初版附录索引 |
