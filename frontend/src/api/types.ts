export interface LoginResponse {
  token: string;
  expiresInSeconds: number;
  username: string;
}

/** Matches backend {@code FilterMethod} JSON. */
export type FilterMethod = "SOR" | "ROR";

/** Request body for {@code POST /api/v1/tasks}. Omitted optional numbers use server defaults. */
export interface CreateTaskRequestBody {
  inputLasPath: string;
  filterMethod?: FilterMethod;
  sorNeighborCount?: number;
  sorStdRatio?: number;
  rorRadius?: number;
  rorMinNeighbors?: number;
}

export type TaskKind = "FILTER" | "SEGMENT" | "CLASSIFY" | "SEMANTIC_PRUNE";

export interface TaskResponseDto {
  id: string;
  status: string;
  inputLasPath: string;
  outputBasePath: string;
  errorMessage: string | null;
  createdAt: string;
  filterMethod: string | null;
  filterParamsJson: Record<string, unknown> | null;
  filterSummary: string;
  taskKind?: TaskKind;
  parentTaskId?: string | null;
  derivedMethod?: string | null;
  derivedParamsJson?: Record<string, unknown> | null;
  derivedSummary?: string | null;
  derivedMetricsJson?: Record<string, unknown> | null;
}

export interface AssetEntryDto {
  role: string;
  fileId: string;
  filename: string;
  mimeType: string;
  downloadPath: string;
}

/** Matches backend {@code FilterRunMetricsDto} from comparison-bundle. */
export interface FilterRunMetricsDto {
  nBefore: number | null;
  nAfter: number | null;
  removalRatioPercent: number | null;
  timingTotalSec: number | null;
  timingDecodeSec: number | null;
  timingFilterSec: number | null;
  timingWriteSec: number | null;
}

export interface ComparisonBundleResponse {
  taskId: string;
  status: string;
  traceId: string;
  assets: AssetEntryDto[];
  runMetrics: FilterRunMetricsDto | null;
}

/** Dual-pane bundle: parent filtered vs child segment/classify, or parent classified vs child pruned. */
export interface DerivedComparisonBundleResponse {
  childTaskId: string;
  status: string;
  traceId: string;
  leftFileId: string;
  leftLabel: string;
  rightFileId: string;
  rightLabel: string;
  childTaskKind: TaskKind;
  derivedMethod: string;
  derivedMetrics: Record<string, unknown>;
  semanticLegendMethod?: string | null;
}

/** Body for {@code POST /api/v1/tasks/{parentId}/derived-jobs}. */
export interface CreateDerivedTaskRequestBody {
  taskKind: TaskKind;
  algorithm: string;
  clusterTolerance?: number;
  minClusterPoints?: number;
  maxClusterPoints?: number;
  useXyOnly?: boolean;
  normalNeighborCount?: number;
  angleThresholdDeg?: number;
  distanceThreshold?: number;
  minRegionPoints?: number;
  maxSeeds?: number;
  cellSizeM?: number;
  maxWindowSize?: number;
  slopeThreshold?: number;
  clothResolution?: number;
  rigidness?: number;
  csfIterations?: number;
  classifyThreshold?: number;
}

/** Body for {@code POST /api/v1/tasks/{classifyTaskId}/semantic-prune-jobs}. */
export interface CreateSemanticPruneTaskRequestBody {
  groundVoxelSizeM?: number;
}

export interface PageResponse<T> {
  content: T[];
  totalElements: number;
  totalPages: number;
  number: number;
  size: number;
}

/** Optional r/g/b are linear 0–1 from LAS when the preview includes RGB. */
export interface Point3dDto {
  x: number;
  y: number;
  z: number;
  r?: number;
  g?: number;
  b?: number;
}

export interface PointPreviewResponse {
  points: Point3dDto[];
  maxPointsRequested: number;
  pointCountReturned: number;
  sourcePointCountEstimate: number;
  truncated: boolean;
}

/** Body for {@code POST /api/v1/files/{fileId}/preview-points}. */
export type PreviewPointsColorMode = "native" | "classification";

export interface PreviewPointsRequestBody {
  maxPoints?: number;
  colorMode?: PreviewPointsColorMode;
}

/** Matches backend {@code LasPathDualPreviewResponse} JSON. */
export interface LasPathDualPreviewResponse {
  sourcePreview: PointPreviewResponse;
  filteredPreview: PointPreviewResponse;
}
