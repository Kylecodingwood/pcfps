import * as THREE from "three";

/**
 * Offscreen target for splat render + EDL (depth texture readable on Metal/WebGL2).
 */
export function createRenderTargetWithDepth(
  widthPixels: number,
  heightPixels: number
): THREE.WebGLRenderTarget {
  const safeWidth = Math.max(1, Math.floor(widthPixels));
  const safeHeight = Math.max(1, Math.floor(heightPixels));
  const renderTarget = new THREE.WebGLRenderTarget(safeWidth, safeHeight, {
    type: THREE.UnsignedByteType,
    format: THREE.RGBAFormat,
    depthBuffer: true,
    stencilBuffer: false,
    resolveDepthBuffer: false,
  });
  renderTarget.texture.name = "PremiumViewer.color";
  renderTarget.depthTexture = new THREE.DepthTexture(safeWidth, safeHeight);
  renderTarget.depthTexture.name = "PremiumViewer.depth";
  return renderTarget;
}

/**
 * Keeps depth attachment dimensions in sync after logical resize.
 */
export function resizeRenderTargetWithDepth(
  renderTarget: THREE.WebGLRenderTarget,
  widthPixels: number,
  heightPixels: number
): void {
  const safeWidth = Math.max(1, Math.floor(widthPixels));
  const safeHeight = Math.max(1, Math.floor(heightPixels));
  renderTarget.setSize(safeWidth, safeHeight);
  const depthTexture = renderTarget.depthTexture;
  if (depthTexture) {
    depthTexture.image.width = safeWidth;
    depthTexture.image.height = safeHeight;
    depthTexture.needsUpdate = true;
  }
}
