import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import type { Point3dDto } from "../api/types";

export interface PointCloudViewportProps {
  label: string;
  pointList: Point3dDto[] | null;
  truncated: boolean | undefined;
  sourcePointCountEstimate: number | undefined;
  loading: boolean;
  errorMessage: string | null;
  /** Hex RGB for PointsMaterial (default cyan). */
  pointColorHex?: number;
  /** CSS min-height for the WebGL canvas container (default larger for dual-pane). */
  canvasMinHeightCss?: string;
}

/**
 * Screen-space-ish point sprite size: fewer points would look invisible without a floor;
 * many points get a low ceiling so the cloud looks finer than large squares.
 */
function computePreviewPointSizeForCount(pointCount: number): number {
  const safePointCount = Math.max(1, pointCount);
  const rawSize = 20000 / safePointCount;
  const sizeCeiling = 2.25;
  const sizeFloor = 0.65;
  return Math.min(sizeCeiling, Math.max(sizeFloor, rawSize));
}

/**
 * Soft circular alpha so GL points are not harsh squares on some GPUs.
 */
function createCircularPointSpriteTexture(): THREE.CanvasTexture | null {
  const canvasPixelSize = 64;
  const canvasElement = document.createElement("canvas");
  canvasElement.width = canvasPixelSize;
  canvasElement.height = canvasPixelSize;
  const canvasContext = canvasElement.getContext("2d");
  if (!canvasContext) {
    return null;
  }
  const center = canvasPixelSize / 2;
  const radialGradient = canvasContext.createRadialGradient(center, center, 0, center, center, center);
  radialGradient.addColorStop(0, "rgba(255,255,255,1)");
  radialGradient.addColorStop(0.45, "rgba(255,255,255,0.85)");
  radialGradient.addColorStop(1, "rgba(255,255,255,0)");
  canvasContext.fillStyle = radialGradient;
  canvasContext.fillRect(0, 0, canvasPixelSize, canvasPixelSize);
  const canvasTexture = new THREE.CanvasTexture(canvasElement);
  canvasTexture.needsUpdate = true;
  return canvasTexture;
}

/**
 * Renders a sparse preview point set using Three.js (not full LAS precision).
 */
function pointListHasFiniteVertexRgb(pointListForRgb: Point3dDto[]): boolean {
  return pointListForRgb.every((point) => {
    const redChannel = point.r;
    const greenChannel = point.g;
    const blueChannel = point.b;
    return (
      typeof redChannel === "number" &&
      typeof greenChannel === "number" &&
      typeof blueChannel === "number" &&
      Number.isFinite(redChannel) &&
      Number.isFinite(greenChannel) &&
      Number.isFinite(blueChannel)
    );
  });
}

export function PointCloudViewport(props: PointCloudViewportProps) {
  const {
    label,
    pointList,
    truncated,
    sourcePointCountEstimate,
    loading,
    errorMessage,
    pointColorHex,
    canvasMinHeightCss,
  } = props;
  const resolvedPointColor = pointColorHex ?? 0x66ccff;
  const usePerVertexLasRgb =
    !!pointList && pointList.length > 0 && pointListHasFiniteVertexRgb(pointList);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);

  useEffect(() => {
    const containerElement = containerRef.current;
    if (!containerElement || !pointList || pointList.length === 0) {
      return;
    }

    const widthPixels = Math.max(1, Math.floor(containerElement.clientWidth));
    const heightPixels = Math.max(240, Math.floor(containerElement.clientHeight));
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x111111);

    const camera = new THREE.PerspectiveCamera(50, widthPixels / heightPixels, 0.1, 1e9);
    cameraRef.current = camera;
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    rendererRef.current = renderer;
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(widthPixels, heightPixels);
    containerElement.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;

    const positionArray = new Float32Array(pointList.length * 3);
    const colorArray = usePerVertexLasRgb ? new Float32Array(pointList.length * 3) : null;
    for (let pointIndex = 0; pointIndex < pointList.length; pointIndex++) {
      const point = pointList[pointIndex];
      positionArray[pointIndex * 3] = point.x;
      positionArray[pointIndex * 3 + 1] = point.y;
      positionArray[pointIndex * 3 + 2] = point.z;
      if (colorArray !== null) {
        colorArray[pointIndex * 3] = point.r!;
        colorArray[pointIndex * 3 + 1] = point.g!;
        colorArray[pointIndex * 3 + 2] = point.b!;
      }
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positionArray, 3));
    if (colorArray !== null) {
      geometry.setAttribute("color", new THREE.BufferAttribute(colorArray, 3));
    }
    geometry.computeBoundingSphere();
    const boundingSphere = geometry.boundingSphere;
    if (boundingSphere) {
      const centerVector = boundingSphere.center;
      const radius = Math.max(boundingSphere.radius, 1e-3);
      camera.position.set(centerVector.x + radius * 2, centerVector.y + radius, centerVector.z + radius * 2);
      controls.target.copy(centerVector);
      camera.near = Math.max(radius / 2000, 0.01);
      camera.far = radius * 2000;
      camera.updateProjectionMatrix();
    }

    const spriteMapTexture = createCircularPointSpriteTexture();
    const pointMaterial = new THREE.PointsMaterial({
      size: computePreviewPointSizeForCount(pointList.length),
      color: usePerVertexLasRgb ? 0xffffff : resolvedPointColor,
      vertexColors: usePerVertexLasRgb,
      sizeAttenuation: true,
      map: spriteMapTexture ?? undefined,
      transparent: spriteMapTexture !== null,
      depthWrite: spriteMapTexture === null,
    });
    const pointsObject = new THREE.Points(geometry, pointMaterial);
    scene.add(pointsObject);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    function applyViewportSizeFromDom(): void {
      const cameraActive = cameraRef.current;
      const rendererActive = rendererRef.current;
      const containerActive = containerRef.current;
      if (!cameraActive || !rendererActive || !containerActive) {
        return;
      }
      const widthNext = Math.max(1, Math.floor(containerActive.clientWidth));
      const heightNext = Math.max(240, Math.floor(containerActive.clientHeight));
      cameraActive.aspect = widthNext / heightNext;
      cameraActive.updateProjectionMatrix();
      rendererActive.setSize(widthNext, heightNext);
    }

    let animationFrameId = 0;
    function animateFrame() {
      animationFrameId = requestAnimationFrame(animateFrame);
      controls.update();
      renderer.render(scene, camera);
    }
    animateFrame();

    const resizeObserver = new ResizeObserver(() => applyViewportSizeFromDom());
    resizeObserver.observe(containerElement);
    window.addEventListener("resize", applyViewportSizeFromDom);
    applyViewportSizeFromDom();

    return () => {
      window.removeEventListener("resize", applyViewportSizeFromDom);
      resizeObserver.disconnect();
      cancelAnimationFrame(animationFrameId);
      controls.dispose();
      geometry.dispose();
      pointMaterial.map?.dispose();
      pointMaterial.dispose();
      renderer.dispose();
      cameraRef.current = null;
      rendererRef.current = null;
      if (renderer.domElement.parentElement) {
        renderer.domElement.parentElement.removeChild(renderer.domElement);
      }
    };
  }, [pointList, resolvedPointColor, usePerVertexLasRgb]);

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
          预览为服务端抽稀{truncated ? "（已截断）" : ""}
          {sourcePointCountEstimate !== undefined && sourcePointCountEstimate > 0
            ? ` · 估计总点数约 ${sourcePointCountEstimate}`
            : ""}
        </p>
      )}
      {!loading && !errorMessage && pointList && pointList.length > 0 && usePerVertexLasRgb && (
        <p style={{ fontSize: 12, color: "#888", margin: "0 0 4px", flexShrink: 0 }}>真彩色（LAS RGB）</p>
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
