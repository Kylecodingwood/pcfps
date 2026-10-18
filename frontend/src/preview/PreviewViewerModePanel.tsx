import { Segmented, Slider, Space, Typography } from "antd";
import { DEFAULT_PREMIUM_VIEWPORT_OPTIONS } from "../viewer/premium/types";

export type PreviewViewerMode = "standard" | "premium";

export interface PreviewViewerModePanelProps {
  viewerMode: PreviewViewerMode;
  onViewerModeChange: (nextMode: PreviewViewerMode) => void;
  previewMaxPointsRequested: number;
  onPreviewMaxPointsChange: (nextValue: number) => void;
  showMaxPointsSlider: boolean;
  premiumPointSizeScale: number;
  onPremiumPointSizeScaleChange: (nextValue: number) => void;
  edlStrength: number;
  onEdlStrengthChange: (nextValue: number) => void;
  edlRadius: number;
  onEdlRadiusChange: (nextValue: number) => void;
}

/**
 * Shared controls for standard vs premium point cloud viewer and preview density.
 */
export function PreviewViewerModePanel(props: PreviewViewerModePanelProps) {
  const {
    viewerMode,
    onViewerModeChange,
    previewMaxPointsRequested,
    onPreviewMaxPointsChange,
    showMaxPointsSlider,
    premiumPointSizeScale,
    onPremiumPointSizeScaleChange,
    edlStrength,
    onEdlStrengthChange,
    edlRadius,
    onEdlRadiusChange,
  } = props;

  return (
    <Space direction="vertical" size="small" style={{ width: "100%", maxWidth: 640, marginBottom: 10 }}>
      <div>
        <Typography.Text>查看器</Typography.Text>
        <Segmented<PreviewViewerMode>
          style={{ marginTop: 6, display: "block" }}
          value={viewerMode}
          onChange={(nextValue) => onViewerModeChange(nextValue)}
          options={[
            { label: "标准", value: "standard" },
            { label: "高保真（Splat+EDL）", value: "premium" },
          ]}
        />
      </div>
      {showMaxPointsSlider ? (
        <div>
          <Typography.Text>预览点数上限（更大更密，但更耗内存与带宽）</Typography.Text>
          <Slider
            min={50_000}
            max={1_000_000}
            step={10_000}
            value={previewMaxPointsRequested}
            onChange={onPreviewMaxPointsChange}
          />
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            当前 {previewMaxPointsRequested.toLocaleString()} 点（服务端均匀抽稀）。
          </Typography.Text>
        </div>
      ) : null}
      {viewerMode === "premium" ? (
        <div>
          <Typography.Text type="secondary" style={{ fontSize: 12, display: "block", marginBottom: 6 }}>
            高保真参数（默认 EDL 强度 {DEFAULT_PREMIUM_VIEWPORT_OPTIONS.edlStrength}）
          </Typography.Text>
          <Typography.Text style={{ fontSize: 12 }}>点大小倍率（过大易呈「气泡」）</Typography.Text>
          <Slider
            min={0.4}
            max={1.8}
            step={0.05}
            value={premiumPointSizeScale}
            onChange={onPremiumPointSizeScaleChange}
          />
          <Typography.Text style={{ fontSize: 12 }}>EDL 强度（描边，过高会显脏）</Typography.Text>
          <Slider min={0} max={2} step={0.05} value={edlStrength} onChange={onEdlStrengthChange} />
          <Typography.Text style={{ fontSize: 12 }}>EDL 邻域半径（像素）</Typography.Text>
          <Slider min={0.5} max={3} step={0.1} value={edlRadius} onChange={onEdlRadiusChange} />
        </div>
      ) : null}
    </Space>
  );
}
