# `cloud_17999bae.las` — PCFPS 功能试参指南

本文基于对仓库内数据 **`terra_las/cloud_17999bae.las`**（与 `点云毕设/terra_las/` 下同名文件一致）的实测统计，结合当前后端 / `python_gateway` / `python_derived` / `python_filter` 实现整理。请按章节**逐项试参**，确认现象后再微调。

---

## 1. 数据档案（分析结论）

| 项目 | 数值 / 说明 |
|------|-------------|
| 路径（仓库内） | `terra_las/cloud_17999bae.las` |
| 点数 | **88 718 138** |
| LAS 点格式 | **Format 3**（含 `red/green/blue`、`classification`、`gps_time`、`return_number` 等） |
| `classification` | **全部为 0**（未分类），属原始/通用 LAS |
| 水平范围 (X×Y) | 约 **669.5 m × 690.1 m** |
| 垂直范围 (Z) | 约 **103.6 m**（整体为一片大场景 campus 尺度） |
| 水平点密度（粗算） | 约 **190 pts/m²**（全幅平均） |
| 典型邻点间距（单文件流式块内 50 万点、子采样估计） | 最近邻中位数约 **0.09 m**，P95 约 **0.22 m**（**厘米级**稠密） |
| 回波 | `return_number` 主要为 **1、2** |
| 强度（流式抽样 1 万点） | 约 P5=9 / P50=19 / P95=37（数值低、动态范围不大，一般不作为主滤波依据） |
| RGB | **有**，预览「真彩色」可用 |

**重要约束（与「系统完全正确」强相关）：**

1. **全量 8870 万点**时，`python_derived` 使用 `laspy.read()` **整文件进内存**；`python_gateway` 的滤波 `process()` **默认不启用分块**（未传 `tile_size`），同样是整文件策略。机器内存不足时会 OOM 或极慢，**这不属于参数错，属于数据规模与管线策略**。
2. 若要先验证流程正确性，建议另存 **抽稀 / 裁切子区** 的 `.las`/`.laz` 做回归；本指南参数仍以**当前全幅几何尺度（百米级 Z、百米级 XY 间距）**为参照，子区可按比例缩放距离类参数。

---

## 2. 环境与预览（所有功能共用）

| 参数 | 作用位置 | 建议先试 | 说明 |
|------|-----------|----------|------|
| `VITE_API_BASE_URL` | 前端 `.env` | `http://localhost:8080` | 与后端网关一致 |
| `PCFPS_PREVIEW_MAX_POINTS` / `application.yml` 的 `pcfps.preview.max-points-default` | 预览抽稀上限 | **180000**（默认） | 全幅 8870 万点下预览必为抽稀；要更密可升到 300k～500k，**内存与接口耗时上升** |
| 前端双窗「预览点数上限」滑条 | `PreviewDualPage` | 180000 → 再升 | 与上项同一语义；过大浏览器易卡 |
| 路径预览 / 双窗路径 | 请求体 `maxPoints` | 与上保持一致 | 路径 LAS 若指向本文件，同上 |

---

## 3. 新建滤波任务（SOR）

**API / 向导 → 合并后 Python 键（网关体字段名见 Spring DTO）：** `sor_neighbor_count`（→ 网关里映射为 SOR 的 `k`）、`sor_std_ratio`（→ `std_ratio`）。

| 参数 | 默认（代码） | 针对本数据建议先试 | 调参方向 |
|------|--------------|---------------------|----------|
| `sor_neighbor_count`（k） | 20 | **24～32** | 邻域约 9～22 cm 间距；k 过小易受单点噪声影响，过大则平滑过强、细节损失 |
| `sor_std_ratio` | 1.0 | **1.0 → 1.2**（保守） / **0.8～0.9**（更狠去噪） | 强度不高、结构以几何为主：略放宽 std 比盲目加 k 更稳 |

**建议试参顺序：** 固定 `std_ratio=1.0`，令 `k = 20 → 28 → 36` 各跑一次，看离群点与建筑边缘；再固定满意 k，扫 `std_ratio`。

**离线大文件（推荐）：** 使用 `python -m python_filter` 时可为 **`--tile_size` / `--tile_overlap`**（与 Spring 网关当前默认路径**无关**，网关未传 tiling）。全量本文件滤波若走网关且内存不够，需改网关或先做子集。

---

## 4. 新建滤波任务（ROR）

| 参数 | 默认 | 建议先试 | 调参方向 |
|------|------|----------|----------|
| `ror_radius` | 0.5 m | **0.35～0.50 m** | 半径应 **明显大于** 典型邻距（~0.1 m），否则易误删结构点 |
| `ror_min_neighbors` | 5 | **6～12** | 半径大时可略升 minNeighbors，抑制稀疏噪声 |

**建议试参顺序：** 固定 `radius=0.45`，`min_neighbors = 5 → 8 → 12`；再微调 `radius ±0.05`。

---

## 5. 分类 — PMF（地面 / 非地面）

**合并到 Python 的键：** `cell_size_m`, `max_window_size`, `slope_threshold`（与校园语义共用 PMF 地面部分）。

| 参数 | 默认 | 建议先试 | 说明 |
|------|------|----------|------|
| `cell_size_m` | 0.6 | **0.5～0.8** | 点间距 ~0.1 m，0.6 m 已远大于点距，格网内统计稳定；场景极大时可略增以减格网数、加速 |
| `max_window_size` | 8 | **6～10** | 窗口越大越能连大片地面，越大越慢 |
| `slope_threshold` | 0.15 | **0.12～0.20** | 校园有缓坡 / 台阶时略**提高**可少吞非地面；地面被大量判非地面则略**降低** |

**建议试参顺序：** 先动 `slope_threshold`，再动 `max_window_size`，最后动 `cell_size_m`。

---

## 6. 分类 — CSF-lite

| 参数 | 默认 | 建议先试 | 说明 |
|------|------|----------|------|
| `cloth_resolution` | 0.5 | **0.4～0.7** | 相对点间距已较粗；过小慢、过大易漏细节地形 |
| `rigidness` | 2 | **2～3** | 略增更「硬布」，适合建筑脚下硬地面 |
| `iterations` | 500 | **400～600** | 收敛不足时可升 |
| `classify_threshold` | 0.5 | **0.45～0.55** | 地面/非地面分界敏感时可微扫 |

---

## 7. 分类 — 校园规则语义 `rule_semantic_campus`

**向导可填（会进合并 JSON）：** `cellSizeM`, `maxWindowSize`, `slopeThreshold`, `semanticNeighborCount`, `semanticPlanarityBuildingMax`, `semanticZStdVegetationMin`（与 PMF 地面共用前三项）。

**Python 仍读取、但当前 Java 合并未写入、需改代码或手工拼网关 JSON 才能传的键：**  
`semantic_z_std_flat_max`（默认 **0.30**）、`semantic_planarity_vegetation_min`（默认 **0.38**）。屋面被判成植被时，往往要动这两类阈值，见下表「现象列」。

| 参数 | 默认 | 建议先试 | 若现象则… |
|------|------|----------|-----------|
| `semantic_neighbor_count` | 24 | **20 / 32 / 40** | k 小：局部更敏感；k 大：更平滑，大平面上 z_std/planarity 更稳 |
| `semantic_planarity_building_max` | 0.12 | **0.14～0.22** | 大屋面被判**植被(3)**：略**增大**（放宽「建筑平面度」） |
| `semantic_z_std_vegetation_min` | 0.28 | **0.32～0.38** | 同上：略**增大**可减少「略糙平面」进植被 |
| `cell_size_m` / `max_window_size` / `slope_threshold` | 同 §5 | 与 PMF 一致先试 | 地面(1)错了，后面语义全错；先保证 PMF 地面合理 |
| `semantic_z_std_flat_max`（仅 Python 默认或手工 JSON） | 0.30 | **0.35～0.45** | 建筑被判植被：常需**增大**（允许屋面邻域 Z 稍糙仍算建筑） |
| `semantic_planarity_vegetation_min`（同上） | 0.38 | **0.42～0.50** | 植被类过宽：略**增大**，减少非植被进 3 类 |

**建议试参顺序：**

1. 只调 PMF 三项（地面比例正常）。  
2. 固定 `semantic_neighbor_count=32`，扫 `semantic_planarity_building_max` 上行。  
3. 再扫 `semantic_z_std_vegetation_min` 上行。  
4. 若仍大量屋面为绿，再考虑改 Python 默认或扩展 API 传 `semantic_z_std_flat_max`。

---

## 8. 分割 — 欧式聚类 `euclidean_cluster`

| 参数 | 默认 | 建议先试 | 说明 |
|------|------|----------|------|
| `cluster_tolerance` | 0.5 m | **0.25～0.45 m** | 点间距 ~0.1 m，0.5 m 已能连较松簇；要更细实例略**减小** |
| `min_cluster_points` | 50 | **80～200** | 稠密数据：略升可去碎片簇 |
| `max_cluster_points`（可选） | 无 | 按需上限 | 避免单簇爆炸（若 API 支持） |

**建议试参顺序：** 先 `tolerance` 从 0.35 双向扫，再调 `min_cluster_points`。

---

## 9. 分割 — 区域生长 `region_growing`

| 参数 | 默认 | 建议先试 | 说明 |
|------|------|----------|------|
| `normal_neighbor_count` | 30 | **24～40** | 估法向稳定性 |
| `angle_threshold_deg` | 30 | **25～40°** | 建筑立面与屋面转折：过小裂簇，过大并簇 |
| `distance_threshold` | 0.3 | **0.15～0.35 m** | 与点间距同量级时可略降以跟表面 |
| `min_region_points` | 100 | **150～400** | 抑制小区域 |
| `max_seeds` | 50 | **40～80** | 大场景可略增覆盖 |

---

## 10. 双窗 / 单窗与任务链（使用本文件时的操作顺序）

1. **路径单窗**：原始 LAS 绝对路径指向本文件；`maxPoints` 先用 180000。  
2. **新建滤波**：优先 SOR（§3）或 ROR（§4）得到 `FILTERED_LAS`。  
3. **滤波双窗**：用父任务 `taskId` 对比原始 vs 滤波。  
4. **派生分类/分割**：**输入一律为已成功滤波的 LAS**（父任务输出）；再对子任务做「派生双窗」预览。  
5. **校园语义双窗**：右侧为 `classification` + `semantic_campus` 调色；调参见 §7。

---

## 11. 记录表（可复制自用）

| 功能 | 试参编号 | 关键参数组合 | 结果（通过/不通过） | 备注 |
|------|----------|----------------|---------------------|------|
| SOR | 1 | k=__, std=__ | | |
| ROR | 1 | r=__, minN=__ | | |
| PMF | 1 | cell=__, win=__, slope=__ | | |
| CSF | 1 | res=__, rigid=__, iter=__, th=__ | | |
| rule_semantic_campus | 1 | k=__, plan_max=__, zveg_min=__ + PMF 三项 | | |
| 欧式聚类 | 1 | tol=__, minPts=__ | | |
| 区域生长 | 1 | k_n=__, angle=__, dist=__, minReg=__ | | |

---

## 12. 免责声明

- 本指南依据**一次**全文件头读与**抽样**统计，未对全 8870 万点做逐点分类验证。  
- 「系统完全正确」在工程上 = **流程、持久化、预览与算法契约正确**；语义/滤波效果仍依赖参数与算力边界。  
- 若需把 `semantic_z_std_flat_max` 等纳入向导，需在 Agent 模式下改 `DerivedParameterMergeSupport` / `CreateDerivedTaskRequest` / 前端表单。

---

*生成说明：数据脚本使用 `laspy` + `numpy`（及局部 `scipy.spatial.cKDTree`）在仓库根目录运行。*
