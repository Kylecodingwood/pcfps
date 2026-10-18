import { clearStoredToken, getStoredToken } from "../auth/tokenStorage";
import type {
  ComparisonBundleResponse,
  CreateDerivedTaskRequestBody,
  CreateSemanticPruneTaskRequestBody,
  CreateTaskRequestBody,
  DerivedComparisonBundleResponse,
  LasPathDualPreviewResponse,
  LoginResponse,
  PageResponse,
  PointPreviewResponse,
  PreviewPointsRequestBody,
  TaskResponseDto,
} from "./types";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8080";

/** Must match Jakarta `@Max` on preview request DTOs in the backend. */
const PREVIEW_MAX_POINTS_API_CAP = 10_000_000;

/**
 * Resolves optional `maxPoints` for preview APIs: explicit caller value wins, else {@code VITE_PREVIEW_MAX_POINTS}.
 * Clamps to {@code [1, PREVIEW_MAX_POINTS_API_CAP]} when a value is present.
 *
 * @param explicitMaxPoints when set, used instead of the Vite env
 */
export function resolvePreviewMaxPointsForRequest(explicitMaxPoints?: number): number | undefined {
  const rawFromEnv = import.meta.env.VITE_PREVIEW_MAX_POINTS;
  let chosen: number | undefined;
  if (explicitMaxPoints !== undefined) {
    chosen = explicitMaxPoints;
  } else if (rawFromEnv !== undefined && rawFromEnv !== null && String(rawFromEnv).trim() !== "") {
    const parsedFromEnv = Number.parseInt(String(rawFromEnv).trim(), 10);
    if (!Number.isFinite(parsedFromEnv) || parsedFromEnv < 1) {
      chosen = undefined;
    } else {
      chosen = parsedFromEnv;
    }
  } else {
    chosen = undefined;
  }
  if (chosen === undefined) {
    return undefined;
  }
  const clampedLow = Math.max(1, chosen);
  return Math.min(clampedLow, PREVIEW_MAX_POINTS_API_CAP);
}

function buildUrl(path: string): string {
  const normalizedBase = apiBaseUrl.replace(/\/$/, "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}

async function parseJsonOrThrow(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = JSON.parse(text) as { message?: string };
      if (body.message) {
        message = body.message;
      }
    } catch {
      /* ignore */
    }
    if (response.status === 401) {
      clearStoredToken();
    }
    throw new Error(message);
  }
  if (!text) {
    return null;
  }
  return JSON.parse(text);
}

export async function loginRequest(username: string, password: string): Promise<LoginResponse> {
  const response = await fetch(buildUrl("/api/v1/auth/login"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return (await parseJsonOrThrow(response)) as LoginResponse;
}

/**
 * Serializes create-task JSON omitting undefined optional fields so the backend applies defaults.
 */
function serializeCreateTaskBody(body: CreateTaskRequestBody): string {
  const payload: Record<string, string | number> = { inputLasPath: body.inputLasPath };
  if (body.filterMethod !== undefined) {
    payload.filterMethod = body.filterMethod;
  }
  if (body.sorNeighborCount !== undefined) {
    payload.sorNeighborCount = body.sorNeighborCount;
  }
  if (body.sorStdRatio !== undefined) {
    payload.sorStdRatio = body.sorStdRatio;
  }
  if (body.rorRadius !== undefined) {
    payload.rorRadius = body.rorRadius;
  }
  if (body.rorMinNeighbors !== undefined) {
    payload.rorMinNeighbors = body.rorMinNeighbors;
  }
  return JSON.stringify(payload);
}

export async function createTaskRequest(body: CreateTaskRequestBody): Promise<TaskResponseDto> {
  const token = getStoredToken();
  const response = await fetch(buildUrl("/api/v1/tasks"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: serializeCreateTaskBody(body),
  });
  return (await parseJsonOrThrow(response)) as TaskResponseDto;
}

export async function getTaskRequest(taskId: string): Promise<TaskResponseDto> {
  const token = getStoredToken();
  const response = await fetch(buildUrl(`/api/v1/tasks/${taskId}`), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  return (await parseJsonOrThrow(response)) as TaskResponseDto;
}

export async function listTasksRequest(page: number, size: number): Promise<PageResponse<TaskResponseDto>> {
  const token = getStoredToken();
  const response = await fetch(
    buildUrl(`/api/v1/tasks?page=${page}&size=${size}&sort=createdAt,desc`),
    {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    }
  );
  return (await parseJsonOrThrow(response)) as PageResponse<TaskResponseDto>;
}

export async function comparisonBundleRequest(taskId: string): Promise<ComparisonBundleResponse> {
  const token = getStoredToken();
  const response = await fetch(buildUrl(`/api/v1/tasks/${taskId}/comparison-bundle`), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  return (await parseJsonOrThrow(response)) as ComparisonBundleResponse;
}

function serializeCreateDerivedTaskBody(body: CreateDerivedTaskRequestBody): string {
  const payload: Record<string, unknown> = {
    taskKind: body.taskKind,
    algorithm: body.algorithm,
  };
  const optionalFieldList: (keyof CreateDerivedTaskRequestBody)[] = [
    "clusterTolerance",
    "minClusterPoints",
    "maxClusterPoints",
    "useXyOnly",
    "normalNeighborCount",
    "angleThresholdDeg",
    "distanceThreshold",
    "minRegionPoints",
    "maxSeeds",
    "cellSizeM",
    "maxWindowSize",
    "slopeThreshold",
    "clothResolution",
    "rigidness",
    "csfIterations",
    "classifyThreshold",
  ];
  for (const fieldKey of optionalFieldList) {
    const fieldValue = body[fieldKey];
    if (fieldValue !== undefined && fieldValue !== null) {
      payload[fieldKey] = fieldValue;
    }
  }
  return JSON.stringify(payload);
}

export async function createDerivedJobRequest(
  parentTaskId: string,
  body: CreateDerivedTaskRequestBody
): Promise<TaskResponseDto> {
  const token = getStoredToken();
  const response = await fetch(buildUrl(`/api/v1/tasks/${parentTaskId}/derived-jobs`), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: serializeCreateDerivedTaskBody(body),
  });
  return (await parseJsonOrThrow(response)) as TaskResponseDto;
}

export async function derivedComparisonBundleRequest(
  childTaskId: string
): Promise<DerivedComparisonBundleResponse> {
  const token = getStoredToken();
  const response = await fetch(buildUrl(`/api/v1/tasks/${childTaskId}/derived-comparison-bundle`), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  return (await parseJsonOrThrow(response)) as DerivedComparisonBundleResponse;
}

export async function semanticPruneComparisonBundleRequest(
  pruneTaskId: string
): Promise<DerivedComparisonBundleResponse> {
  const token = getStoredToken();
  const response = await fetch(buildUrl(`/api/v1/tasks/${pruneTaskId}/semantic-prune-comparison-bundle`), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  return (await parseJsonOrThrow(response)) as DerivedComparisonBundleResponse;
}

function serializeCreateSemanticPruneBody(body: CreateSemanticPruneTaskRequestBody): string {
  const payload: Record<string, number> = {};
  if (body.groundVoxelSizeM !== undefined && body.groundVoxelSizeM !== null) {
    payload.groundVoxelSizeM = body.groundVoxelSizeM;
  }
  return JSON.stringify(payload);
}

export async function createSemanticPruneJobRequest(
  classifyTaskId: string,
  body: CreateSemanticPruneTaskRequestBody
): Promise<TaskResponseDto> {
  const token = getStoredToken();
  const response = await fetch(buildUrl(`/api/v1/tasks/${classifyTaskId}/semantic-prune-jobs`), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: serializeCreateSemanticPruneBody(body),
  });
  return (await parseJsonOrThrow(response)) as TaskResponseDto;
}

export async function previewLasPathRequest(
  lasPath: string,
  maxPoints?: number
): Promise<PointPreviewResponse> {
  const token = getStoredToken();
  const effectiveMaxPoints = resolvePreviewMaxPointsForRequest(maxPoints);
  const response = await fetch(buildUrl("/api/v1/preview/las-path"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ lasPath, maxPoints: effectiveMaxPoints }),
  });
  return (await parseJsonOrThrow(response)) as PointPreviewResponse;
}

export async function previewDualLasPathRequest(
  sourceLasPath: string,
  filteredLasPath: string,
  maxPoints?: number
): Promise<LasPathDualPreviewResponse> {
  const token = getStoredToken();
  const effectiveMaxPoints = resolvePreviewMaxPointsForRequest(maxPoints);
  const response = await fetch(buildUrl("/api/v1/preview/las-path/dual"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ sourceLasPath, filteredLasPath, maxPoints: effectiveMaxPoints }),
  });
  return (await parseJsonOrThrow(response)) as LasPathDualPreviewResponse;
}

export async function previewPointsRequest(
  fileId: string,
  body?: PreviewPointsRequestBody
): Promise<PointPreviewResponse> {
  const token = getStoredToken();
  const explicitFromBody = body?.maxPoints;
  const effectiveMaxPoints = resolvePreviewMaxPointsForRequest(explicitFromBody);
  const requestBody: PreviewPointsRequestBody =
    effectiveMaxPoints !== undefined ? { ...body, maxPoints: effectiveMaxPoints } : { ...(body ?? {}) };
  const response = await fetch(buildUrl(`/api/v1/files/${fileId}/preview-points`), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(requestBody),
  });
  return (await parseJsonOrThrow(response)) as PointPreviewResponse;
}

export async function fetchAuthorizedBlobUrl(downloadPath: string): Promise<string> {
  const token = getStoredToken();
  const response = await fetch(buildUrl(downloadPath), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    throw new Error(`Download failed: ${response.statusText}`);
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}
