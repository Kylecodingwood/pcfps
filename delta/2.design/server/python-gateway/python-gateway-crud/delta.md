# python-gateway-crud

> 超时/重试见 [`3.coding/specification.md`](../../../../3.coding/specification.md)。

## 客户端方法（内部 Facade）

| 方法 | 职责 | 超时与重试 |
|------|------|------------|
| `submitFilteringJobBlockingUntilAccepted(command)` | `POST /jobs`，得到 `externalPythonJobUuid` | 连接 **5 s** / 读取 **60 s**；幂等键见下 |
| `pollFilteringJobLifecycleSnapshot(externalUuid)` | `GET /jobs/{uuid}` | 读取 **15 s** |
| `cancelFilteringJob(externalUuid)` | `DELETE`，可选预留 | ---- |

幂等：**`externalBusinessTaskIdUuid`** — Python 若在 DB 已实现重复拒绝或返回既有 job，需要文档化；离线阶段未绑定。

失败映射：

| Python HTTP | Java 行为 |
|-------------|-----------|
| `400` / `FILTER_*` 业务 | 任务 `FAILED`，**不重试** |
| `5xx` / `Timeout` / `IOException` | 任务保持 `RUNNING` 或回退 `PENDING`（实现择一），按规约 **指数退避重试 ≤3** |

## 与算法实现

成功路径建议 **in-process** 调用 `python_filter.pipeline.process`（嵌入 FastAPI worker）以避免子进程序列化开销；Spring 仅见 HTTP。

## 契约细化

OpenAPI YAML 可生成自本表；字段名最终 snake_case vs camelCase 由团队 `ObjectMapper` 统一，**但必须与 `1.req/integration-python/entity.md` 含义一一对应**。
