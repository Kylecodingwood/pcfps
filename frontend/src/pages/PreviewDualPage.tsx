import { Alert, Button, Card, Col, Descriptions, Form, Input, Row, Segmented, Space, Typography } from "antd";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  comparisonBundleRequest,
  derivedComparisonBundleRequest,
  previewDualLasPathRequest,
  previewPointsRequest,
  resolvePreviewMaxPointsForRequest,
  semanticPruneComparisonBundleRequest,
} from "../api/client";
import type { FilterRunMetricsDto, Point3dDto, PointPreviewResponse, TaskKind } from "../api/types";
import { derivedMetricKeyToChineseLabel } from "../preview/derivedMetricLabelsZh";
import { DualPanePointViewport } from "../preview/DualPanePointViewport";
import { DualPreviewLegends } from "../preview/DualPreviewLegends";
import {
  PreviewViewerModePanel,
  type PreviewViewerMode,
} from "../preview/PreviewViewerModePanel";
import { DEFAULT_PREMIUM_VIEWPORT_OPTIONS } from "../viewer/premium/types";
import {
  formatPercentForDisplay,
  formatPointCountForDisplay,
  formatSecondsForDisplay,
} from "../preview/formatExperimentMetrics";

function readInitialPreviewMaxPoints(): number {
  const resolvedFromEnvironment = resolvePreviewMaxPointsForRequest(undefined);
  if (resolvedFromEnvironment !== undefined) {
    return resolvedFromEnvironment;
  }
  return 180_000;
}

function readInitialViewerMode(viewerQuery: string | null): PreviewViewerMode {
  return viewerQuery === "premium" ? "premium" : "standard";
}

function formatDerivedMetricValue(metricValue: unknown): string {
  if (metricValue === null || metricValue === undefined) {
    return "—";
  }
  if (typeof metricValue === "number" && Number.isFinite(metricValue)) {
    return Number.isInteger(metricValue) ? String(metricValue) : metricValue.toFixed(6).replace(/\.?0+$/, "");
  }
  return String(metricValue);
}

type WorkspaceSegment = "path" | "filter" | "derived" | "semanticPrune";

/** 双窗画布高度：与布局占位一致，避免 Row 被 flex 压扁后画布仍按 vh 绘制盖住下方指标区。 */
const dualPaneCanvasMinHeightCss = "clamp(280px, 36vh, 540px)";

function resolveWorkspaceSegment(
  childTaskIdRaw: string,
  filterTaskIdRaw: string,
  pruneTaskIdRaw: string,
  workspaceRaw: string
): WorkspaceSegment {
  if (childTaskIdRaw !== "") {
    return "derived";
  }
  if (pruneTaskIdRaw !== "") {
    return "semanticPrune";
  }
  if (filterTaskIdRaw !== "") {
    return "filter";
  }
  if (workspaceRaw === "filter" || workspaceRaw === "derived" || workspaceRaw === "semanticPrune") {
    return workspaceRaw;
  }
  return "path";
}

/**
 * Qt-style single workspace: dual preview for taskId (原始 vs 滤波)、childTaskId（滤波 vs 分割/分类）、或两条服务器路径.
 * Top Segmented switches mode without duplicating preview shells elsewhere.
 */
export function PreviewDualPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const childTaskIdFromQuery = searchParams.get("childTaskId");
  const taskIdFromQuery = searchParams.get("taskId");
  const pruneTaskIdFromQuery = searchParams.get("pruneTaskId");
  const workspaceFromQuery = searchParams.get("workspace")?.trim() ?? "";
  const viewerFromQuery = searchParams.get("viewer");

  const childTaskIdTrimmed = childTaskIdFromQuery?.trim() ?? "";
  const filterTaskIdTrimmed = taskIdFromQuery?.trim() ?? "";
  const pruneTaskIdTrimmed = pruneTaskIdFromQuery?.trim() ?? "";

  const activeWorkspaceSegment = useMemo(
    () => resolveWorkspaceSegment(childTaskIdTrimmed, filterTaskIdTrimmed, pruneTaskIdTrimmed, workspaceFromQuery),
    [childTaskIdTrimmed, filterTaskIdTrimmed, pruneTaskIdTrimmed, workspaceFromQuery]
  );

  const [sourcePathInput, setSourcePathInput] = useState("");
  const [filteredPathInput, setFilteredPathInput] = useState("");

  const [sourcePointList, setSourcePointList] = useState<Point3dDto[] | null>(null);
  const [filteredPointList, setFilteredPointList] = useState<Point3dDto[] | null>(null);
  const [sourcePreviewMeta, setSourcePreviewMeta] = useState<Pick<
    PointPreviewResponse,
    "truncated" | "sourcePointCountEstimate"
  > | null>(null);
  const [filteredPreviewMeta, setFilteredPreviewMeta] = useState<Pick<
    PointPreviewResponse,
    "truncated" | "sourcePointCountEstimate"
  > | null>(null);
  const [sourceErrorMessage, setSourceErrorMessage] = useState<string | null>(null);
  const [filteredErrorMessage, setFilteredErrorMessage] = useState<string | null>(null);
  const [bundleErrorMessage, setBundleErrorMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [taskRunMetrics, setTaskRunMetrics] = useState<FilterRunMetricsDto | null>(null);
  const [derivedMetricsRecord, setDerivedMetricsRecord] = useState<Record<string, unknown> | null>(null);
  const [leftViewportLabel, setLeftViewportLabel] = useState("原始（抽稀）");
  const [rightViewportLabel, setRightViewportLabel] = useState("第二侧（抽稀）");

  const [filterTaskIdDraft, setFilterTaskIdDraft] = useState("");
  const [derivedChildTaskIdDraft, setDerivedChildTaskIdDraft] = useState("");
  const [semanticPruneTaskIdDraft, setSemanticPruneTaskIdDraft] = useState("");
  const [previewMaxPointsRequested, setPreviewMaxPointsRequested] = useState(readInitialPreviewMaxPoints);
  const [viewerMode, setViewerMode] = useState<PreviewViewerMode>(() => readInitialViewerMode(viewerFromQuery));
  const [premiumPointSizeScale, setPremiumPointSizeScale] = useState(
    DEFAULT_PREMIUM_VIEWPORT_OPTIONS.pointSizeScale
  );
  const [edlStrength, setEdlStrength] = useState(DEFAULT_PREMIUM_VIEWPORT_OPTIONS.edlStrength);
  const [edlRadius, setEdlRadius] = useState(DEFAULT_PREMIUM_VIEWPORT_OPTIONS.edlRadius);
  const [derivedLegendTaskKind, setDerivedLegendTaskKind] = useState<TaskKind | null>(null);
  const [derivedLegendMethod, setDerivedLegendMethod] = useState<string>("");
  const [semanticLegendMethod, setSemanticLegendMethod] = useState<string>("");

  function handleViewerModeChange(nextMode: PreviewViewerMode) {
    setViewerMode(nextMode);
    const nextParams = new URLSearchParams(searchParams);
    if (nextMode === "premium") {
      nextParams.set("viewer", "premium");
    } else {
      nextParams.delete("viewer");
    }
    const queryString = nextParams.toString();
    void navigate(queryString ? `/preview/dual?${queryString}` : "/preview/dual", { replace: true });
  }

  function handleWorkspaceSegmentChange(nextSegment: WorkspaceSegment) {
    if (nextSegment === "semanticPrune") {
      if (pruneTaskIdTrimmed !== "") {
        void navigate(`/preview/dual?pruneTaskId=${encodeURIComponent(pruneTaskIdTrimmed)}`, { replace: true });
        return;
      }
      void navigate("/preview/dual?workspace=semanticPrune", { replace: true });
      return;
    }
    if (nextSegment === "path") {
      void navigate("/preview/dual", { replace: true });
      return;
    }
    if (nextSegment === "filter") {
      if (filterTaskIdTrimmed !== "") {
        void navigate(`/preview/dual?taskId=${encodeURIComponent(filterTaskIdTrimmed)}`, { replace: true });
        return;
      }
      void navigate("/preview/dual?workspace=filter", { replace: true });
      return;
    }
    if (childTaskIdTrimmed !== "") {
      void navigate(`/preview/dual?childTaskId=${encodeURIComponent(childTaskIdTrimmed)}`, { replace: true });
      return;
    }
    void navigate("/preview/dual?workspace=derived", { replace: true });
  }

  useEffect(() => {
    if (childTaskIdTrimmed !== "") {
      let cancelled = false;

      async function loadFromDerivedChildTask() {
        setBundleErrorMessage(null);
        setSourceErrorMessage(null);
        setFilteredErrorMessage(null);
        setSourcePointList(null);
        setFilteredPointList(null);
        setSourcePreviewMeta(null);
        setFilteredPreviewMeta(null);
        setTaskRunMetrics(null);
        setDerivedMetricsRecord(null);
        setDerivedLegendTaskKind(null);
        setDerivedLegendMethod("");
        setSemanticLegendMethod("");
        setLoading(true);
        try {
          const derivedBundle = await derivedComparisonBundleRequest(childTaskIdTrimmed);
          if (cancelled) {
            return;
          }
          setDerivedLegendTaskKind(derivedBundle.childTaskKind);
          setDerivedLegendMethod(derivedBundle.derivedMethod ?? "");
          setDerivedMetricsRecord(derivedBundle.derivedMetrics ?? {});
          setLeftViewportLabel(`${derivedBundle.leftLabel}（抽稀）`);
          setRightViewportLabel(`${derivedBundle.rightLabel}（抽稀）`);
          const previewBodyLeft = { maxPoints: previewMaxPointsRequested };
          const previewBodyRight = { maxPoints: previewMaxPointsRequested, colorMode: "classification" as const };
          const leftPreviewPromise = previewPointsRequest(derivedBundle.leftFileId, previewBodyLeft).catch((errorUnknown: unknown) => {
            const message = errorUnknown instanceof Error ? errorUnknown.message : "左侧预览失败";
            return { error: message as string };
          });
          const rightPreviewPromise = previewPointsRequest(derivedBundle.rightFileId, previewBodyRight).catch((errorUnknown: unknown) => {
            const message = errorUnknown instanceof Error ? errorUnknown.message : "右侧预览失败";
            return { error: message as string };
          });
          const [leftOutcome, rightOutcome] = await Promise.all([leftPreviewPromise, rightPreviewPromise]);
          if (cancelled) {
            return;
          }
          if ("error" in leftOutcome) {
            setSourceErrorMessage(leftOutcome.error);
          } else {
            setSourcePointList(leftOutcome.points);
            setSourcePreviewMeta({
              truncated: leftOutcome.truncated,
              sourcePointCountEstimate: leftOutcome.sourcePointCountEstimate,
            });
          }
          if ("error" in rightOutcome) {
            setFilteredErrorMessage(rightOutcome.error);
          } else {
            setFilteredPointList(rightOutcome.points);
            setFilteredPreviewMeta({
              truncated: rightOutcome.truncated,
              sourcePointCountEstimate: rightOutcome.sourcePointCountEstimate,
            });
          }
        } catch (errorUnknown) {
          if (!cancelled) {
            const message = errorUnknown instanceof Error ? errorUnknown.message : "加载失败";
            setBundleErrorMessage(message);
          }
        } finally {
          if (!cancelled) {
            setLoading(false);
          }
        }
      }

      void loadFromDerivedChildTask();
      return () => {
        cancelled = true;
      };
    }

    if (pruneTaskIdTrimmed !== "") {
      let cancelled = false;

      async function loadFromSemanticPruneTask() {
        setBundleErrorMessage(null);
        setSourceErrorMessage(null);
        setFilteredErrorMessage(null);
        setSourcePointList(null);
        setFilteredPointList(null);
        setSourcePreviewMeta(null);
        setFilteredPreviewMeta(null);
        setTaskRunMetrics(null);
        setDerivedMetricsRecord(null);
        setDerivedLegendTaskKind(null);
        setDerivedLegendMethod("");
        setSemanticLegendMethod("");
        setLoading(true);
        try {
          const semanticBundle = await semanticPruneComparisonBundleRequest(pruneTaskIdTrimmed);
          if (cancelled) {
            return;
          }
          setDerivedLegendTaskKind(semanticBundle.childTaskKind);
          setDerivedLegendMethod(semanticBundle.derivedMethod ?? "");
          setSemanticLegendMethod(semanticBundle.semanticLegendMethod ?? "");
          setDerivedMetricsRecord(semanticBundle.derivedMetrics ?? {});
          setLeftViewportLabel(`${semanticBundle.leftLabel}（抽稀）`);
          setRightViewportLabel(`${semanticBundle.rightLabel}（抽稀）`);
          const previewBodyLeft = { maxPoints: previewMaxPointsRequested, colorMode: "classification" as const };
          const previewBodyRight = { maxPoints: previewMaxPointsRequested, colorMode: "classification" as const };
          const leftPreviewPromise = previewPointsRequest(semanticBundle.leftFileId, previewBodyLeft).catch((errorUnknown: unknown) => {
            const message = errorUnknown instanceof Error ? errorUnknown.message : "左侧预览失败";
            return { error: message as string };
          });
          const rightPreviewPromise = previewPointsRequest(semanticBundle.rightFileId, previewBodyRight).catch((errorUnknown: unknown) => {
            const message = errorUnknown instanceof Error ? errorUnknown.message : "右侧预览失败";
            return { error: message as string };
          });
          const [leftOutcome, rightOutcome] = await Promise.all([leftPreviewPromise, rightPreviewPromise]);
          if (cancelled) {
            return;
          }
          if ("error" in leftOutcome) {
            setSourceErrorMessage(leftOutcome.error);
          } else {
            setSourcePointList(leftOutcome.points);
            setSourcePreviewMeta({
              truncated: leftOutcome.truncated,
              sourcePointCountEstimate: leftOutcome.sourcePointCountEstimate,
            });
          }
          if ("error" in rightOutcome) {
            setFilteredErrorMessage(rightOutcome.error);
          } else {
            setFilteredPointList(rightOutcome.points);
            setFilteredPreviewMeta({
              truncated: rightOutcome.truncated,
              sourcePointCountEstimate: rightOutcome.sourcePointCountEstimate,
            });
          }
        } catch (errorUnknown) {
          if (!cancelled) {
            const message = errorUnknown instanceof Error ? errorUnknown.message : "加载失败";
            setBundleErrorMessage(message);
          }
        } finally {
          if (!cancelled) {
            setLoading(false);
          }
        }
      }

      void loadFromSemanticPruneTask();
      return () => {
        cancelled = true;
      };
    }

    if (filterTaskIdTrimmed !== "") {
      let cancelled = false;

      async function loadFromFilterTask() {
        setBundleErrorMessage(null);
        setSourceErrorMessage(null);
        setFilteredErrorMessage(null);
        setSourcePointList(null);
        setFilteredPointList(null);
        setSourcePreviewMeta(null);
        setFilteredPreviewMeta(null);
        setTaskRunMetrics(null);
        setDerivedMetricsRecord(null);
        setDerivedLegendTaskKind(null);
        setDerivedLegendMethod("");
        setSemanticLegendMethod("");
        setLeftViewportLabel("原始（抽稀）");
        setRightViewportLabel("滤波结果（抽稀）");
        setLoading(true);
        try {
          const bundle = await comparisonBundleRequest(filterTaskIdTrimmed);
          setTaskRunMetrics(bundle.runMetrics ?? null);
          const sourceAsset = bundle.assets.find((asset) => asset.role === "SOURCE_LAS");
          const filteredAsset = bundle.assets.find((asset) => asset.role === "FILTERED_LAS");
          if (!sourceAsset || !filteredAsset) {
            setBundleErrorMessage("缺少 SOURCE_LAS 或 FILTERED_LAS（任务需已成功）");
            setLoading(false);
            return;
          }
          const previewBody = { maxPoints: previewMaxPointsRequested };
          const sourcePreviewPromise = previewPointsRequest(sourceAsset.fileId, previewBody).catch((errorUnknown: unknown) => {
            const message = errorUnknown instanceof Error ? errorUnknown.message : "原始预览失败";
            return { error: message as string };
          });
          const filteredPreviewPromise = previewPointsRequest(filteredAsset.fileId, previewBody).catch((errorUnknown: unknown) => {
            const message = errorUnknown instanceof Error ? errorUnknown.message : "滤波预览失败";
            return { error: message as string };
          });
          const [sourceOutcome, filteredOutcome] = await Promise.all([sourcePreviewPromise, filteredPreviewPromise]);
          if (cancelled) {
            return;
          }
          if ("error" in sourceOutcome) {
            setSourceErrorMessage(sourceOutcome.error);
          } else {
            setSourcePointList(sourceOutcome.points);
            setSourcePreviewMeta({
              truncated: sourceOutcome.truncated,
              sourcePointCountEstimate: sourceOutcome.sourcePointCountEstimate,
            });
          }
          if ("error" in filteredOutcome) {
            setFilteredErrorMessage(filteredOutcome.error);
          } else {
            setFilteredPointList(filteredOutcome.points);
            setFilteredPreviewMeta({
              truncated: filteredOutcome.truncated,
              sourcePointCountEstimate: filteredOutcome.sourcePointCountEstimate,
            });
          }
        } catch (errorUnknown) {
          if (!cancelled) {
            const message = errorUnknown instanceof Error ? errorUnknown.message : "加载失败";
            setBundleErrorMessage(message);
          }
        } finally {
          if (!cancelled) {
            setLoading(false);
          }
        }
      }

      void loadFromFilterTask();
      return () => {
        cancelled = true;
      };
    }

    return undefined;
  }, [childTaskIdTrimmed, filterTaskIdTrimmed, pruneTaskIdTrimmed, previewMaxPointsRequested]);

  async function handlePathDualPreview() {
    const sourceTrimmed = sourcePathInput.trim();
    const filteredTrimmed = filteredPathInput.trim();
    if (!sourceTrimmed || !filteredTrimmed) {
      return;
    }
    setBundleErrorMessage(null);
    setSourceErrorMessage(null);
    setFilteredErrorMessage(null);
    setSourcePointList(null);
    setFilteredPointList(null);
    setSourcePreviewMeta(null);
    setFilteredPreviewMeta(null);
    setTaskRunMetrics(null);
    setDerivedMetricsRecord(null);
    setDerivedLegendTaskKind(null);
    setDerivedLegendMethod("");
    setSemanticLegendMethod("");
    setLeftViewportLabel("原始（抽稀）");
    setRightViewportLabel("第二路径（抽稀）");
    setLoading(true);
    try {
      const dualResponse = await previewDualLasPathRequest(sourceTrimmed, filteredTrimmed, previewMaxPointsRequested);
      setSourcePointList(dualResponse.sourcePreview.points);
      setFilteredPointList(dualResponse.filteredPreview.points);
      setSourcePreviewMeta({
        truncated: dualResponse.sourcePreview.truncated,
        sourcePointCountEstimate: dualResponse.sourcePreview.sourcePointCountEstimate,
      });
      setFilteredPreviewMeta({
        truncated: dualResponse.filteredPreview.truncated,
        sourcePointCountEstimate: dualResponse.filteredPreview.sourcePointCountEstimate,
      });
    } catch (errorUnknown) {
      const message = errorUnknown instanceof Error ? errorUnknown.message : "预览失败";
      setBundleErrorMessage(message);
    } finally {
      setLoading(false);
    }
  }

  const isDerivedChildMode = childTaskIdTrimmed !== "";
  const isSemanticPruneTaskMode = pruneTaskIdTrimmed !== "";
  const isFilterTaskMode = filterTaskIdTrimmed !== "" && !isDerivedChildMode && !isSemanticPruneTaskMode;
  const isTaskBundleUi = isDerivedChildMode || isFilterTaskMode || isSemanticPruneTaskMode;
  const showFilterTaskIdChooser = activeWorkspaceSegment === "filter" && filterTaskIdTrimmed === "";
  const showDerivedChildTaskIdChooser = activeWorkspaceSegment === "derived" && childTaskIdTrimmed === "";
  const showSemanticPruneTaskIdChooser = activeWorkspaceSegment === "semanticPrune" && pruneTaskIdTrimmed === "";
  const showPathDualForm = activeWorkspaceSegment === "path";

  const hasFullRunMetrics =
    taskRunMetrics != null &&
    (taskRunMetrics.nBefore != null ||
      taskRunMetrics.nAfter != null ||
      taskRunMetrics.timingTotalSec != null);

  const timingBreakdownVisible =
    taskRunMetrics != null &&
    (taskRunMetrics.timingDecodeSec != null ||
      taskRunMetrics.timingFilterSec != null ||
      taskRunMetrics.timingWriteSec != null);

  const hasDerivedMetricsPanel =
    derivedMetricsRecord != null && Object.keys(derivedMetricsRecord).length > 0;

  const pageTitle = isSemanticPruneTaskMode
    ? "分类 vs 语义精简（双窗）"
    : isDerivedChildMode
      ? "滤波 vs 分割/分类（双窗）"
      : isFilterTaskMode
        ? "原始 vs 滤波（双窗）"
        : showFilterTaskIdChooser
          ? "滤波对比（输入任务 ID）"
          : showDerivedChildTaskIdChooser
            ? "派生双窗（输入子任务 ID）"
            : showSemanticPruneTaskIdChooser
              ? "语义精简双窗（输入子任务 ID）"
              : "路径双窗预览";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 16,
        width: "100%",
        paddingBottom: 24,
      }}
    >
      <div style={{ flexShrink: 0, paddingRight: 4 }}>
        <Typography.Title level={3} style={{ marginTop: 0, marginBottom: 8 }}>
          {pageTitle}
        </Typography.Title>

        <div style={{ marginBottom: 10 }}>
          <Segmented<WorkspaceSegment>
            value={activeWorkspaceSegment}
            onChange={(value) => handleWorkspaceSegmentChange(value)}
            options={[
              { label: "滤波对比", value: "filter" },
              { label: "派生双窗", value: "derived" },
              { label: "语义精简双窗", value: "semanticPrune" },
              { label: "路径双窗", value: "path" },
            ]}
          />
          <Typography.Text type="secondary" style={{ marginLeft: 12, fontSize: 13 }}>
            单路径预览见 <Link to="/preview/single">单文件抽稀</Link>
          </Typography.Text>
        </div>

        {isTaskBundleUi ? (
          <Space style={{ marginBottom: 8 }} wrap>
            <Link to="/jobs">返回任务列表</Link>
            <Link to="/preview/dual">路径双窗（清空 query）</Link>
          </Space>
        ) : null}

        {bundleErrorMessage ? <Alert type="error" message={bundleErrorMessage} style={{ marginBottom: 8 }} /> : null}

        {showFilterTaskIdChooser || showDerivedChildTaskIdChooser || showSemanticPruneTaskIdChooser ? (
          <Space direction="vertical" style={{ width: "100%", marginBottom: 12 }} size="middle">
            <Typography.Title level={5} style={{ margin: 0 }}>
              加载任务（滤波 / 派生 / 语义精简）
            </Typography.Title>
            {showFilterTaskIdChooser ? (
              <Card size="small" title="加载滤波任务双窗">
                <Space direction="vertical" style={{ width: "100%" }} size="middle">
                  <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
                    输入已成功滤波的父任务 UUID，或从任务列表点击「对比预览」。
                  </Typography.Paragraph>
                  <Space.Compact style={{ maxWidth: 520, width: "100%" }}>
                    <Input
                      placeholder="taskId（UUID）"
                      value={filterTaskIdDraft}
                      onChange={(event) => setFilterTaskIdDraft(event.target.value)}
                    />
                    <Button
                      type="primary"
                      onClick={() => {
                        const trimmed = filterTaskIdDraft.trim();
                        if (!trimmed) {
                          return;
                        }
                        void navigate(`/preview/dual?taskId=${encodeURIComponent(trimmed)}`);
                      }}
                    >
                      加载
                    </Button>
                  </Space.Compact>
                  <Link to="/jobs">去任务列表</Link>
                </Space>
              </Card>
            ) : null}
            {showDerivedChildTaskIdChooser ? (
              <Card size="small" title="加载派生子任务双窗">
                <Space direction="vertical" style={{ width: "100%" }} size="middle">
                  <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
                    输入已成功完成的派生任务（分割/分类）UUID，或从任务列表点击「派生双窗」。
                  </Typography.Paragraph>
                  <Space.Compact style={{ maxWidth: 520, width: "100%" }}>
                    <Input
                      placeholder="childTaskId（UUID）"
                      value={derivedChildTaskIdDraft}
                      onChange={(event) => setDerivedChildTaskIdDraft(event.target.value)}
                    />
                    <Button
                      type="primary"
                      onClick={() => {
                        const trimmed = derivedChildTaskIdDraft.trim();
                        if (!trimmed) {
                          return;
                        }
                        void navigate(`/preview/dual?childTaskId=${encodeURIComponent(trimmed)}`);
                      }}
                    >
                      加载
                    </Button>
                  </Space.Compact>
                  <Link to="/jobs">去任务列表</Link>
                </Space>
              </Card>
            ) : null}
            {showSemanticPruneTaskIdChooser ? (
              <Card size="small" title="加载语义精简子任务双窗">
                <Space direction="vertical" style={{ width: "100%" }} size="middle">
                  <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
                    输入已成功完成的「语义精简」子任务 UUID，或从任务列表点击「语义精简双窗」。
                  </Typography.Paragraph>
                  <Space.Compact style={{ maxWidth: 520, width: "100%" }}>
                    <Input
                      placeholder="pruneTaskId（UUID）"
                      value={semanticPruneTaskIdDraft}
                      onChange={(event) => setSemanticPruneTaskIdDraft(event.target.value)}
                    />
                    <Button
                      type="primary"
                      onClick={() => {
                        const trimmed = semanticPruneTaskIdDraft.trim();
                        if (!trimmed) {
                          return;
                        }
                        void navigate(`/preview/dual?pruneTaskId=${encodeURIComponent(trimmed)}`);
                      }}
                    >
                      加载
                    </Button>
                  </Space.Compact>
                  <Link to="/jobs">去任务列表</Link>
                </Space>
              </Card>
            ) : null}
          </Space>
        ) : null}

        {showPathDualForm ? (
          <div style={{ marginBottom: 12 }}>
            <Typography.Title level={5} style={{ marginBottom: 8 }}>
              路径双窗（服务器绝对路径）
            </Typography.Title>
            <Form layout="vertical" style={{ maxWidth: 720 }} onFinish={() => void handlePathDualPreview()}>
              <Form.Item label="原始 LAS / LAZ / PLY 路径" required>
                <Input.TextArea
                  rows={2}
                  value={sourcePathInput}
                  onChange={(event) => setSourcePathInput(event.target.value)}
                  placeholder="/path/to/source.las"
                />
              </Form.Item>
              <Form.Item label="第二路径 LAS / LAZ / PLY" required>
                <Input.TextArea
                  rows={2}
                  value={filteredPathInput}
                  onChange={(event) => setFilteredPathInput(event.target.value)}
                  placeholder="/path/to/filtered.las"
                />
              </Form.Item>
              {bundleErrorMessage ? <Alert type="error" message={bundleErrorMessage} style={{ marginBottom: 12 }} /> : null}
              <Button type="primary" htmlType="submit" loading={loading}>
                生成双窗预览
              </Button>
            </Form>
          </div>
        ) : null}

        {(isFilterTaskMode || isDerivedChildMode || isSemanticPruneTaskMode) && !bundleErrorMessage ? (
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
        ) : showPathDualForm ? (
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
        ) : null}
      </div>

      <Row gutter={[12, 12]} style={{ width: "100%", flexShrink: 0 }} align="stretch">
        <Col xs={24} lg={12} style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
          <DualPanePointViewport
            viewerMode={viewerMode}
            premiumPointSizeScale={premiumPointSizeScale}
            edlStrength={edlStrength}
            edlRadius={edlRadius}
            label={leftViewportLabel}
            pointList={sourcePointList}
            truncated={sourcePreviewMeta?.truncated}
            sourcePointCountEstimate={sourcePreviewMeta?.sourcePointCountEstimate}
            loading={loading}
            errorMessage={sourceErrorMessage}
            pointColorHex={0xff9944}
            canvasMinHeightCss={dualPaneCanvasMinHeightCss}
          />
        </Col>
        <Col xs={24} lg={12} style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
          <DualPanePointViewport
            viewerMode={viewerMode}
            premiumPointSizeScale={premiumPointSizeScale}
            edlStrength={edlStrength}
            edlRadius={edlRadius}
            label={rightViewportLabel}
            pointList={filteredPointList}
            truncated={filteredPreviewMeta?.truncated}
            sourcePointCountEstimate={filteredPreviewMeta?.sourcePointCountEstimate}
            loading={loading}
            errorMessage={filteredErrorMessage}
            pointColorHex={0x66ccff}
            canvasMinHeightCss={dualPaneCanvasMinHeightCss}
          />
        </Col>
      </Row>

      {(isDerivedChildMode || isSemanticPruneTaskMode) && derivedLegendTaskKind ? (
        <DualPreviewLegends
          childTaskKind={derivedLegendTaskKind}
          derivedMethod={derivedLegendMethod}
          semanticLegendMethod={semanticLegendMethod}
        />
      ) : null}

      {isTaskBundleUi ? (
        <div style={{ flexShrink: 0, paddingRight: 4 }}>
          <Typography.Title level={5} style={{ marginTop: 0, marginBottom: 10 }}>
            实验指标与说明
          </Typography.Title>
          <Space direction="vertical" style={{ width: "100%" }} size="middle">
            {(isDerivedChildMode || isSemanticPruneTaskMode) && !bundleErrorMessage && hasDerivedMetricsPanel && derivedMetricsRecord ? (
              <Card title="派生 / 语义精简 实验数据（metrics_bundle）" size="small">
                <Descriptions column={1} size="small" bordered>
                  {Object.entries(derivedMetricsRecord).map(([metricKey, metricValue]) => (
                    <Descriptions.Item key={metricKey} label={derivedMetricKeyToChineseLabel(metricKey)}>
                      {formatDerivedMetricValue(metricValue)}
                    </Descriptions.Item>
                  ))}
                </Descriptions>
                <Typography.Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0, fontSize: 13 }}>
                  {isSemanticPruneTaskMode
                    ? "左侧为父分类输出，右侧为语义精简后；两侧均为 classification 伪彩色（抽稀预览）。"
                    : "左侧为父任务滤波结果，右侧为子任务输出；点云为 preview-points 抽稀（右侧 classification 伪彩色）。"}
                </Typography.Paragraph>
              </Card>
            ) : null}
            {isFilterTaskMode && !bundleErrorMessage && hasFullRunMetrics ? (
              <Card title="滤波实验指标（全量 LAS，来自 Python metrics）" size="small">
                <Descriptions column={1} size="small" bordered>
                  <Descriptions.Item label="原始点数">
                    {formatPointCountForDisplay(taskRunMetrics?.nBefore ?? null)}
                  </Descriptions.Item>
                  <Descriptions.Item label="滤波后点数">
                    {formatPointCountForDisplay(taskRunMetrics?.nAfter ?? null)}
                  </Descriptions.Item>
                  <Descriptions.Item label="去除比例">
                    {formatPercentForDisplay(taskRunMetrics?.removalRatioPercent ?? null)}
                  </Descriptions.Item>
                  <Descriptions.Item label="处理总耗时">
                    {formatSecondsForDisplay(taskRunMetrics?.timingTotalSec ?? null)}
                  </Descriptions.Item>
                  {timingBreakdownVisible ? (
                    <Descriptions.Item label="阶段耗时（解码 / 滤波 / 写出）">
                      {`${formatSecondsForDisplay(taskRunMetrics?.timingDecodeSec ?? null)} / ${formatSecondsForDisplay(
                        taskRunMetrics?.timingFilterSec ?? null,
                      )} / ${formatSecondsForDisplay(taskRunMetrics?.timingWriteSec ?? null)}`}
                    </Descriptions.Item>
                  ) : null}
                </Descriptions>
                <Typography.Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0, fontSize: 13 }}>
                  点云为 preview-points 抽稀结果，与上表全量点数不同属正常。
                </Typography.Paragraph>
              </Card>
            ) : null}
            {(isDerivedChildMode || isSemanticPruneTaskMode) && !bundleErrorMessage && !loading && !hasDerivedMetricsPanel ? (
              <Alert
                type="warning"
                showIcon
                message="无派生 / 语义精简任务指标"
                description="例如 Mock 或未落库 metrics；仍可通过两侧点云查看效果。"
              />
            ) : null}
            {isFilterTaskMode && !bundleErrorMessage && !loading && !hasFullRunMetrics ? (
              <Alert
                type="warning"
                showIcon
                message="无全量滤波指标"
                description="例如 Mock 模式、历史任务或未落库 metrics；两侧点数请以预览抽稀估计为准。"
              />
            ) : null}
          </Space>
        </div>
      ) : null}
    </div>
  );
}
