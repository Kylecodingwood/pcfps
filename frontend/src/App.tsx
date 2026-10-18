import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { MainLayout } from "./layouts/MainLayout";
import { ClassifyHubPage } from "./pages/ClassifyHubPage";
import { DeriveWizardPage } from "./pages/DeriveWizardPage";
import { JobListPage } from "./pages/JobListPage";
import { JobWizardPage } from "./pages/JobWizardPage";
import { SegmentHubPage } from "./pages/SegmentHubPage";
import { SemanticPruneWizardPage } from "./pages/SemanticPruneWizardPage";
import { LoginPage } from "./pages/LoginPage";
import { PreviewDualPage } from "./pages/PreviewDualPage";
import { PreviewSinglePage } from "./pages/PreviewSinglePage";
import { RedirectCompareRoute } from "./pages/RedirectCompareRoute";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Navigate to="/jobs" replace />} />
          <Route path="/jobs" element={<JobListPage />} />
          <Route path="/jobs/new" element={<JobWizardPage />} />
          <Route path="/jobs/:parentTaskId/segment/new" element={<DeriveWizardPage mode="segment" />} />
          <Route path="/jobs/:parentTaskId/classify/new" element={<DeriveWizardPage mode="classify" />} />
          <Route path="/jobs/:classifyTaskId/semantic-prune/new" element={<SemanticPruneWizardPage />} />
          <Route path="/process/segment" element={<SegmentHubPage />} />
          <Route path="/process/classify" element={<ClassifyHubPage />} />
          <Route path="/preview/single" element={<PreviewSinglePage />} />
          <Route path="/preview/dual" element={<PreviewDualPage />} />
        </Route>
        <Route
          path="/tasks/:taskId/compare"
          element={
            <ProtectedRoute>
              <RedirectCompareRoute />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/jobs" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
