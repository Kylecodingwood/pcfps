# 流程说明：Python 集成（integration-python）

> 与 [requirements.md](../requirements.md) v0.2 **TBD-02** 与本节增补一致。

## 时序（首期）

1. Java **POST /jobs** 提交作业至 Python REST，载荷至少包含：`externalBusinessTaskId`、`inputLasFilesystemPath`、`outputLasFilesystemPath`、`filterMethod`（`sor`|`ror`）及与方法绑定的可选参数分组。
2. Python 校验路径与参数后立即返回 **`202 Accepted`** + `externalPythonJobUuid`。
3. Java 标记任务 **RUNNING** 并开始轮询 `GET /jobs/{externalPythonJobUuid}`。
4. Python Worker 拉起与 CLI 等价的核心函数 `python_filter.pipeline.process(**)`（或通过薄包装子进程）。
5. 成功后响应体带出 **产物路径词典**、`N_*` 指标、耗时拆分；Java 回填 `file-metadata` 并使任务 **SUCCEEDED**；失败则以 `errorCode` + `retryable=false|true`。

## CLI ↔ REST 载荷映射（权威）

| CLI flag | REST JSON key (snake_case 草案) | 类型 |
|----------|---------------------------------|------|
| `--input` | `input_las_path` | string |
| `--output` | `output_result_path` | string |
| `--method` | `filter_method` | enum `sor|ror` |
| `--k` | `sor_neighbor_count` | integer |
| `--std_ratio` | `sor_std_ratio` | number |
| `--radius` | `ror_radius` | number |
| `--min_neighbors` | `ror_min_neighbors` | integer |

> 备注：CLI 已对 `*.las|*.laz|*.pcd` 三种输出 writer 判别；REST 首期建议 **只允许 `.las` 主产物**，PCD **仅预览通道**——防歧义。

## 异步与超时

仍为 **异步 + 轮询**——避免 Java `RestTemplate` 同步阻塞整条 3GB 路径；对齐 `requirements` TBD-02 超时/重试表。
