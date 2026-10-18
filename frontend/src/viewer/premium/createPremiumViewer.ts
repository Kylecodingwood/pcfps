import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import type { Point3dDto } from "../../api/types";
import {
  buildPointBuffersFromPointList,
  computePremiumBasePointSize,
} from "./buildPointBuffers";
import { EdlPass } from "./EdlPass";
import {
  createRenderTargetWithDepth,
  resizeRenderTargetWithDepth,
} from "./createRenderTargetWithDepth";
import { createSplatPointsMaterial, updateSplatPointsMaterialUniforms } from "./splatPointsMaterial";
import type { PremiumViewportOptions } from "./types";
import { DEFAULT_PREMIUM_VIEWPORT_OPTIONS, PREMIUM_MAX_PIXEL_RATIO } from "./types";

export interface PremiumViewerRuntime {
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  renderer: THREE.WebGLRenderer;
  controls: OrbitControls;
  sceneRenderTarget: THREE.WebGLRenderTarget;
  edlPass: EdlPass;
  pointsObject: THREE.Points;
  pointsGeometry: THREE.BufferGeometry;
  pointsMaterial: THREE.ShaderMaterial;
  animationFrameId: number;
}

export interface MountPremiumViewerOptions {
  containerElement: HTMLElement;
  pointList: Point3dDto[];
  pointColorHex: number;
  premiumOptions?: Partial<PremiumViewportOptions>;
}

/**
 * Mounts splat points + EDL into a DOM container (manual RT; avoids EffectComposer buffer bugs).
 */
export function mountPremiumViewer(options: MountPremiumViewerOptions): PremiumViewerRuntime {
  const mergedOptions: PremiumViewportOptions = {
    ...DEFAULT_PREMIUM_VIEWPORT_OPTIONS,
    ...options.premiumOptions,
  };

  const widthPixels = Math.max(1, Math.floor(options.containerElement.clientWidth));
  const heightPixels = Math.max(240, Math.floor(options.containerElement.clientHeight));
  const pixelRatio = Math.min(window.devicePixelRatio, PREMIUM_MAX_PIXEL_RATIO);
  const renderWidthPixels = Math.max(1, Math.floor(widthPixels * pixelRatio));
  const renderHeightPixels = Math.max(1, Math.floor(heightPixels * pixelRatio));

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x111111);

  const camera = new THREE.PerspectiveCamera(50, widthPixels / heightPixels, 0.1, 1e9);

  const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: false,
    logarithmicDepthBuffer: false,
    powerPreference: "high-performance",
  });
  renderer.setPixelRatio(pixelRatio);
  renderer.setSize(widthPixels, heightPixels);
  options.containerElement.appendChild(renderer.domElement);

  const sceneRenderTarget = createRenderTargetWithDepth(renderWidthPixels, renderHeightPixels);

  const edlPass = new EdlPass();
  edlPass.strength = mergedOptions.edlStrength;
  edlPass.kernelRadius = mergedOptions.edlRadius;
  edlPass.setSize(renderWidthPixels, renderHeightPixels);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;

  const bufferBuildResult = buildPointBuffersFromPointList(options.pointList);
  const pointsGeometry = new THREE.BufferGeometry();
  pointsGeometry.setAttribute("position", new THREE.BufferAttribute(bufferBuildResult.positionArray, 3));
  if (bufferBuildResult.colorArray !== null) {
    pointsGeometry.setAttribute("color", new THREE.BufferAttribute(bufferBuildResult.colorArray, 3));
  } else {
    const neutralColorArray = new Float32Array(options.pointList.length * 3);
    for (let channelIndex = 0; channelIndex < neutralColorArray.length; channelIndex++) {
      neutralColorArray[channelIndex] = 1;
    }
    pointsGeometry.setAttribute("color", new THREE.BufferAttribute(neutralColorArray, 3));
  }
  pointsGeometry.computeBoundingSphere();
  const boundingSphere = pointsGeometry.boundingSphere;
  if (boundingSphere) {
    const centerVector = boundingSphere.center;
    const radius = Math.max(boundingSphere.radius, 1e-3);
    camera.position.set(centerVector.x + radius * 2, centerVector.y + radius, centerVector.z + radius * 2);
    controls.target.copy(centerVector);
    camera.near = Math.max(radius / 2000, 0.01);
    camera.far = radius * 2000;
    camera.updateProjectionMatrix();
  }

  const basePointSize = computePremiumBasePointSize(
    options.pointList.length,
    mergedOptions.pointSizeScale
  );
  const pointsMaterial = createSplatPointsMaterial({
    basePointSize,
    pointSizeScale: 1,
    solidColorHex: options.pointColorHex,
    useVertexColors: bufferBuildResult.usePerVertexColor,
  });
  const pointsObject = new THREE.Points(pointsGeometry, pointsMaterial);
  scene.add(pointsObject);

  const clearColor = new THREE.Color(0x111111);

  let animationFrameId = 0;
  function animateFrame(): void {
    animationFrameId = requestAnimationFrame(animateFrame);
    if (document.visibilityState === "hidden") {
      return;
    }
    controls.update();

    const previousRenderTarget = renderer.getRenderTarget();
    renderer.setRenderTarget(sceneRenderTarget);
    renderer.setClearColor(clearColor, 1);
    renderer.clear();
    renderer.render(scene, camera);

    edlPass.renderToScreen = true;
    edlPass.render(renderer, sceneRenderTarget, sceneRenderTarget);

    renderer.setRenderTarget(previousRenderTarget);
  }
  animateFrame();

  return {
    scene,
    camera,
    renderer,
    controls,
    sceneRenderTarget,
    edlPass,
    pointsObject,
    pointsGeometry,
    pointsMaterial,
    animationFrameId,
  };
}

export function resizePremiumViewer(runtime: PremiumViewerRuntime, widthPixels: number, heightPixels: number): void {
  const safeWidth = Math.max(1, Math.floor(widthPixels));
  const safeHeight = Math.max(240, Math.floor(heightPixels));
  const pixelRatio = runtime.renderer.getPixelRatio();
  const renderWidthPixels = Math.max(1, Math.floor(safeWidth * pixelRatio));
  const renderHeightPixels = Math.max(1, Math.floor(safeHeight * pixelRatio));

  runtime.camera.aspect = safeWidth / safeHeight;
  runtime.camera.updateProjectionMatrix();
  runtime.renderer.setSize(safeWidth, safeHeight);
  resizeRenderTargetWithDepth(runtime.sceneRenderTarget, renderWidthPixels, renderHeightPixels);
  runtime.edlPass.setSize(renderWidthPixels, renderHeightPixels);
}

export function updatePremiumViewerPoints(
  runtime: PremiumViewerRuntime,
  pointList: Point3dDto[],
  pointColorHex: number,
  premiumOptions: PremiumViewportOptions
): void {
  runtime.scene.remove(runtime.pointsObject);
  runtime.pointsGeometry.dispose();
  runtime.pointsMaterial.dispose();

  const bufferBuildResult = buildPointBuffersFromPointList(pointList);
  const pointsGeometry = new THREE.BufferGeometry();
  pointsGeometry.setAttribute("position", new THREE.BufferAttribute(bufferBuildResult.positionArray, 3));
  if (bufferBuildResult.colorArray !== null) {
    pointsGeometry.setAttribute("color", new THREE.BufferAttribute(bufferBuildResult.colorArray, 3));
  } else {
    const neutralColorArray = new Float32Array(pointList.length * 3);
    for (let channelIndex = 0; channelIndex < neutralColorArray.length; channelIndex++) {
      neutralColorArray[channelIndex] = 1;
    }
    pointsGeometry.setAttribute("color", new THREE.BufferAttribute(neutralColorArray, 3));
  }
  pointsGeometry.computeBoundingSphere();
  const boundingSphere = pointsGeometry.boundingSphere;
  if (boundingSphere) {
    const centerVector = boundingSphere.center;
    const radius = Math.max(boundingSphere.radius, 1e-3);
    runtime.camera.position.set(centerVector.x + radius * 2, centerVector.y + radius, centerVector.z + radius * 2);
    runtime.controls.target.copy(centerVector);
    runtime.camera.near = Math.max(radius / 2000, 0.01);
    runtime.camera.far = radius * 2000;
    runtime.camera.updateProjectionMatrix();
  }

  const basePointSize = computePremiumBasePointSize(pointList.length, premiumOptions.pointSizeScale);
  const pointsMaterial = createSplatPointsMaterial({
    basePointSize,
    pointSizeScale: 1,
    solidColorHex: pointColorHex,
    useVertexColors: bufferBuildResult.usePerVertexColor,
  });
  const pointsObject = new THREE.Points(pointsGeometry, pointsMaterial);
  runtime.scene.add(pointsObject);

  runtime.pointsObject = pointsObject;
  runtime.pointsGeometry = pointsGeometry;
  runtime.pointsMaterial = pointsMaterial;
}

export function applyPremiumViewerOptions(runtime: PremiumViewerRuntime, premiumOptions: PremiumViewportOptions): void {
  runtime.edlPass.strength = premiumOptions.edlStrength;
  runtime.edlPass.kernelRadius = premiumOptions.edlRadius;
  const pointCount = runtime.pointsGeometry.attributes.position.count;
  const basePointSize = computePremiumBasePointSize(pointCount, premiumOptions.pointSizeScale);
  updateSplatPointsMaterialUniforms(runtime.pointsMaterial, basePointSize, 1);
}
