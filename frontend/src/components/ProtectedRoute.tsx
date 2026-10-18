import { Navigate } from "react-router-dom";
import { getStoredToken } from "../auth/tokenStorage";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = getStoredToken();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}
