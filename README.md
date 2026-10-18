# PCFPS（点云滤波毕设）

Monorepo layout:

- `[delta/](delta/)` — 需求/设计文档（Delta 工作空间）
- `[backend/](backend/)` — Spring Boot 3 + PostgreSQL + JWT；默认 **`HttpPythonGatewayService`** 调真实 Python；`mock-python` Profile 走内存 Mock。
- `[frontend/](frontend/)` — Vite + React + TypeScript + **Ant Design** + Three.js；**处理任务**（列表含滤波摘要、新建向导可选 **SOR/ROR** 与参数）与 **点云预览**分路由（见下表）；旧链接 `/tasks/:id/compare` 自动跳到带 `taskId` 的双窗预览。
- `[python_gateway/](python_gateway/)` — **在线** FastAPI：`POST /jobs`、`POST /derived-jobs`、`GET /jobs/{id}`；滤波调用 `python_filter.process`；派生任务调用 `python_derived.process_derived`，写出 `derived.las`
- `[python_filter/](python_filter/)` — **离线** LAS SOR/ROR 滤波（`laspy` + `numpy` + `scipy.cKDTree` + `sklearn.BallTree`），CLI / 库入口 `process(...)`
- `[python_derived/](python_derived/)` — **派生**分割（欧式聚类 DBSCAN、区域生长）与分类（PMF-lite、CSF-lite、**`rule_semantic_campus` 校园规则伪语义**），由网关在线调用。分割写入 LAS 时 **`classification` 仅使用 0～31**（噪声 0，簇 `1 + ((id-1) % 30)`）；若点格式含 **`user_data`**，则额外写入 **簇号（0～255）** 供预览区分更多簇。语义分类写入 **1=地面、2=建筑、3=植被、4=其它**（`generating_software` 含 `PCFPS_RULE_SEMANTIC_v1` 标记）。

## 当前进度（2026-05）

### 已完成

- **需求与设计骨架**：`delta/` 已完成 `1.req / 2.design / 3.coding` 的主干结构与关键文档；实现映射与 `preview-points` 规约见 `[delta/3.coding/README.md](delta/3.coding/README.md)`、`[delta/3.coding/specification.md](delta/3.coding/specification.md)`。
- **后端基础能力**：
  - JWT 登录鉴权（`demo/password` 演示账号）。
  - 任务创建/查询、`comparison-bundle` 聚合接口。
  - 文件受控下载接口（不直接暴露服务器绝对路径）。
  - Python 调度：`POST /jobs` → 轮询 `GET /jobs/{id}`；默认连 **`python_gateway`**（见 `[python_gateway/README.md](python_gateway/README.md)`）；`mock-python` Profile 下仍为内存 Mock。`POST /api/v1/tasks` 可选 **`filterMethod`（SOR/ROR）** 与数值参数（省略则由服务端合并默认并写入 **`filter_task.filter_method` + `filter_params_json`（JSONB）**）；调度时按快照组装网关 body；**存量库**需执行 `[backend/db/schema/upgrade_add_filter_task_config.sql](backend/db/schema/upgrade_add_filter_task_config.sql)`。
  - **Web 预览点 JSON**：`POST /api/v1/files/{fileId}/preview-points`（任务归属资产）；以及 **`POST /api/v1/preview/las-path`**、**`POST /api/v1/preview/las-path/dual`**（服务器 **绝对路径**、规范化后须为 **普通文件**；需 **JWT**，信任模型与建任务时填写 `inputLasPath` 相同）。**LAS/LAZ** 由子进程 `las_preview_sample.py`（**Python3 + laspy**）；**ASCII PLY** 由 Java 解析。错误码含 `PREVIEW_PATH_INVALID`（400）等。详见 `[backend/README.md](backend/README.md)`。
  - **LAS 预览真彩色 / 伪彩色**：`preview-points` 请求体可选 **`colorMode`**：`native`（默认，LAS 有 RGB 时优先真彩色）或 **`classification`**（按 `classification`/`user_data` 伪彩色，**即使 LAS 仍带 RGB 维度也不用于显示着色**，便于分割/分类结果在大屏上看清簇/类）。路径型 `las-path` 预览固定为 `native`。ASCII PLY 仍为单色。
  - **点云工作台（前端）**：`/preview/dual` 单页内用 **Segmented** 切换 **滤波对比 / 派生双窗 / 路径双窗**；同一套 `PointCloudViewport`，仅更换 `preview-points` 的 `fileId` 与 `colorMode`；向导成功入口文案 **「在大屏中查看」** 直达该页。
  - **LAS 预览 stdout 管道**：先前主线程在子进程结束前未消费 stdout，大 JSON 填满 OS 管道缓冲区后子进程阻塞在写端，表现为长时间超时。已在 `LasPreviewSubprocessRunner` 中用**后台线程抽干 stdout** 修复；累计读取体量受 **`PCFPS_PREVIEW_MAX_FILE_BYTES`（`pcfps.preview.max-file-bytes`）** 上限约束，与 PLY 预览同配置。
  - **预览 `maxPoints` 上限**：路径预览与 `preview-points` 请求体中的 `maxPoints` 校验已放宽至 **1～10_000_000**；前端可选 **`VITE_PREVIEW_MAX_POINTS`** 统一传入（见 `[frontend/README.md](frontend/README.md)`），不设时仍由后端默认抽稀规模决定。
  - **预览单测**：`AsciiPlyPreviewParserTest`（ASCII PLY 抽稀、拒绝 binary header）、`LasPreviewSubprocessRunnerTest`（stdout 抽干与超管道缓冲场景）等，保证预览路径可回归。
- **前端基础能力**：
  - **Ant Design** 布局（`ConfigProvider` 中文 + 圆角/系统字体主题）：登录、侧栏 **处理任务 / 点云预览**、任务列表（**配置摘要**列：滤波或派生；成功滤波任务 **对比预览 / 分割 / 分类** 入口）、**新建处理向导**（**SOR/ROR**（`Segmented` 切换）、参数 **placeholder 提示默认**、卡片式布局 → 轮询 → 成功页展示 **滤波摘要 + 输出目录** → 双窗对比；成功页另链 **`/jobs/:id/segment/new`**、**`/jobs/:id/classify/new`**）、**子向导**（分割 / 分类，独立页提交 **`POST .../derived-jobs`**）、**单路径抽稀预览**、**双窗对比**（`?taskId=`：原始 vs 滤波 + `runMetrics`；**`?childTaskId=`**：滤波 vs 分割/分类 + **`derivedMetrics`**；或手动两路径）（详见 `[frontend/README.md](frontend/README.md)`）。
- **路径统一预览（无上传落库）**：预览页填 **服务器绝对路径** 时走 `POST /api/v1/preview/las-path`（单）与 `POST /api/v1/preview/las-path/dual`（双）；服务端仅校验 **绝对路径 + 普通文件 + 扩展名**（无输出目录前缀限制）。任务内对比仍走 **`fileId` + `POST .../files/{id}/preview-points`**，与路径预览并存。
- **数据库落地**：
  - 改为手动 SQL 建表（不使用 Flyway）。
  - `backend/db/schema/init_schema.sql`（含 `filter_method` / `filter_params_json` / **`filter_metrics_json`** / **派生列** `task_kind`、`parent_task_id`、`derived_*`）+ `backend/db/seed/demo-users.sql` 已可用；已有库升级见 `upgrade_add_filter_task_config.sql`，若需 Python **实验指标**落库再执行 `upgrade_add_filter_metrics_json.sql`，派生任务列见 **`upgrade_add_derived_task_columns.sql`**。
- **算法离线链路（2026-05）**：`python_filter` 已实现 `SOR` / `ROR` CLI，**仅 LAS/LAZ ↔ LAS/LAZ**（流式子集写出，保留 header 尺度）；默认整载入内存，超大点云可选用 **XY 分块 + 重叠**（`--tile_size` / `--tile_overlap`，单位与 LAS 的 XY 一致）。stdout 打印 `N_before/N_after`、分段计时；分块模式额外输出 `tile_grid_nx/ny` 与 `timing_pass1_bucket_sec` / `timing_pass2_tiles_sec`。详细用法见 `[python_filter/README.md](python_filter/README.md)`。

### 已完成：分割 / 分类派生任务

- **入口**：任务列表成功行 **对比预览 / 分割 / 分类**；滤波成功向导页 **新建分割 / 新建分类**。
- **子向导**：`/jobs/:parentTaskId/segment/new`、`/jobs/:parentTaskId/classify/new`；提交 **`POST /api/v1/tasks/{parentId}/derived-jobs`**（`taskKind` + `algorithm` + 可选参数，服务端合并默认并快照 `derived_params_json`）。
- **Python**：`python_gateway` **`POST /derived-jobs`** → `python_derived.process_derived`（**euclidean_cluster**、**region_growing**、**pmf**、**csf**）写 **`derived.las`**（`classification` 标签）+ **`metrics_bundle`**。
- **双窗**：`/preview/dual?childTaskId=` → **`GET /api/v1/tasks/{childId}/derived-comparison-bundle`**（左父 **FILTERED_LAS**、右子 **SEGMENTED_LAS** / **CLASSIFIED_LAS**）+ 页内 **派生实验数据 `Descriptions`**；LAS 预览脚本对 **仅有 classification** 的点云赋 **伪彩色 r/g/b**。

### 下一步计划（推荐顺序）

与下文「代办」中的展示项对应；**P0–P2、P4、P5b 已落地**；后续以工程化（P3）、展示增强（P5）为主。


| 优先级    | 内容                        | 说明                                                                                                                                                                           |
| ------ | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **P0** | **前端对接 `preview-points`** | **已完成**：对比页双窗 JSON 点云 + 抽稀说明。                                                                                                                                           |
| **P1** | **真实 Python 在线服务**        | **已完成**：`python_gateway` + `HttpPythonGatewayService`（`WebClient`）；无 Python 时用 `--spring.profiles.active=mock-python`。                                                          |
| **P2** | **任务成功产物与算法一致**           | **已完成**：存在 `filtered.las` 则登记 LAS；仅 Mock 且无 LAS 产物时仍回退最小 ASCII `filtered.ply`。                                                                                                     |
| **P3** | **工程化与契约**                | 从设计表生成/维护 `delta/OpenAPI`；后端任务流/权限/预览最小集成测；CI 可选用小型 LAS fixture 跑 `python_filter` CLI。                                                                                       |
| **P4** | **Ant Design 壳层**         | **已完成**：Layout / Menu / Table / Form / Steps / Result。                                                                                                                       |
| **P5** | **展示增强（答辩加分）**            | 任务列表已显示 **滤波配置摘要**；**双窗任务模式**已展示 **全量点数 + 去除比例 + Python 耗时**（`runMetrics`）；后续可做剖面/薄切片、ROI 或与分块网格对齐的局部对比。可选评估 Potree 等大点云方案。                                                                                                   |
| **P5b** | **分割 / 分类派生任务** | **已完成**：四算法、`derived-jobs` / `derived-comparison-bundle`、`metrics_bundle` 落库、子向导与 **`?childTaskId=`** 双窗；存量库执行 `upgrade_add_derived_task_columns.sql`。                                                                                                   |
| **P6** | **论文与交付物**                | 架构图、时序图、数据库 E-R、接口说明、实验结果（耗时/效果对比）。                                                                                                                                          |


## 代办（前端展示 / 答辩可视）

> 与上表 **P5** 等展示增强对应；抽稀预览浏览器侧已闭环（`preview-points` + 双窗点云）。  
> **目标能力（已定方向）**：**抽稀预览** + **剖面** + **分块/ROI 对比**，解决「仅鸟瞰整城时 CloudCompare 也不容易看出滤波差异」的问题。  
> **工程思路（参考 rz_sanweijiguangdianyunchuli）**：格式识别与减负在**服务端/算法层**完成；浏览器只对接 **JSON 预览点**（`x,y,z` 数组 + 元数据如 `truncated`、点数估计等）。本仓库后端为 **Spring Boot**：实现上为 **解码 → 抽稀 → JSON**（ASCII PLY/XYZ 可由 Java 解析；LAS/LAZ 等可经 **Python/laspy** 或算法侧预处理，细节在实现阶段定）。

- [x] **抽稀预览（浏览器侧）**：对比页已请求 `preview-points` 并在 UI 标明抽稀与 `truncated` / 点数估计等元数据。
- **剖面展示**：Three.js 中**剖切平面 / 薄切片**，只显示截面附近点，便于看立面与离群结构（与 CloudCompare 剖面同类需求）。
- **一块一块对比**：**ROI 或与 `python_filter` 分块网格对齐**的子范围，源 vs 滤波**同范围、同视角**并排或联动；若单块仍过大，块内继续抽稀或由后端按块返回 JSON。
- [x] **JSON 预览对接（P0）**：对比页已使用 `POST /api/v1/files/{fileId}/preview-points` + Three 点云（见 `[frontend/README.md](frontend/README.md)`）。
- [x] **Ant Design 落地**：已用 Layout、Menu、Table、Form、Steps、Result 等；Three 点云嵌入各预览页。

## 待做 / 展望（当前版本未实现）

以下多为老师评审或工业场景延伸需求，**未在本仓库排期实现**，供后续迭代与论文「展望」引用：

- **左右分栏拖拽（Resizable）**：可拖拽调整双窗宽度比例。
- **视锥 / ROI 联动加密抽稀**：放大局部时向服务端请求更密子集，而非仅提高全局 `maxPoints`。
- **参考 LAS / CloudCompare 真值对比**：与人工标注 LAS 同屏对比；可选定量 IoU / 栅格一致率。
- **剖面切片 + 二维高程滤波链**：薄层切片后在中值/拟合/高度阈值上再去尖峰，并可选回写 LAS。
- **工业「特征保留」滤波**：按语义/几何分层压缩与去噪（人车树等），区别于全局 SOR/ROR。
- **深度学习语义分割**：大规模标注与训练管线。
- **系统内嵌点云标注工具**、**Potree 级 LOD 海量浏览** 等。

## 展示方案讨论纪要（2026-05）

### 1. 能力与答辩叙事


| 能力            | 作用                                     |
| ------------- | -------------------------------------- |
| **抽稀预览**      | 控制浏览器内存与请求体积；**不替代** LAS 全精度存档。        |
| **剖面**        | 把纵深关系拉开，**补鸟瞰看不清**的问题。                 |
| **分块/ROI 对比** | 局部放大、与算法 tile 叙事一致，**补「差异被上亿点糊住」**的问题。 |


三者叠加，用于毕设演示：**全局用指标（N、耗时）+ 局部用几何**；与「只在网页里复刻 CloudCompare 全功能」区分开，答辩仍站得住。

### 2. 精度说明（避免误解）

- **不丢精度**指的是：**滤波结果 LAS、任务产物路径上的主数据**保持完整精度与可追溯。  
- **浏览器里那一屏**若经抽稀或仅加载子块，**屏幕显示本身不是全点云**；答辩应表述为「全精度在 LAS，Web 为可交互预览层」。

### 3. 传输与预览形态（**已拍板：JSON + 后端解码抽稀**）

参考 [lihan1206/rz_sanweijiguangdianyunchuli](https://github.com/lihan1206/rz_sanweijiguangdianyunchuli)：前端 **Three.js 只画 `x,y,z` 点数组**；多格式在**服务端**解析，预览用 **抽稀后的 JSON** 下发。本仓库采用**同一原则**。

**已定决策：**

1. **浏览器预览主通道**：**JSON**（仅承载**预览规模**的点集及元数据），**不把整云 LAS 打成整文件 JSON**（避免体积与内存失控）。
2. **服务端**：对 **任务资产**（`FileAsset` + `fileId`）或 **已鉴权用户提交的绝对路径**（`/preview/las-path*`）做 **解码 → 抽稀 → JSON**；LAS 全精度仍落在磁盘产物与路径登记上，与预览分离。
3. **PLY**：仍可作为 **磁盘上的中间/演示产物**（如当前 Mock 写 ASCII PLY），由 **后端读取并解析** 后进入上述 JSON 管道；**前端不再以 PLY 文件为主传输形态**（迁移完成后可弱化仅 PLY 的对比页路径）。

**当前仓库实现状态：**  
- **任务链**：`POST .../preview-points`（按 `fileId`）+ 前端 `/preview/dual?taskId=…` 双窗 **JSON 点云**；产物 **`filtered.las`**（真实 Python）或 Mock 时 **`filtered.ply`**。  
- **仅预览链**：`POST /api/v1/preview/las-path*` + 前端 `/preview/single`、`/preview/dual`（无 `taskId` 时填两路径）；路径须为进程可读 **绝对路径** 下的 **LAS/LAZ/ASCII PLY**（适合毕设/可信机，不宜对公网开放）。



---

**仍可在实现前细化的设计点**：剖面/ROI 是否独立接口、双窗相机联动、路径预览与任务的统一指标面板等。

### 前端路由一览（登录后）

| 路径 | 用途 |
|------|------|
| `/jobs` | 任务列表；成功 **滤波** 任务：**对比预览**、**分割**、**分类**；成功 **派生** 任务：**派生双窗** |
| `/jobs/new` | 新建处理：填路径 → 创建任务 → 轮询 → 成功页输出目录 → **打开双窗对比**（并可进子向导） |
| `/process/segment` | **点云分割**枢纽：列出已成功的滤波父任务 → 链到子向导 |
| `/process/classify` | **点云分类**枢纽：同上 |
| `/jobs/:parentTaskId/segment/new` | 分割子向导（欧式聚类 / 区域生长）→ 轮询 → **`/preview/dual?childTaskId=`** |
| `/jobs/:parentTaskId/classify/new` | 分类子向导（PMF / CSF / **校园规则语义**）→ 同上 |
| `/preview/single` | 单文件：填绝对路径 → 路径预览 API（JWT + 服务端可读普通文件） |
| `/preview/dual` | 双窗：`?taskId=` 原始 vs 滤波；**`?childTaskId=`** 滤波 vs 分割/分类；无 query 时两路径走 dual 路径 API |
| `/tasks/:id/compare` | 兼容旧 URL，重定向到 `/preview/dual?taskId=…` |

## Quick start（当前可跑通）

1. PostgreSQL：建库与用户后，执行 `backend/db/schema/init_schema.sql` 建表，再执行 `backend/db/seed/demo-users.sql`。
2. **真实滤波链路**：安装依赖并启动 `python_gateway`（默认 `http://127.0.0.1:8000`，见 `[python_gateway/README.md](python_gateway/README.md)`）。若暂不启动，则 Spring 使用 **`mvn spring-boot:run -Dspring-boot.run.arguments=--spring.profiles.active=mock-python`**（不调真实滤波，对比页仍可预览抽稀：源为 LAS、滤波侧为 Mock PLY）。
3. `backend`: `mvn spring-boot:run`（默认连 `PYTHON_SERVICE_BASE_URL`，与 `python_gateway` 端口一致）。若需对 **LAS/LAZ** 调预览（`preview-points` 或 `preview/las-path*`），运行 Spring 的机器需 **Python3 + laspy**（见 `[backend/README.md](backend/README.md)`）；Mock 下滤波侧为 ASCII PLY 时由 Java 解析即可。  
   - **路径预览**：任意本机可读 **绝对路径** 下的 **LAS/LAZ/ASCII PLY** 均可（与 **建任务** 填 `inputLasPath` 同一信任模型）；请勿在不可信网络暴露该后端。
4. `frontend`: `cp frontend/.env.example frontend/.env` 后 `npm install && npm run dev`（默认 `http://localhost:5173`，已装 **antd**）

详见各子目录 `README.md`。

算法 CLI 上手（仓库根）：`pip install -r python_filter/requirements.txt` → `PYTHONPATH=. python -m python_filter --help`。细节见 `[python_filter/README.md](python_filter/README.md)`。

## 源码打包（答辩 / 提交附件）

生成**仅含源代码**的 zip（排除 `node_modules`、`target`、`outputfile`、`terra_las` 等，约几十 MB）：

```bash
./scripts/package-source.sh
```

默认输出到上级目录 `../pcfps-source-YYYYMMDD.zip`；解压后环境与启动步骤见 **[SOURCE_README.md](SOURCE_README.md)**。

## 真实 Python

- **离线**：`python_filter/` CLI 与 `process(...)`。
- **在线（默认）**：`python_gateway/`（FastAPI）+ 后端 **`HttpPythonGatewayService`**（`PYTHON_SERVICE_BASE_URL`，默认 `http://127.0.0.1:8000`）。
- **无 Python 服务时**：Spring **`--spring.profiles.active=mock-python`** → `MockPythonGatewayService`；任务成功时若无 `filtered.las` 则回退登记最小 ASCII **`filtered.ply`**。

## 展示边界与可信性

- **定位**：本系统是“自动化滤波业务平台”，不是通用点云工作站（如 CloudCompare/Potree Desktop）。
- **数据分层**：
  - **LAS**：原始主数据（处理与存档主依据）。
  - **预览**：以 **JSON 点集（后端解码 + 抽稀）** 为主通道供 Web 交互（已定）；磁盘上的 **PLY** 仍可作中间产物，由服务端读取而非依赖浏览器解析大文件。
- **为什么前端不直接读 LAS**：浏览器侧对 LAS/LAZ 的解析、超大文件加载、LOD/索引管理成本高；采用「**后端/算法侧处理 → 预览 JSON** + 前端点渲染」。
- **可信展示最小要求**（答辩重点）：
  1. 前后必须是两份不同数据：`SOURCE_PREVIEW` 与 `FILTERED_PREVIEW`。
  2. 页面提供量化指标：`N_before`、`N_after`、去除比例、处理耗时。
  3. 双窗口同视角联动（旋转/缩放同步），避免视觉误导。

## 冻结清单（先定契约再编码）

为避免反复返工，先冻结以下契约：

1. Python API：`POST /jobs`、`GET /jobs/{externalJobId}`。
2. 状态枚举：`PENDING/RUNNING/SUCCEEDED/FAILED`（后续可扩展 `CANCELLED`）。
3. 产物命名与角色：真实 Python 写出并登记 **`filtered.las`**（`FILTERED_LAS`）；Mock 且无 LAS 产物时可为 **`filtered.ply`**。对比 bundle 以 **SOURCE_LAS + FILTERED_LAS** 为主；Web 预览以 **`preview-points` JSON** 为主通道。
4. 错误语义：`errorCode + errorMessage`，并区分可重试/不可重试。

> “冻结”= 在 `delta` 文档中定稿并作为实现合同，非必要不改字段与语义。

