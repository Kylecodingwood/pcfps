/**
 * Maps Python {@code metrics_bundle} keys (snake_case) to Chinese labels for dual-preview UI.
 */
const DERIVED_METRIC_LABEL_ZH_MAP: Record<string, string> = {
  n_input: "输入点数",
  n_output: "输出点数",
  algorithm_code: "算法代码",
  num_clusters: "簇数量",
  noise_point_count: "噪声点数",
  noise_ratio: "噪声占比",
  wall_time_sec: "耗时（秒）",
  n_ground: "地面点数",
  n_non_ground: "非地面点数",
  n_building: "建筑点数",
  n_vegetation: "植被点数",
  n_other: "其它点数",
  ground_ratio: "地面占比",
  n_removed_34: "删除 3/4 类点数",
  n_ground_in: "精简前地面点数",
  n_ground_out: "精简后地面点数",
  ground_voxel_size_m: "地面体素边长（米）",
  compression_ratio: "相对输入压缩比",
};

/**
 * @param metricKey key from {@code derivedMetrics} JSON
 * @return Chinese label when known; otherwise the original key for display
 */
export function derivedMetricKeyToChineseLabel(metricKey: string): string {
  return DERIVED_METRIC_LABEL_ZH_MAP[metricKey] ?? metricKey;
}
