/**
 * Utility pages — 404, Access Denied, Settings placeholder.
 */

import { Link, useNavigate } from 'react-router-dom';
import { ShieldX, FileQuestion, Settings as SettingsIcon } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import toast from 'react-hot-toast';

export function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-50">
      <div className="text-center animate-fade-in">
        <FileQuestion className="w-16 h-16 text-surface-300 mx-auto mb-4" />
        <h1 className="text-4xl font-bold text-surface-900 mb-2">404</h1>
        <p className="text-surface-500 mb-6">The page you're looking for doesn't exist</p>
        <Link to="/" className="btn-primary">Go Home</Link>
      </div>
    </div>
  );
}

export function AccessDeniedPage() {
  const { user, login, logout } = useAuth();
  const navigate = useNavigate();

  const handleQuickSwitch = async (email: string, roleName: string) => {
    try {
      const loggedInUser = await login({ email, password: 'Demo1234!' });
      toast.success(`Switched to ${roleName}`);
      if (loggedInUser?.role === 'candidate') {
        navigate('/my-dashboard');
      } else if (loggedInUser?.role === 'interviewer') {
        navigate('/interviews');
      } else {
        navigate('/dashboard');
      }
    } catch {
      toast.error(`Failed to switch to ${roleName}`);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const isCandidate = user?.role === 'candidate';
  const isInterviewer = user?.role === 'interviewer';
  const defaultDashboard = isCandidate
    ? '/my-dashboard'
    : isInterviewer
      ? '/interviews'
      : '/dashboard';

  const dashboardLabel = isCandidate
    ? 'Go to My Applications'
    : isInterviewer
      ? 'Go to My Interviews'
      : 'Go to Staff Dashboard';

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-50 p-6">
      <div className="card max-w-lg w-full p-8 text-center animate-fade-in shadow-xl border-surface-200">
        <div className="w-16 h-16 bg-red-50 text-red-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <ShieldX className="w-8 h-8" />
        </div>
        <h1 className="text-2xl md:text-3xl font-bold text-surface-900 mb-2">Access Restricted</h1>
        
        {user ? (
          <div className="p-3 bg-surface-50 rounded-xl border border-surface-200 mb-4 text-xs text-surface-600">
            Signed in as <strong className="text-surface-900">{user.name}</strong>{' '}
            <span className="capitalize px-2 py-0.5 rounded-full bg-surface-200 font-semibold text-surface-700 ml-1">
              {user.role.replace('_', ' ')}
            </span>
          </div>
        ) : null}

        <p className="text-surface-600 text-sm mb-6 leading-relaxed">
          {isCandidate
            ? 'This section is reserved for recruiting and hiring staff. Candidates can view their own applications and browse open career opportunities.'
            : isInterviewer
              ? 'This section is reserved for recruiters and hiring managers. As an interviewer, you have access to your assigned interviews and scorecards.'
              : 'Your account does not have permission to access this specific resource.'}
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-8">
          <Link to={defaultDashboard} className="btn-primary w-full sm:w-auto justify-center">
            {dashboardLabel}
          </Link>
          <Link to="/careers" className="btn-secondary w-full sm:w-auto justify-center">
            Browse Careers
          </Link>
        </div>

        {/* Quick Demo Switcher */}
        <div className="pt-6 border-t border-surface-100 text-left">
          <p className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2.5">
            Switch Demo Account (1-Click Test)
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
            <button
              onClick={() => handleQuickSwitch('admin@recruitflow.dev', 'Admin (Sarah Admin)')}
              className="p-2 rounded-xl border border-surface-200 hover:border-primary-300 hover:bg-primary-50 text-left transition-colors"
            >
              <p className="font-semibold text-surface-900">Admin</p>
              <p className="text-[11px] text-surface-500">Sarah Admin</p>
            </button>
            <button
              onClick={() => handleQuickSwitch('recruiter@recruitflow.dev', 'Recruiter (Mark Recruiter)')}
              className="p-2 rounded-xl border border-surface-200 hover:border-primary-300 hover:bg-primary-50 text-left transition-colors"
            >
              <p className="font-semibold text-surface-900">Recruiter</p>
              <p className="text-[11px] text-surface-500">Mark Recruiter</p>
            </button>
            <button
              onClick={() => handleQuickSwitch('manager@recruitflow.dev', 'Hiring Manager (Lisa Manager)')}
              className="p-2 rounded-xl border border-surface-200 hover:border-primary-300 hover:bg-primary-50 text-left transition-colors"
            >
              <p className="font-semibold text-surface-900">Manager</p>
              <p className="text-[11px] text-surface-500">Lisa Manager</p>
            </button>
            <button
              onClick={() => handleQuickSwitch('interviewer@recruitflow.dev', 'Interviewer (David Interviewer)')}
              className="p-2 rounded-xl border border-surface-200 hover:border-primary-300 hover:bg-primary-50 text-left transition-colors"
            >
              <p className="font-semibold text-surface-900">Interviewer</p>
              <p className="text-[11px] text-surface-500">David Interviewer</p>
            </button>
            <button
              onClick={() => handleQuickSwitch('alex@example.com', 'Candidate (Alex Johnson)')}
              className="p-2 rounded-xl border border-surface-200 hover:border-primary-300 hover:bg-primary-50 text-left transition-colors sm:col-span-2"
            >
              <p className="font-semibold text-surface-900">Candidate</p>
              <p className="text-[11px] text-surface-500">Alex Johnson</p>
            </button>
          </div>
          <div className="mt-4 text-center">
            <button
              onClick={handleLogout}
              className="text-xs text-surface-400 hover:text-surface-600 underline"
            >
              Sign out of account
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function SettingsPage() {
  return (
    <div className="animate-fade-in">
      <h1 className="text-2xl font-bold text-surface-900 mb-2">Settings</h1>
      <p className="text-surface-500 mb-6">Manage your account preferences</p>
      <div className="card p-8 text-center">
        <SettingsIcon className="w-12 h-12 text-surface-300 mx-auto mb-4" />
        <p className="text-surface-500">Settings page coming soon</p>
      </div>
    </div>
  );
}
