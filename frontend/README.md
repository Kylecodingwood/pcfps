# PCFPS Frontend (Vite + React + Ant Design + Three.js)

## Setup

```bash
npm install
```

Copy `.env.example` to `.env` and set:

```
VITE_API_BASE_URL=http://localhost:8080
```

可选 **`VITE_PREVIEW_MAX_POINTS`**（正整数，最大 **10_000_000**，与后端校验一致）：设置后，单路径 / 双路径 / 任务双窗的预览请求都会带上该 `maxPoints`；不设则仍由后端默认 **`PCFPS_PREVIEW_MAX_POINTS`**（常见为 `50000`）决定。大点数会显著增加 JSON 体积与浏览器内存，仅建议在可信本机调试。

## Run (dev)

```bash
npm run dev
```

Open the printed URL (default `http://localhost:5173`). CORS allows this origin on the backend.

## Routes（登录后）

| 路径 | 说明 |
|------|------|
| `/jobs` | 任务列表（Ant Design `Table`）；成功 **滤波** 任务：**对比预览**、**分割**、**分类**；成功 **派生** 任务：**派生双窗** |
| `/process/segment` | **点云分割**枢纽：已成功的滤波任务列表 → `/jobs/:id/segment/new` |
| `/process/classify` | **点云分类**枢纽：同上 → `/jobs/:id/classify/new` |
| `/jobs/new` | **新建处理**：`Steps` — LAS **绝对路径** + **SOR/ROR**（`Segmented`）与可选参数（placeholder 提示默认）→ `POST /api/v1/tasks` → 轮询 → 成功页展示 **滤波摘要**、**输出目录** → **双窗对比**；可链到子向导 |
| `/jobs/:parentTaskId/segment/new` | **分割子向导** → `POST /api/v1/tasks/{parentId}/derived-jobs`（`taskKind=SEGMENT`）→ 轮询 → **`/preview/dual?childTaskId=`** |
| `/jobs/:parentTaskId/classify/new` | **地面分类子向导** → 同上（`taskKind=CLASSIFY`） |
| `/preview/single` | **单文件抽稀**：填绝对路径 → `POST /api/v1/preview/las-path`（JWT；服务端须能读到该普通文件） |
| `/preview/dual` | **点云工作台（双窗）**：页内 **Segmented** 切换滤波对比 / 派生双窗 / 路径双窗；`?workspace=filter` / `?workspace=derived` 可在无 ID 时进入对应输入卡片。无 bundle query 时为 **两路径** + `POST /api/v1/preview/las-path/dual`；`?taskId=` → `comparison-bundle` + 两次 `preview-points`（`native`）；**`?childTaskId=`** → `derived-comparison-bundle` + 左侧 `preview-points`（`native`）+ 右侧 **`colorMode: classification`** |
| `/tasks/:id/compare` | 兼容旧链接，重定向到 `/preview/dual?taskId=…` |

## 与后端的约定

- **任务处理**：`POST /api/v1/tasks`，body 含 `inputLasPath`（必填）及可选 `filterMethod`、`sorNeighborCount`、`sorStdRatio`、`rorRadius`、`rorMinNeighbors`；省略数值时由后端合并默认并返回 `filterSummary`。
- **路径预览**：填本机 **绝对路径**；后端校验 JWT 与文件可读性（与建任务路径同一信任模型）。
- **任务对比**：仍走 **JWT + fileId**，不走路径预览接口；`comparison-bundle` 含 `runMetrics`（滤波）；**`derived-comparison-bundle`** 含 `derivedMetrics`（分割/分类子任务）。

## 点云查看器：标准 vs 高保真

预览页（`/preview/single`、`/preview/dual`）支持 **Segmented** 切换：

| 模式 | 实现 | 说明 |
|------|------|------|
| **标准** | [`PointCloudViewport`](src/components/PointCloudViewport.tsx) | `PointsMaterial` + 圆形 sprite 贴图，点大小上限约 2.25，轻量稳定。 |
| **高保真** | [`PremiumPointCloudViewport`](src/components/PremiumPointCloudViewport.tsx) | 自定义 **Splat shader**（高斯软边、更大点径）+ **EDL** 后期描边；见 `src/viewer/premium/`。 |

URL 可加 `?viewer=premium` 固定高保真模式（便于论文截图复现）。高保真模式下可调 **点大小倍率 / EDL 强度 / EDL 半径**；GPU 与内存占用高于标准模式，建议逐步提高 `maxPoints` 并观察帧率。

## Build

```bash
npm run build
```

Output in `dist/`.
