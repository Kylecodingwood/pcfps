import { Navigate, useParams } from "react-router-dom";

/** Legacy URL `/tasks/:taskId/compare` → query-based dual preview. */
export function RedirectCompareRoute() {
  const { taskId } = useParams<{ taskId: string }>();
  if (!taskId) {
    return <Navigate to="/preview/dual" replace />;
  }
  return <Navigate to={`/preview/dual?taskId=${encodeURIComponent(taskId)}`} replace />;
}
