# PCFPS 源代码说明

本压缩包为 **PCFPS（点云滤波毕设）** 项目的**源代码**交付物，不含本地运行产生的大数据与依赖缓存。解压后请按下列步骤配置环境并启动各服务。

## 项目说明

PCFPS 是面向校园点云的 **SOR/ROR 滤波与派生处理（分割、分类）** 业务平台：Spring Boot 后端编排任务，FastAPI Python 网关执行算法，React + Three.js 前端提供任务管理与双窗点云预览。

| 目录 | 说明 | 详细文档 |
|------|------|----------|
| `backend/` | Spring Boot 3 API、JWT、PostgreSQL、任务与预览 | [backend/README.md](backend/README.md) |
| `frontend/` | Vite + React + Ant Design + Three.js | [frontend/README.md](frontend/README.md) |
| `python_gateway/` | 在线 FastAPI（滤波 / 派生任务） | [python_gateway/README.md](python_gateway/README.md) |
| `python_filter/` | 离线 LAS SOR/ROR 滤波库与 CLI | [python_filter/README.md](python_filter/README.md) |
| `python_derived/` | 分割、分类派生算法 | （由网关调用，见 `python_gateway`） |
| `python_rf_semantic/` | RF 语义分类实验（可选） | 见 `docs/reference/` |
| `delta/` | 需求 / 设计 / 编码规约（Delta 工作空间） | [delta/3.coding/README.md](delta/3.coding/README.md) |
| `docs/` | 论文配图脚本与参考文档 | `docs/thesis/`、`docs/reference/` |
| `scripts/` | 工具脚本（含源码打包） | [scripts/package-source.sh](scripts/package-source.sh) |

根目录 [README.md](README.md) 为开发总览与功能进度。

## 包内不含什么

以下目录/文件**未打入**源码包，解压后需自行准备或重新生成：

- `outputfile/` — 任务运行输出（滤波 LAS、预览等）
- `terra_las/` — 本地实验点云与模型
- `frontend/node_modules/`、`frontend/dist/` — 前端依赖与构建产物
- `backend/target/` — Maven 编译输出
- `frontend/.env` — 本地环境变量（请从 `frontend/.env.example` 复制）
- `*.joblib` — 机器学习模型文件

实验与答辩请使用**自备 LAS 文件**（绝对路径填入新建任务向导），或先跑通 Mock 链路验证界面。

## 环境要求

| 组件 | 版本建议 |
|------|----------|
| Java | 17+ |
| Maven | 3.9+ |
| PostgreSQL | 14+ |
| Node.js | 18+ |
| Python | 3.10+（网关、滤波、`laspy` 预览） |

## 解压后快速启动

假设解压目录为 `pcfps/`，以下命令均在对应子目录或注明路径下执行。

### 1. 数据库

```bash
# 在 psql 中创建用户与库（需有建库权限）
CREATE USER pcfps WITH PASSWORD 'pcfps';
CREATE DATABASE pcfps OWNER pcfps;

# 建表与演示账号（在仓库根目录）
psql -U pcfps -d pcfps -f backend/db/schema/init_schema.sql
psql -U pcfps -d pcfps -f backend/db/seed/demo-users.sql
```

若数据库为旧版结构，按需执行 `backend/db/schema/upgrade_*.sql`（见 [backend/README.md](backend/README.md)）。

演示登录：**用户名 `demo`，密码 `password`**。

### 2. Python 网关（真实滤波链路）

```bash
pip install -r python_gateway/requirements.txt
# 在仓库根目录，保证可 import python_filter、python_derived
export PYTHONPATH=.
uvicorn python_gateway.main:app --host 127.0.0.1 --port 8000
```

离线滤波 CLI（可选）：

```bash
pip install -r python_filter/requirements.txt
PYTHONPATH=. python -m python_filter --help
```

LAS/LAZ **Web 预览**还需本机 **Python3 + laspy**（后端子进程调用，见 backend README）。

### 3. 后端

```bash
cd backend
mvn spring-boot:run
```

- 默认连接 `http://127.0.0.1:8000` 的 Python 网关。
- 暂不启动 Python 时可用 Mock：`mvn spring-boot:run -Dspring-boot.run.arguments=--spring.profiles.active=mock-python`

环境变量示例：`SPRING_DATASOURCE_URL`、`SPRING_DATASOURCE_USERNAME`、`SPRING_DATASOURCE_PASSWORD`、`JWT_SECRET`、`PYTHON_SERVICE_BASE_URL`（见 backend README）。

### 4. 前端

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

浏览器打开终端提示的地址（默认 `http://localhost:5173`）。`.env` 中 `VITE_API_BASE_URL` 需指向后端（默认 `http://localhost:8080`）。

## 重新打包源码

在源码树内执行：

```bash
./scripts/package-source.sh
# 或指定输出路径
./scripts/package-source.sh ~/Desktop/pcfps-source.zip
```

默认在**上一级目录**生成 `pcfps-source-YYYYMMDD.zip`。

## 各模块文档索引

- 后端 API、预览、环境变量：[backend/README.md](backend/README.md)
- 前端路由与预览约定：[frontend/README.md](frontend/README.md)
- Python 网关契约：[python_gateway/README.md](python_gateway/README.md)
- 滤波算法与 CLI：[python_filter/README.md](python_filter/README.md)
- 实现规约与接口冻结：[delta/3.coding/specification.md](delta/3.coding/specification.md)
