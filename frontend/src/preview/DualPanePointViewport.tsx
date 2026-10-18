import { PointCloudViewport, type PointCloudViewportProps } from "../components/PointCloudViewport";
import {
  PremiumPointCloudViewport,
  type PremiumPointCloudViewportProps,
} from "../components/PremiumPointCloudViewport";
import type { PreviewViewerMode } from "./PreviewViewerModePanel";

type DualPanePointViewportProps = PointCloudViewportProps & {
  viewerMode: PreviewViewerMode;
  premiumPointSizeScale?: number;
  edlStrength?: number;
  edlRadius?: number;
};

/**
 * Renders standard or premium point viewport with identical preview props.
 */
export function DualPanePointViewport(props: DualPanePointViewportProps) {
  const { viewerMode, premiumPointSizeScale, edlStrength, edlRadius, ...viewportProps } = props;
  if (viewerMode === "premium") {
    const premiumProps: PremiumPointCloudViewportProps = {
      ...viewportProps,
      premiumPointSizeScale,
      edlStrength,
      edlRadius,
    };
    return <PremiumPointCloudViewport {...premiumProps} />;
  }
  return <PointCloudViewport {...viewportProps} />;
}
