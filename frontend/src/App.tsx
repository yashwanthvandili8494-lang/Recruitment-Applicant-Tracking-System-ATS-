/**
 * App root — React Router configuration with all routes.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './hooks/useAuth';
import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './layouts/AppLayout';

// Pages
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import CareersPage from './pages/CareersPage';
import JobsPage from './pages/JobsPage';
import JobDetailPage from './pages/JobDetailPage';
import ApplicationsPage from './pages/ApplicationsPage';
import ApplicationDetailPage from './pages/ApplicationDetailPage';
import CandidatesPage from './pages/CandidatesPage';
import CandidateDetailPage from './pages/CandidateDetailPage';
import InterviewsPage from './pages/InterviewsPage';
import OffersPage from './pages/OffersPage';
import UsersPage from './pages/UsersPage';
import { NotFoundPage, AccessDeniedPage, SettingsPage } from './pages/UtilityPages';

function AppRoutes() {
  const { isAuthenticated, user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-surface-50">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-surface-500 text-sm">Loading RecruitFlow...</p>
        </div>
      </div>
    );
  }

  // Determine default landing page based on role
  const defaultRoute = !isAuthenticated
    ? '/careers'
    : user?.role === 'candidate'
      ? '/my-dashboard'
      : user?.role === 'interviewer'
        ? '/interviews'
        : '/dashboard';

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={isAuthenticated ? <Navigate to={defaultRoute} /> : <LoginPage />} />
      <Route path="/register" element={isAuthenticated ? <Navigate to={defaultRoute} /> : <RegisterPage />} />
      <Route path="/careers" element={<CareersPage />} />
      <Route path="/careers/:jobId" element={<JobDetailPage />} />
      <Route path="/access-denied" element={<AccessDeniedPage />} />

      {/* Authenticated routes — wrapped in AppLayout */}
      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        {/* Staff Dashboard */}
        <Route path="/dashboard" element={
          <ProtectedRoute allowedRoles={['admin', 'recruiter', 'hiring_manager']}>
            <DashboardPage />
          </ProtectedRoute>
        } />

        {/* Candidate Dashboard */}
        <Route path="/my-dashboard" element={
          <ProtectedRoute allowedRoles={['candidate']}>
            <ApplicationsPage />
          </ProtectedRoute>
        } />

        {/* Jobs */}
        <Route path="/jobs" element={
          <ProtectedRoute allowedRoles={['admin', 'recruiter', 'hiring_manager']}>
            <JobsPage />
          </ProtectedRoute>
        } />
        <Route path="/jobs/:jobId" element={
          <ProtectedRoute allowedRoles={['admin', 'recruiter', 'hiring_manager']}>
            <JobDetailPage />
          </ProtectedRoute>
        } />

        {/* Applications */}
        <Route path="/applications" element={<ApplicationsPage />} />
        <Route path="/applications/:applicationId" element={<ApplicationDetailPage />} />
        <Route path="/my-applications" element={
          <ProtectedRoute allowedRoles={['candidate']}>
            <ApplicationsPage />
          </ProtectedRoute>
        } />

        {/* Candidates */}
        <Route path="/candidates" element={
          <ProtectedRoute allowedRoles={['admin', 'recruiter', 'hiring_manager']}>
            <CandidatesPage />
          </ProtectedRoute>
        } />
        <Route path="/candidates/:candidateId" element={<CandidateDetailPage />} />

        {/* Interviews */}
        <Route path="/interviews" element={<InterviewsPage />} />
        <Route path="/my-interviews" element={
          <ProtectedRoute allowedRoles={['candidate']}>
            <InterviewsPage />
          </ProtectedRoute>
        } />

        {/* Offers */}
        <Route path="/offers" element={<OffersPage />} />

        {/* Admin */}
        <Route path="/users" element={
          <ProtectedRoute allowedRoles={['admin']}>
            <UsersPage />
          </ProtectedRoute>
        } />

        {/* Settings */}
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/profile" element={<SettingsPage />} />
      </Route>

      {/* Redirects */}
      <Route path="/" element={<Navigate to={defaultRoute} replace />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              borderRadius: '12px',
              background: '#1e293b',
              color: '#f8fafc',
              fontSize: '14px',
            },
          }}
        />
      </AuthProvider>
    </BrowserRouter>
  );
}
