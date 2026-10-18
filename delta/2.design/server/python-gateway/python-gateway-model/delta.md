# python-gateway-model

> 与 [`python-gateway-api/delta.md`](../python-gateway-api/delta.md)、[`1.req/integration-python/entity.md`](../../../../1.req/integration-python/entity.md) 对齐。

## Java DTO 草案 → JSON 别名

### `PythonJobSubmitCommandAggregate`

用于 `WebClient` body 组装。

| Java field | JSON key (`objectMapper` camelCase 建议) |
|------------|-----------------------------------------|
| `externalBusinessTaskIdUuid` | `externalBusinessTaskId` |
| `inputLasFilesystemPathString` | `inputLasPath` |
| `outputResultFilesystemPathString` | `outputResultPath` |
| `filterMethodEnumerationTokenPlain` (`SOR`,`ROR`) | `filterMethod` |
| `sorNeighborCountIntegerOptional` | `sorNeighborCount` |
| `sorStdRatioDoubleOptional` | `sorStdRatio` |
| `rorRadiusDoubleOptional` | `rorRadius` |
| `rorMinNeighborsExclusiveIntegerOptional` | `rorMinNeighbors` |

> 默认值：与方法无关字段忽略；与方法冲突参数 → validator 报错。

映射关系：等价于 `--k/--std_ratio/--radius/--min_neighbors`。

### `PythonJobStatusPollView`

| Java field | JSON key |
|------------|----------|
| `externalPythonJobUuid` | id |
| `lifecycleStateEnumeration` | lifecycleState |
| `metricsTimingBundleView` | metrics |
| `artifactRoleToPathDictionary` | artifacts |
| `integrationErrorStableCodeOptional` | errorCode |

### `TimingMetricsBundleNestedRecord`

封装 `timingTotalSeconds`, `timingDecodeSeconds`, `timingFilterSeconds`, `timingWriteSeconds`,
`originalPointRowCountBeforeInteger`, `filteredPointRowCountAfterInteger`.
