# 实体说明：Python 集成（integration-python）

## PythonJobSubmissionPayloadContract（Spring → Worker）

跨系统视图；Java `PythonJobSubmitCommand` DTO **必须可复制**为该 JSON Schema 子集。

| 字段 | 必填 | 说明 |
|------|------|------|
| `external_business_task_id` | 是 | 幂等/trace；对应 DB `taskId` |
| `input_las_path` | 是 | LAS/LAZ filesystem path readable by algo service account |
| `output_result_path` | 是 | Writer 后缀决定 subset LAS / ascii PCD（业务策略可限制后缀）|
| `filter_method` | 是 | `sor|ror` |
| `sor_neighbor_count` | 条件（method=sor）| 默认 **20** |
| `sor_std_ratio` | 条件（method=sor）| 默认 **1.0** |
| `ror_radius` | 条件（method=ror）| LAS 坐标单位 |
| `ror_min_neighbors` | 条件（method=ror）| 不包含自身 |

校验失败 → **400**，`retryable=false`，错误码：`FILTER_PAYLOAD_INVALID`。

## PythonJobStatusResponseContract（Worker → Spring）

| 字段 | RUNNING/SUCCEEDED/FAILED |
|------|---------------------------|
| `external_python_job_uuid` | 始终返回 |
| `lifecycle_state_machine_token` | `PENDING|RUNNING|SUCCEEDED|FAILED` |
| `progress_ratio_float_optional` | 可选 0–1 |
| `metrics_bundle` | 成功：`N_before`,`N_after`, `timing_total_sec`, 分段 timings |
| `artifact_path_dictionary` | 成功：`FILTERED_LAS` 等 URI 或服务端绝对路径 + 后端再登记 |
| `error_code_stable_string_optional` | 失败必填 |
| `error_message_human_plain_optional` | 失败必填 |
| `retryable_hint_boolean_optional` | 失败；网络类 true，参数类 false |
