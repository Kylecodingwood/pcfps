# PCFPS 后端（Spring Boot）

## 环境要求

- Java 17+
- Maven 3.9+
- PostgreSQL 14+

## 数据库

本项目**不使用 Flyway**。表结构请用 `psql` **手动执行** SQL 脚本。

1. **创建数据库与用户**（在 `psql` 中执行，需用有建库权限的账号连接，例如 macOS Homebrew 下常用：`psql postgres`）：

```sql
CREATE USER pcfps WITH PASSWORD 'pcfps';
CREATE DATABASE pcfps OWNER pcfps;
```

2. **建表**（仅 DDL，不含演示数据）：

```bash
psql -U pcfps -d pcfps -f db/schema/init_schema.sql
```

若数据库**早已用旧版 `init_schema.sql` 建过**，请再执行一次升级脚本（幂等 `IF NOT EXISTS`）以加入滤波列：

```bash
psql -U pcfps -d pcfps -f db/schema/upgrade_add_filter_task_config.sql
```

若需 **滤波实验指标**（`filter_metrics_json`，与 `comparison-bundle.runMetrics` 一致）：

```bash
psql -U pcfps -d pcfps -f db/schema/upgrade_add_filter_metrics_json.sql
```

若需 **分割/分类派生任务**（`task_kind`、`parent_task_id`、`derived_method`、`derived_params_json`、`derived_metrics_json` 及索引）：

```bash
psql -U pcfps -d pcfps -f db/schema/upgrade_add_derived_task_columns.sql
```

3. **导入演示账号**（与建表脚本分离）：

```bash
psql -U pcfps -d pcfps -f db/seed/demo-users.sql
```

- 用户名：`demo`  
- 密码：`password`

4. 再 **启动应用**（`spring.jpa.hibernate.ddl-auto` 为 `validate`，要求表已存在并与实体一致）。

## 环境变量配置

| 变量 | 说明 |
|------|------|
| `SPRING_DATASOURCE_URL` | JDBC 地址（默认 `jdbc:postgresql://localhost:5432/pcfps`） |
| `SPRING_DATASOURCE_USERNAME` | 数据库用户名 |
| `SPRING_DATASOURCE_PASSWORD` | 数据库密码 |
| `JWT_SECRET` | JWT 签名密钥（生产环境请使用足够长的随机串） |
| `OUTPUT_ROOT` | 每个任务输出目录的根路径（未设置时默认：Monorepo 下与 `backend` 同级的 `outputfile/`，即 `${user.dir}/../outputfile`，依赖从 `backend` 目录启动；其它启动方式请显式设置本变量） |
| `FILTER_MAX_CONCURRENT_RUNNING` | 全局最多同时处于 `RUNNING` 的任务数（默认 `1`） |
| `MOCK_PYTHON_SUCCEED_AFTER_TICKS` | 仅 `mock-python` Profile：Mock 轮询多少次后视为成功（默认 `3`） |
| `PYTHON_SERVICE_BASE_URL` | 默认 `http://127.0.0.1:8000`；真实滤波时指向 `python_gateway` 根地址 |
| `SPRING_PROFILES_ACTIVE` | 设为 `mock-python` 可在未启动 `python_gateway` 时使用内存 Mock（不调 `python_filter`） |
| `PCFPS_PREVIEW_MAX_POINTS` | JSON 预览默认最大点数（默认 `50000`） |
| `PCFPS_PREVIEW_MAX_FILE_BYTES` | ASCII PLY 预览允许的最大文件字节；**LAS 子进程 stdout 抽干**时亦用该值作为累计读取上限（默认 `100000000`） |
| `PCFPS_PREVIEW_PYTHON` | LAS 抽样脚本解释器（默认 `python3`） |
| `PCFPS_PREVIEW_LAS_ENABLED` | 是否启用 LAS/LAZ 子进程预览（默认 `true`） |
| `PCFPS_PREVIEW_PROCESS_TIMEOUT_SEC` | LAS 子进程超时秒数（默认 `600`） |

## 路径预览（无 `file_id`，JWT + 绝对路径）

用于「仅填服务器绝对路径」的预览页；**不**创建 `FileAsset`。请求须带 **Bearer JWT**。路径经 `trim` 后须为 **绝对路径**，`normalize().toAbsolutePath()` 后 **`Files.isRegularFile`**，扩展名为 **las / laz / ply**（与建任务 `inputLasPath` 同一信任模型：任意持令牌用户可让服务端尝试读取进程有权访问的路径；适合毕设/可信机）。

| 接口 | 说明 |
|------|------|
| `POST /api/v1/preview/las-path` | Body：`{"lasPath":"/abs/…","maxPoints":…}`；`maxPoints` 可选，校验范围 **1～10_000_000**（与 `preview-points` 一致）。 |
| `POST /api/v1/preview/las-path/dual` | Body：`{"sourceLasPath":"…","filteredLasPath":"…","maxPoints":…}`；同上。 |

错误码：`PREVIEW_PATH_INVALID`（400）、`FILE_NOT_FOUND`（路径非普通文件等）、其它与文件型预览相同。

## Web 预览 JSON（`preview-points`）

- **接口**：`POST /api/v1/files/{fileId}/preview-points`，请求头 `Authorization: Bearer ...`、`Content-Type: application/json`；请求体可为 `{}`、`{"maxPoints":50000}`，或带可选 **`colorMode`**：`native`（默认）与 **`classification`**（`label` 为别名），控制 LAS/LAZ 子进程着色语义；省略 `maxPoints` 时使用 `PCFPS_PREVIEW_MAX_POINTS`。`maxPoints` 校验范围 **1～10_000_000**（极大值时 JSON 与子进程内存风险自负）。非法 `colorMode` 返回 **400**（`PREVIEW_INVALID_COLOR_MODE`）。
- **响应**：`application/json`，字段含 `points`（`x,y,z` 数组）、`truncated`、`sourcePointCountEstimate` 等。
- **格式**：`.las`/`.laz` 由运行时调用 `scripts/las_preview_sample.py`（需已安装 **laspy** 及 LAZ 所需后端）；`.ply` 仅支持 **ASCII**（用于当前 Mock 产物）。
- **本地大 LAS 验证**（不入 CI）：将 `FileAsset.storedPath` 指向本机如 `terra_las/cloud_17999bae.las` 或 `outputfile/output.las` 后，用上述接口对对应 `fileId` 发 POST 校验返回点数与坐标量级。

### 代码位置

- HTTP：`com.pcfps.file.FileDownloadController`（`POST .../preview-points`）。
- 编排与 DTO：`com.pcfps.preview`（`PointPreviewService`、`PointPreviewRequest` / `PointPreviewResponse` 等）。
- LAS 子进程脚本：`src/main/resources/scripts/las_preview_sample.py`（打包进 jar，运行时解压到临时文件后由 `ProcessBuilder` 执行）。

## 任务产物登记（`completeTaskSuccess`）

- **真实 Python**：`python_gateway` 在任务的 `outputBasePath` 下写出 **`filtered.las`** 后，Spring 登记 **`SOURCE_LAS`**（输入路径）与 **`FILTERED_LAS`**（`filtered.las` 绝对路径）。对比 bundle 不再依赖 `PREVIEW` 角色。
- **`mock-python` Profile**：无 LAS 产物时仍写入最小 ASCII **`filtered.ply`** 并登记为 `FILTERED_LAS`，便于本地无 Python 服务时走通 UI（`preview-points` 走 Java PLY 解析）。

## 运行

```bash
mvn spring-boot:run
```

仅 Mock、不启动 `python_gateway` 时：

```bash
mvn spring-boot:run -Dspring-boot.run.arguments=--spring.profiles.active=mock-python
```

API 根地址：`http://localhost:8080`

## 与 Python 集成

- **默认（非 `mock-python`）**：`HttpPythonGatewayService` 使用 **`WebClient`** 调用 `PYTHON_SERVICE_BASE_URL` 上的 **`POST /jobs`**、**`GET /jobs/{id}`**（见仓库 `[python_gateway/README.md](../python_gateway/README.md)`）。
- **`mock-python` Profile**：仅注册 `MockPythonGatewayService`，不调外部 HTTP。
