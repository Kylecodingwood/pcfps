import { Space, Typography } from "antd";
import type { TaskKind } from "../api/types";

/**
 * RGB hex swatches must match {@code rgb_for_semantic_campus} in
 * {@code backend/src/main/resources/scripts/las_preview_sample.py}.
 */
const SEMANTIC_CAMPUS_SWATCH_LIST: ReadonlyArray<{ classLabel: string; hexColor: string }> = [
  { classLabel: "1 地面", hexColor: "#38bf61" },
  { classLabel: "2 建筑", hexColor: "#336beb" },
  { classLabel: "3 植被", hexColor: "#8cd138" },
  { classLabel: "4 其它", hexColor: "#eb9e2e" },
];

const GROUND_NON_GROUND_SWATCH_LIST: ReadonlyArray<{ classLabel: string; hexColor: string }> = [
  { classLabel: "1 地面", hexColor: "#38bf61" },
  { classLabel: "2 非地面", hexColor: "#eb6b2e" },
];

export interface DualPreviewLegendsProps {
  childTaskKind: TaskKind;
  derivedMethod: string;
  /** Parent classify algorithm token when {@code childTaskKind} is {@code SEMANTIC_PRUNE} (palette hint). */
  semanticLegendMethod?: string | null;
}

/**
 * Legend for derived dual-pane: PMF/CSF binary colours, campus semantic four classes, or segment guidance.
 */
export function DualPreviewLegends(props: DualPreviewLegendsProps) {
  const { childTaskKind, derivedMethod, semanticLegendMethod } = props;
  const methodToken = derivedMethod.trim().toLowerCase();
  const semanticLegendToken = (semanticLegendMethod ?? "").trim().toLowerCase();

  if (childTaskKind === "SEGMENT") {
    return (
      <div style={{ marginTop: 10, padding: "8px 12px", background: "var(--ant-color-fill-quaternary, #fafafa)", borderRadius: 8 }}>
        <Typography.Text strong>分割图例说明</Typography.Text>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0, marginTop: 6, fontSize: 13 }}>
          不同颜色表示不同空间簇（实例），不是「所有树同色」的语义类别。灰白系多为噪声或未归入簇的点。
        </Typography.Paragraph>
      </div>
    );
  }

  if (
    childTaskKind === "SEMANTIC_PRUNE" &&
    (semanticLegendToken === "rule_semantic_campus" || semanticLegendToken === "ml_rf_semantic")
  ) {
    const legendTitle = semanticLegendToken === "ml_rf_semantic" ? "语义精简（配色同 RF 1–4 类）" : "语义精简（配色同校园规则语义）";
    return (
      <div style={{ marginTop: 10, padding: "8px 12px", background: "var(--ant-color-fill-quaternary, #fafafa)", borderRadius: 8 }}>
        <Typography.Text strong>{legendTitle}</Typography.Text>
        <Space wrap size={[12, 8]} style={{ marginTop: 8 }}>
          {SEMANTIC_CAMPUS_SWATCH_LIST.map((entry) => (
            <Space key={entry.classLabel} size={6} align="center">
              <span
                style={{
                  display: "inline-block",
                  width: 18,
                  height: 18,
                  borderRadius: 4,
                  background: entry.hexColor,
                  border: "1px solid rgba(0,0,0,0.12)",
                }}
              />
              <Typography.Text style={{ fontSize: 13 }}>{entry.classLabel}</Typography.Text>
            </Space>
          ))}
        </Space>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0, marginTop: 8, fontSize: 12 }}>
          已删除类别 3、4；地面（1）经水平体素抽稀；建筑（2）保留。右侧点云更稀疏属正常。
        </Typography.Paragraph>
      </div>
    );
  }

  if (childTaskKind === "SEMANTIC_PRUNE") {
    return (
      <div style={{ marginTop: 10, padding: "8px 12px", background: "var(--ant-color-fill-quaternary, #fafafa)", borderRadius: 8 }}>
        <Typography.Text strong>语义精简（voxel_drop_ground）</Typography.Text>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0, marginTop: 8, fontSize: 13 }}>
          删除类别 3、4；地面（1）按 XY 体素保留每格最低点；建筑（2）与其它类别保留。若父任务为 PMF/CSF 二分类，图例以「classification」伪彩色为准。
        </Typography.Paragraph>
      </div>
    );
  }

  if (childTaskKind === "CLASSIFY" && (methodToken === "rule_semantic_campus" || methodToken === "ml_rf_semantic")) {
    const legendTitle =
      methodToken === "ml_rf_semantic" ? "RF 有监督语义分类（1–4 类）" : "校园规则语义分类";
    return (
      <div style={{ marginTop: 10, padding: "8px 12px", background: "var(--ant-color-fill-quaternary, #fafafa)", borderRadius: 8 }}>
        <Typography.Text strong>{legendTitle}</Typography.Text>
        <Space wrap size={[12, 8]} style={{ marginTop: 8 }}>
          {SEMANTIC_CAMPUS_SWATCH_LIST.map((entry) => (
            <Space key={entry.classLabel} size={6} align="center">
              <span
                style={{
                  display: "inline-block",
                  width: 18,
                  height: 18,
                  borderRadius: 4,
                  background: entry.hexColor,
                  border: "1px solid rgba(0,0,0,0.12)",
                }}
              />
              <Typography.Text style={{ fontSize: 13 }}>{entry.classLabel}</Typography.Text>
            </Space>
          ))}
        </Space>
      </div>
    );
  }

  if (childTaskKind === "CLASSIFY" && (methodToken === "pmf" || methodToken === "csf")) {
    return (
      <div style={{ marginTop: 10, padding: "8px 12px", background: "var(--ant-color-fill-quaternary, #fafafa)", borderRadius: 8 }}>
        <Typography.Text strong>地面分类（PMF / CSF）</Typography.Text>
        <Space wrap size={[12, 8]} style={{ marginTop: 8 }}>
          {GROUND_NON_GROUND_SWATCH_LIST.map((entry) => (
            <Space key={entry.classLabel} size={6} align="center">
              <span
                style={{
                  display: "inline-block",
                  width: 18,
                  height: 18,
                  borderRadius: 4,
                  background: entry.hexColor,
                  border: "1px solid rgba(0,0,0,0.12)",
                }}
              />
              <Typography.Text style={{ fontSize: 13 }}>{entry.classLabel}</Typography.Text>
            </Space>
          ))}
        </Space>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0, marginTop: 6, fontSize: 12 }}>
          色块与 LAS 预览脚本中 binary 调色一致；右侧需使用「classification」伪彩色。
        </Typography.Paragraph>
      </div>
    );
  }

  return null;
}
