import { Alert, Button, Form, Input, Typography } from "antd";
import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { previewLasPathRequest, resolvePreviewMaxPointsForRequest } from "../api/client";
import type { Point3dDto, PointPreviewResponse } from "../api/types";
import { PointCloudViewport } from "../components/PointCloudViewport";
import { PremiumPointCloudViewport } from "../components/PremiumPointCloudViewport";
import {
  PreviewViewerModePanel,
  type PreviewViewerMode,
} from "../preview/PreviewViewerModePanel";
import { DEFAULT_PREMIUM_VIEWPORT_OPTIONS } from "../viewer/premium/types";

function readInitialSinglePreviewMaxPoints(): number {
  const resolvedFromEnvironment = resolvePreviewMaxPointsForRequest(undefined);
  if (resolvedFromEnvironment !== undefined) {
    return resolvedFromEnvironment;
  }
  return 180_000;
}

/**
 * Mode 1: single LAS path on server, path-based preview API (no task).
 */
function readInitialViewerMode(viewerQuery: string | null): PreviewViewerMode {
  return viewerQuery === "premium" ? "premium" : "standard";
}

export function PreviewSinglePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [lasPathInput, setLasPathInput] = useState("");
  const [previewMaxPointsRequested, setPreviewMaxPointsRequested] = useState(readInitialSinglePreviewMaxPoints);
  const [viewerMode, setViewerMode] = useState<PreviewViewerMode>(() =>
    readInitialViewerMode(searchParams.get("viewer"))
  );
  const [premiumPointSizeScale, setPremiumPointSizeScale] = useState(
    DEFAULT_PREMIUM_VIEWPORT_OPTIONS.pointSizeScale
  );
  const [edlStrength, setEdlStrength] = useState(DEFAULT_PREMIUM_VIEWPORT_OPTIONS.edlStrength);
  const [edlRadius, setEdlRadius] = useState(DEFAULT_PREMIUM_VIEWPORT_OPTIONS.edlRadius);
  const [pointList, setPointList] = useState<Point3dDto[] | null>(null);
  const [previewMeta, setPreviewMeta] = useState<Pick<
    PointPreviewResponse,
    "truncated" | "sourcePointCountEstimate"
  > | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  function handleViewerModeChange(nextMode: PreviewViewerMode) {
    setViewerMode(nextMode);
    const nextParams = new URLSearchParams(searchParams);
    if (nextMode === "premium") {
      nextParams.set("viewer", "premium");
    } else {
      nextParams.delete("viewer");
    }
    const queryString = nextParams.toString();
    void navigate(queryString ? `/preview/single?${queryString}` : "/preview/single", { replace: true });
  }

  async function handlePreview() {
    const trimmedPath = lasPathInput.trim();
    if (!trimmedPath) {
      return;
    }
    setErrorMessage(null);
    setPointList(null);
    setPreviewMeta(null);
    setLoading(true);
    try {
      const previewResponse = await previewLasPathRequest(trimmedPath, previewMaxPointsRequested);
      setPointList(previewResponse.points);
      setPreviewMeta({
        truncated: previewResponse.truncated,
        sourcePointCountEstimate: previewResponse.sourcePointCountEstimate,
      });
    } catch (errorUnknown) {
      const message = errorUnknown instanceof Error ? errorUnknown.message : "预览失败";
      setErrorMessage(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ height: "100%", flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          flexShrink: 0,
          maxHeight: "min(44vh, 420px)",
          overflowY: "auto",
          paddingRight: 4,
        }}
      >
        <Typography.Title level={3} style={{ marginTop: 0, marginBottom: 8 }}>
          单文件抽稀预览
        </Typography.Title>
        <Form layout="vertical" style={{ maxWidth: 720 }} onFinish={() => void handlePreview()}>
          <PreviewViewerModePanel
            viewerMode={viewerMode}
            onViewerModeChange={handleViewerModeChange}
            previewMaxPointsRequested={previewMaxPointsRequested}
            onPreviewMaxPointsChange={setPreviewMaxPointsRequested}
            showMaxPointsSlider
            premiumPointSizeScale={premiumPointSizeScale}
            onPremiumPointSizeScaleChange={setPremiumPointSizeScale}
            edlStrength={edlStrength}
            onEdlStrengthChange={setEdlStrength}
            edlRadius={edlRadius}
            onEdlRadiusChange={setEdlRadius}
          />
          <Form.Item label="LAS / LAZ / ASCII PLY 绝对路径" required style={{ marginBottom: 8 }}>
            <Input.TextArea
              rows={2}
              value={lasPathInput}
              onChange={(event) => setLasPathInput(event.target.value)}
              placeholder="/path/to/cloud.las"
            />
          </Form.Item>
          {errorMessage && <Alert type="error" message={errorMessage} style={{ marginBottom: 8 }} />}
          <Button type="primary" htmlType="submit" loading={loading} disabled={!lasPathInput.trim()}>
            生成预览
          </Button>
        </Form>
      </div>
      <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column", marginTop: 10 }}>
        {viewerMode === "premium" ? (
          <PremiumPointCloudViewport
            label="抽稀预览"
            pointList={pointList}
            truncated={previewMeta?.truncated}
            sourcePointCountEstimate={previewMeta?.sourcePointCountEstimate}
            loading={loading}
            errorMessage={null}
            pointColorHex={0x66ccff}
            premiumPointSizeScale={premiumPointSizeScale}
            edlStrength={edlStrength}
            edlRadius={edlRadius}
          />
        ) : (
          <PointCloudViewport
            label="抽稀预览"
            pointList={pointList}
            truncated={previewMeta?.truncated}
            sourcePointCountEstimate={previewMeta?.sourcePointCountEstimate}
            loading={loading}
            errorMessage={null}
            pointColorHex={0x66ccff}
          />
        )}
      </div>
    </div>
  );
}
