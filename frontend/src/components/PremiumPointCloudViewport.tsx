import { useEffect, useRef } from "react";
import type { PointCloudViewportProps } from "./PointCloudViewport";
import {
  applyPremiumViewerOptions,
  mountPremiumViewer,
  resizePremiumViewer,
  type PremiumViewerRuntime,
} from "../viewer/premium/createPremiumViewer";
import { disposePremiumViewer } from "../viewer/premium/disposePremiumViewer";
import type { PremiumViewportOptions } from "../viewer/premium/types";
import { DEFAULT_PREMIUM_VIEWPORT_OPTIONS } from "../viewer/premium/types";

export interface PremiumPointCloudViewportProps extends PointCloudViewportProps {
  premiumPointSizeScale?: number;
  edlStrength?: number;
  edlRadius?: number;
}

/**
 * High-fidelity point preview: splat shader + Eye-Dome Lighting post-process.
 */
export function PremiumPointCloudViewport(props: PremiumPointCloudViewportProps) {
  const {
    label,
    pointList,
    truncated,
    sourcePointCountEstimate,
    loading,
    errorMessage,
    pointColorHex,
    canvasMinHeightCss,
    premiumPointSizeScale,
    edlStrength,
    edlRadius,
  } = props;
  const resolvedPointColor = pointColorHex ?? 0x66ccff;
  const containerRef = useRef<HTMLDivElement | null>(null);
  const runtimeRef = useRef<PremiumViewerRuntime | null>(null);

  const premiumOptionsRef = useRef<PremiumViewportOptions>({ ...DEFAULT_PREMIUM_VIEWPORT_OPTIONS });
  premiumOptionsRef.current = {
    pointSizeScale: premiumPointSizeScale ?? DEFAULT_PREMIUM_VIEWPORT_OPTIONS.pointSizeScale,
    edlStrength: edlStrength ?? DEFAULT_PREMIUM_VIEWPORT_OPTIONS.edlStrength,
    edlRadius: edlRadius ?? DEFAULT_PREMIUM_VIEWPORT_OPTIONS.edlRadius,
  };

  useEffect(() => {
    const containerElement = containerRef.current;
    if (!containerElement || !pointList || pointList.length === 0 || loading || errorMessage) {
      return;
    }

    disposePremiumViewer(runtimeRef.current);
    runtimeRef.current = mountPremiumViewer({
      containerElement,
      pointList,
      pointColorHex: resolvedPointColor,
      premiumOptions: premiumOptionsRef.current,
    });

    function applyViewportSizeFromDom(): void {
      const runtime = runtimeRef.current;
      const containerActive = containerRef.current;
      if (!runtime || !containerActive) {
        return;
      }
      resizePremiumViewer(
        runtime,
        Math.max(1, Math.floor(containerActive.clientWidth)),
        Math.max(240, Math.floor(containerActive.clientHeight))
      );
    }

    const resizeObserver = new ResizeObserver(() => applyViewportSizeFromDom());
    resizeObserver.observe(containerElement);
    window.addEventListener("resize", applyViewportSizeFromDom);
    applyViewportSizeFromDom();

    return () => {
      window.removeEventListener("resize", applyViewportSizeFromDom);
      resizeObserver.disconnect();
      disposePremiumViewer(runtimeRef.current);
      runtimeRef.current = null;
    };
  }, [pointList, resolvedPointColor, loading, errorMessage]);

  useEffect(() => {
    const runtime = runtimeRef.current;
    if (!runtime || !pointList || pointList.length === 0) {
      return;
    }
    applyPremiumViewerOptions(runtime, premiumOptionsRef.current);
  }, [premiumPointSizeScale, edlStrength, edlRadius, pointList]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        flex: 1,
        minHeight: 0,
        minWidth: 0,
      }}
    >
      <h3 style={{ margin: "0 0 8px", fontSize: "1rem", flexShrink: 0 }}>{label}</h3>
      {loading && <p style={{ color: "#888", flexShrink: 0 }}>加载预览点…</p>}
      {errorMessage && <p style={{ color: "crimson", flexShrink: 0 }}>{errorMessage}</p>}
      {!loading && !errorMessage && (!pointList || pointList.length === 0) && (
        <p style={{ color: "#888", flexShrink: 0 }}>无预览点</p>
      )}
      {truncated !== undefined && (
        <p style={{ fontSize: 12, color: "#888", margin: "4px 0", flexShrink: 0 }}>
          高保真预览（Splat + EDL）· 服务端抽稀{truncated ? "（已截断）" : ""}
          {sourcePointCountEstimate !== undefined && sourcePointCountEstimate > 0
            ? ` · 估计总点数约 ${sourcePointCountEstimate}`
            : ""}
        </p>
      )}
      <div
        ref={containerRef}
        style={{
          flex: 1,
          width: "100%",
          minWidth: 0,
          border: "1px solid #333",
          borderRadius: 6,
          minHeight: canvasMinHeightCss ?? "max(280px, min(58vh, 820px))",
        }}
      />
    </div>
  );
}
