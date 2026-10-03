/**
 * Application Detail Page.
 * Displays application review details, pipeline stage progress, resume, and status audit trail.
 */

import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import type { Application, StatusHistory } from '../types';
import StatusBadge from '../components/StatusBadge';
import { useAuth } from '../hooks/useAuth';
import {
  FileText, User, Briefcase, Calendar, Clock, ArrowLeft,
  Loader2, AlertCircle, CheckCircle, Download, ArrowUpDown,
  History, XCircle, ChevronRight, MessageSquare,
} from 'lucide-react';
import toast from 'react-hot-toast';

const PIPELINE_STAGES = [
  { id: 'applied', label: 'Applied' },
  { id: 'under_review', label: 'Review' },
  { id: 'shortlisted', label: 'Shortlisted' },
  { id: 'interview_scheduled', label: 'Interview' },
  { id: 'offered', label: 'Offer' },
  { id: 'hired', label: 'Hired' },
];

const ALL_STATUS_OPTIONS = [
  { value: 'applied', label: 'Applied' },
  { value: 'under_review', label: 'Under Review' },
  { value: 'shortlisted', label: 'Shortlisted' },
  { value: 'interview_scheduled', label: 'Interview Scheduled' },
  { value: 'interview_completed', label: 'Interview Completed' },
  { value: 'offered', label: 'Offer Extended' },
  { value: 'hired', label: 'Hired' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'on_hold', label: 'On Hold' },
];

export default function ApplicationDetailPage() {
  const { applicationId, id } = useParams<{ applicationId?: string; id?: string }>();
  const effectiveId = applicationId || id;
  const navigate = useNavigate();
  const { user } = useAuth();

  const [application, setApplication] = useState<Application | null>(null);
  const [history, setHistory] = useState<StatusHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Status update modal for staff
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [newStatus, setNewStatus] = useState('');
  const [statusReason, setStatusReason] = useState('');
  const [updatingStatus, setUpdatingStatus] = useState(false);

  // Withdraw state for candidate
  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [withdrawing, setWithdrawing] = useState(false);

  const fetchApplicationData = async () => {
    if (!effectiveId) return;
    setLoading(true);
    setError(null);
    try {
      const [appRes, historyRes] = await Promise.all([
        api.get<Application>(`/applications/${effectiveId}`),
        api.get<StatusHistory[]>(`/applications/${effectiveId}/history`),
      ]);
      setApplication(appRes.data);
      setHistory(historyRes.data || []);
      setNewStatus(appRes.data.status);
    } catch (err: any) {
      if (err.response?.status === 404) {
        setError('Application not found.');
      } else if (err.response?.status === 403) {
        setError('You do not have permission to view this application.');
      } else {
        setError('Failed to load application details.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplicationData();
  }, [effectiveId]);

  const isStaff = user?.role !== 'candidate';
  const isOwnerCandidate = user?.role === 'candidate' && application?.candidate_id === user.id;

  const handleStatusUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!effectiveId || !newStatus) return;

    setUpdatingStatus(true);
    try {
      await api.patch(`/applications/${effectiveId}/status`, {
        status: newStatus,
        reason: statusReason.trim() || undefined,
      });
      toast.success(`Application updated to ${newStatus.replace('_', ' ')}`);
      setShowStatusModal(false);
      setStatusReason('');
      fetchApplicationData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to update status');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleWithdraw = async () => {
    if (!effectiveId) return;
    setWithdrawing(true);
    try {
      await api.post(`/applications/${effectiveId}/withdraw`);
      toast.success('Application withdrawn successfully');
      setShowWithdrawModal(false);
      fetchApplicationData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to withdraw application');
    } finally {
      setWithdrawing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-primary-600 animate-spin mx-auto mb-3" />
          <p className="text-surface-500 text-sm">Loading application details...</p>
        </div>
      </div>
    );
  }

  if (error || !application) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Link
          to={isStaff ? '/applications' : '/my-applications'}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-surface-600 hover:text-primary-600"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Applications
        </Link>
        <div className="card p-12 text-center max-w-md mx-auto">
          <div className="w-14 h-14 bg-red-50 text-red-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-7 h-7" />
          </div>
          <h2 className="text-xl font-bold text-surface-900 mb-2">Application Not Found</h2>
          <p className="text-surface-500 text-sm mb-6">{error || 'This application does not exist.'}</p>
          <Link
            to={isStaff ? '/applications' : '/my-applications'}
            className="btn-primary w-full justify-center"
          >
            Return to Applications List
          </Link>
        </div>
      </div>
    );
  }

  // Calculate current stage index for pipeline
  const currentStageIndex = PIPELINE_STAGES.findIndex(
    (s) => s.id === application.status || (s.id === 'interview_scheduled' && application.status === 'interview_completed')
  );

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Header & Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          to={isStaff ? '/applications' : '/my-applications'}
          className="inline-flex items-center gap-2 text-sm font-medium text-surface-600 hover:text-primary-600 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to {isStaff ? 'All Applications' : 'My Applications'}
        </Link>

        {/* Action button in top bar */}
        <div className="flex items-center gap-3">
          {isStaff && (
            <button
              onClick={() => {
                setNewStatus(application.status);
                setShowStatusModal(true);
              }}
              className="btn-primary !py-2 !px-4 text-xs"
            >
              <ArrowUpDown className="w-3.5 h-3.5" /> Update Status
            </button>
          )}

          {isOwnerCandidate && application.status !== 'withdrawn' && application.status !== 'rejected' && application.status !== 'hired' && (
            <button
              onClick={() => setShowWithdrawModal(true)}
              className="btn-secondary !py-2 !px-3 text-xs text-red-600 hover:bg-red-50 border-red-200"
            >
              <XCircle className="w-3.5 h-3.5" /> Withdraw
            </button>
          )}
        </div>
      </div>

      {/* Main Card Header */}
      <div className="card p-6 md:p-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl md:text-3xl font-extrabold text-surface-900">
                {application.job_title || 'Application'}
              </h1>
              <StatusBadge status={application.status} size="lg" />
            </div>

            <div className="flex flex-wrap items-center gap-y-1 gap-x-5 text-sm text-surface-500">
              <span className="flex items-center gap-1.5 font-medium text-surface-800">
                <User className="w-4 h-4 text-primary-600" />
                {isStaff ? (
                  <Link
                    to={`/candidates/${application.candidate_id}`}
                    className="hover:text-primary-600 hover:underline"
                  >
                    {application.candidate_name || 'Candidate Profile'}
                  </Link>
                ) : (
                  <span>{application.candidate_name || user?.name}</span>
                )}
              </span>

              <span className="flex items-center gap-1.5">
                <Calendar className="w-4 h-4 text-surface-400" />
                Applied on {new Date(application.applied_at).toLocaleDateString()}
              </span>

              {application.updated_at && application.updated_at !== application.applied_at && (
                <span className="flex items-center gap-1.5 text-xs text-surface-400">
                  <Clock className="w-3.5 h-3.5" />
                  Last updated {new Date(application.updated_at).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link
              to={`/careers/${application.job_id}`}
              className="btn-secondary !text-xs !py-2 !px-3.5"
            >
              <Briefcase className="w-3.5 h-3.5" /> View Job Posting
            </Link>
          </div>
        </div>

        {/* Pipeline Stepper */}
        {application.status !== 'rejected' && application.status !== 'withdrawn' ? (
          <div className="mt-8 pt-8 border-t border-surface-100">
            <p className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-4">
              Recruitment Pipeline Progress
            </p>
            <div className="flex items-center justify-between relative">
              {/* Connector line */}
              <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-1 bg-surface-200 -z-0" />
              <div
                className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-primary-600 -z-0 transition-all duration-500"
                style={{
                  width: `${Math.max(0, Math.min(100, (currentStageIndex / (PIPELINE_STAGES.length - 1)) * 100))}%`,
                }}
              />

              {PIPELINE_STAGES.map((stage, idx) => {
                const isPassed = currentStageIndex >= idx;
                const isCurrent = currentStageIndex === idx;

                return (
                  <div key={stage.id} className="relative z-10 flex flex-col items-center">
                    <div
                      className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs transition-all duration-300 ${
                        isCurrent
                          ? 'gradient-primary text-white ring-4 ring-primary-100 shadow-md scale-110'
                          : isPassed
                          ? 'bg-primary-600 text-white'
                          : 'bg-white border-2 border-surface-300 text-surface-400'
                      }`}
                    >
                      {isPassed && !isCurrent ? (
                        <CheckCircle className="w-4 h-4" />
                      ) : (
                        <span>{idx + 1}</span>
                      )}
                    </div>
                    <span
                      className={`text-[11px] font-semibold mt-2 whitespace-nowrap ${
                        isCurrent
                          ? 'text-primary-700'
                          : isPassed
                          ? 'text-surface-800'
                          : 'text-surface-400'
                      }`}
                    >
                      {stage.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="mt-6 p-4 rounded-xl bg-surface-50 border border-surface-200 text-xs text-surface-600 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-surface-400 shrink-0" />
            <span>
              This application has been marked as{' '}
              <strong className="capitalize">{application.status.replace('_', ' ')}</strong>.
            </span>
          </div>
        )}
      </div>

      {/* Grid: Details & Status Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Application Details & Cover Letter */}
        <div className="lg:col-span-2 space-y-6">
          {/* Cover Letter */}
          <div className="card p-6 md:p-8 space-y-3">
            <h2 className="text-lg font-bold text-surface-900 flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-primary-600" />
              Cover Letter & Candidate Note
            </h2>
            {application.cover_letter ? (
              <div className="p-4 bg-surface-50 rounded-xl border border-surface-200/70 text-sm text-surface-700 leading-relaxed whitespace-pre-line">
                {application.cover_letter}
              </div>
            ) : (
              <p className="text-sm text-surface-400 italic">No cover letter was included with this application.</p>
            )}
          </div>

          {/* Attached Resume */}
          <div className="card p-6 space-y-3">
            <h2 className="text-lg font-bold text-surface-900 flex items-center gap-2">
              <FileText className="w-5 h-5 text-primary-600" />
              Resume Attachment
            </h2>

            {application.resume_id ? (
              <div className="flex items-center justify-between p-4 bg-primary-50/60 border border-primary-200 rounded-xl">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-primary-900">Candidate Resume</p>
                    <p className="text-xs text-primary-700">Official document on file</p>
                  </div>
                </div>

                <a
                  href={`/api/v1/resumes/${application.resume_id}/download`}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-primary !text-xs !py-2 !px-4"
                >
                  <Download className="w-3.5 h-3.5" /> Download File
                </a>
              </div>
            ) : (
              <div className="p-4 bg-surface-50 rounded-xl border border-surface-200/60 text-xs text-surface-500 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-surface-400" />
                <span>No resume file was attached to this application.</span>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Status Change History Timeline */}
        <div className="lg:col-span-1 space-y-6">
          <div className="card p-6">
            <h3 className="text-base font-bold text-surface-900 flex items-center gap-2 mb-4">
              <History className="w-4 h-4 text-primary-600" />
              Activity & History
            </h3>

            {history.length === 0 ? (
              <p className="text-xs text-surface-400 italic py-4">No history entries recorded yet.</p>
            ) : (
              <div className="space-y-4 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-surface-200">
                {history.map((entry, idx) => (
                  <div key={entry.id || idx} className="flex items-start gap-3 relative pl-6">
                    <div className="absolute left-1.5 top-1.5 w-3 h-3 rounded-full bg-primary-500 ring-4 ring-white" />
                    <div className="min-w-0 flex-1 space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <StatusBadge status={entry.new_status} size="sm" />
                      </div>
                      {entry.reason && (
                        <p className="text-xs text-surface-700 font-medium">"{entry.reason}"</p>
                      )}
                      <div className="flex items-center gap-2 text-[11px] text-surface-400">
                        {entry.changed_by_name && <span>By {entry.changed_by_name}</span>}
                        <span>•</span>
                        <span>{new Date(entry.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Staff Update Status Modal */}
      {showStatusModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="card p-6 max-w-md w-full shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-surface-900">Update Application Stage</h3>
              <button
                onClick={() => setShowStatusModal(false)}
                className="text-surface-400 hover:text-surface-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleStatusUpdate} className="space-y-4">
              <div>
                <label className="label-text">Select New Stage</label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="input-field"
                  required
                >
                  {ALL_STATUS_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="label-text">Reason or Notes (Optional)</label>
                <textarea
                  rows={3}
                  value={statusReason}
                  onChange={(e) => setStatusReason(e.target.value)}
                  placeholder="e.g., Passed technical screening, scheduling interview round 2..."
                  className="input-field text-xs resize-none"
                  maxLength={1000}
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowStatusModal(false)}
                  className="btn-secondary !text-xs !py-2"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updatingStatus}
                  className="btn-primary !text-xs !py-2"
                >
                  {updatingStatus ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" /> Saving...
                    </>
                  ) : (
                    'Save Transition'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Candidate Withdraw Confirmation Modal */}
      {showWithdrawModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="card p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-surface-900">Withdraw Application?</h3>
            <p className="text-xs text-surface-600 leading-relaxed">
              Are you sure you want to withdraw your application for{' '}
              <strong>{application.job_title}</strong>? This action cannot be undone.
            </p>
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowWithdrawModal(false)}
                className="btn-secondary !text-xs !py-2"
              >
                Keep Application
              </button>
              <button
                type="button"
                onClick={handleWithdraw}
                disabled={withdrawing}
                className="btn-danger !text-xs !py-2"
              >
                {withdrawing ? 'Withdrawing...' : 'Yes, Withdraw'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
