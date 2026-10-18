import type { Point3dDto } from "../../api/types";

export interface PointBufferBuildResult {
  positionArray: Float32Array;
  colorArray: Float32Array | null;
  usePerVertexColor: boolean;
}

export function pointListHasFiniteVertexRgb(pointListForRgb: Point3dDto[]): boolean {
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

/**
 * Builds GPU buffers from preview JSON points.
 */
export function buildPointBuffersFromPointList(pointList: Point3dDto[]): PointBufferBuildResult {
  const usePerVertexColor = pointList.length > 0 && pointListHasFiniteVertexRgb(pointList);
  const positionArray = new Float32Array(pointList.length * 3);
  const colorArray = usePerVertexColor ? new Float32Array(pointList.length * 3) : null;

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

  return { positionArray, colorArray, usePerVertexColor };
}

/**
 * Splat base size aligned with standard preview (20000/N), slightly larger for soft-edge overlap.
 */
export function computePremiumBasePointSize(pointCount: number, pointSizeScale: number): number {
  const safePointCount = Math.max(1, pointCount);
  const standardPreviewSize = 20000 / safePointCount;
  const splatBoostFactor = 1.35;
  const sizeFloor = 0.75;
  const sizeCeiling = 3.5;
  const boostedSize = standardPreviewSize * splatBoostFactor * pointSizeScale;
  return Math.min(sizeCeiling, Math.max(sizeFloor, boostedSize));
}
