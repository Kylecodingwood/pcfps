# 3.coding：实现映射说明

## 单一事实来源

- 业务与流程决议：[1.req/requirements.md](../1.req/requirements.md) **v0.2**
- 横切规约：[specification.md](specification.md)

## 技术栈（已确认）

| 层 | 技术 |
|----|------|
| 后端 | Java, Spring Boot, PostgreSQL |
| 算法服务（离线已实现） | `python_filter`（`numpy` + `laspy` + `scipy` kd-tree + `sklearn.BallTree`），CLI + 库 |
| 算法服务（在线目标） | Python + REST（thin-wrapper 未来包装同一 `process`） |
| 前端 | React, Three.js（已定：Ant Design + Three；预览数据走 JSON 点集，见根 `README.md`） |

## 与 `2.design/server` 域映射（草案）

| 设计域 | 建议代码包路径（实现时定稿） |
|--------|------------------------------|
| `auth` | `.../auth` 或 `.../security` |
| `job` | `.../job` |
| `file-metadata` | `.../file` 或 `.../storage` |
| `python-gateway` | `.../integration/python` |
| **Web 预览点 JSON**（已实现） | `com.pcfps.preview`：`PointPreviewService`、`AsciiPlyPreviewParser`、`LasPreviewSubprocessRunner`；HTTP：`FileDownloadController`（`fileId`）、`PreviewPathController`（**绝对路径 + JWT** `las-path` / `las-path/dual`） |

## Web 预览传输（与根 README / 后端一致）

- **接口（任务资产）**：`POST /api/v1/files/{fileId}/preview-points`，`Content-Type: application/json`，请求体可为 `{}` 或 `{"maxPoints":…}`；响应为抽稀后的 `points`（`x,y,z`）及 `truncated`、`sourcePointCountEstimate` 等。
- **接口（服务器路径，无 file 行）**：`POST /api/v1/preview/las-path`、`POST /api/v1/preview/las-path/dual` — 见 [specification.md](specification.md)；JWT + 绝对路径普通文件。
- **实现分工**：**LAS/LAZ** 由 `backend/src/main/resources/scripts/las_preview_sample.py`（`laspy`）子进程抽样；**ASCII PLY** 由 Java 流式解析（兼容当前 Mock 的 `filtered.ply`/`preview.ply`）。
- **配置**：`pcfps.preview.*`（见 [`backend/README.md`](../../backend/README.md) 与 `application.yml`）。
- **与算法产物**：真实管线为 LAS→LAS 时，只要 `file_asset.stored_path` 指向 LAS，即可用本接口预览；Mock 任务仍写 PLY 的说明见 `backend/README.md`「Mock 任务与真实 LAS 产物」。

## 下一步

1. CI：使用固定 **小型 LAS fixture**（<1MB）跑 `python_filter`；可选增加对 `preview-points` 的小样集成测（大 LAS 仅本地验证）。
2. 生成 OpenAPI：由 `delta/2.design/server/python-gateway` 表驱动（将 `preview-points` 纳入契约）。
3. `jpa/`、`custom/` 与各 `*-model` / `*-api` 同步演进。
4. ~~前端：对比页改为请求 `preview-points` + 点云渲染~~（已完成：Ant Design 分流 + `/preview/*`）。

算法目录快速链接：[`python_filter/README.md`](../../python_filter/README.md)。  
后端运行与预览说明：[`backend/README.md`](../../backend/README.md)。
