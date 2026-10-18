import type { PremiumViewerRuntime } from "./createPremiumViewer";

/**
 * Disposes GPU resources held by a premium viewer runtime.
 */
export function disposePremiumViewer(runtime: PremiumViewerRuntime | null): void {
  if (!runtime) {
    return;
  }
  cancelAnimationFrame(runtime.animationFrameId);
  runtime.controls.dispose();
  runtime.pointsGeometry.dispose();
  runtime.pointsMaterial.dispose();
  runtime.edlPass.dispose();
  runtime.sceneRenderTarget.dispose();
  runtime.renderer.dispose();
  if (runtime.renderer.domElement.parentElement) {
    runtime.renderer.domElement.parentElement.removeChild(runtime.renderer.domElement);
  }
}
