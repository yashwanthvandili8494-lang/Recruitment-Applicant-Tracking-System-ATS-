/**
 * Applications tracking page — view and manage applications with status filtering.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import type { Application, ApplicationListResponse } from '../types';
import StatusBadge from '../components/StatusBadge';
import { useAuth } from '../hooks/useAuth';
import {
  FileText, Search, Loader2, ChevronLeft, ChevronRight,
  ArrowUpDown, Eye, User,
} from 'lucide-react';
import toast from 'react-hot-toast';

const STATUS_OPTIONS = [
  '', 'applied', 'under_review', 'shortlisted', 'interview_scheduled',
  'interview_completed', 'offered', 'hired', 'rejected', 'withdrawn', 'on_hold',
];

export default function ApplicationsPage() {
  const { user } = useAuth();
  const [applications, setApplications] = useState<Application[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [showStatusModal, setShowStatusModal] = useState<Application | null>(null);
  const [newStatus, setNewStatus] = useState('');
  const [reason, setReason] = useState('');

  const fetchApplications = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: '20' });
      if (statusFilter) params.append('status', statusFilter);

      const { data } = await api.get<ApplicationListResponse>(`/applications?${params}`);
      setApplications(data.applications);
      setTotal(data.total);
    } catch {
      toast.error('Failed to load applications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchApplications(); }, [page, statusFilter]);

  const handleStatusUpdate = async () => {
    if (!showStatusModal || !newStatus) return;
    try {
      await api.patch(`/applications/${showStatusModal.id}/status`, {
        status: newStatus,
        reason: reason || undefined,
      });
      toast.success('Status updated');
      setShowStatusModal(null);
      setNewStatus('');
      setReason('');
      fetchApplications();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Invalid status transition');
    }
  };

  const totalPages = Math.ceil(total / 20);
  const isStaff = user?.role !== 'candidate';

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">
            {isStaff ? 'Applications' : 'My Applications'}
          </h1>
          <p className="text-surface-500 mt-1">{total} total</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="input-field w-auto"
        >
          <option value="">All Statuses</option>
          {STATUS_OPTIONS.filter(Boolean).map((s) => (
            <option key={s} value={s}>
              {s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
            </option>
          ))}
        </select>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      ) : applications.length === 0 ? (
        <div className="text-center py-16 card">
          <FileText className="w-12 h-12 text-surface-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-surface-700">No applications found</h3>
          <p className="text-surface-500 mt-1">
            {isStaff ? 'Applications will appear here when candidates apply' : 'Browse jobs and apply to get started'}
          </p>
          {!isStaff && (
            <Link to="/careers" className="btn-primary mt-4">Browse Jobs</Link>
          )}
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-surface-50 border-b border-surface-100">
                <tr>
                  {isStaff && <th className="table-header">Candidate</th>}
                  <th className="table-header">Job</th>
                  <th className="table-header">Status</th>
                  <th className="table-header">Applied</th>
                  <th className="table-header">Updated</th>
                  <th className="table-header w-24">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100">
                {applications.map((app) => (
                  <tr key={app.id} className="hover:bg-surface-50/50 transition-colors">
                    {isStaff && (
                      <td className="table-cell">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 gradient-primary rounded-full flex items-center justify-center text-white text-xs font-bold">
                            {app.candidate_name?.charAt(0) || '?'}
                          </div>
                          <span className="font-medium text-surface-900">{app.candidate_name || 'Unknown'}</span>
                        </div>
                      </td>
                    )}
                    <td className="table-cell font-medium text-surface-900">{app.job_title || '—'}</td>
                    <td className="table-cell"><StatusBadge status={app.status} /></td>
                    <td className="table-cell text-surface-500 text-xs">
                      {new Date(app.applied_at).toLocaleDateString()}
                    </td>
                    <td className="table-cell text-surface-500 text-xs">
                      {new Date(app.updated_at).toLocaleDateString()}
                    </td>
                    <td className="table-cell">
                      <div className="flex items-center gap-1">
                        <Link
                          to={`/applications/${app.id}`}
                          className="p-1.5 hover:bg-surface-100 rounded-lg text-surface-400 hover:text-primary-600"
                          title="View"
                        >
                          <Eye className="w-4 h-4" />
                        </Link>
                        {isStaff && (
                          <button
                            onClick={() => { setShowStatusModal(app); setNewStatus(''); }}
                            className="p-1.5 hover:bg-surface-100 rounded-lg text-surface-400 hover:text-primary-600"
                            title="Update Status"
                          >
                            <ArrowUpDown className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between px-6 py-4 border-t border-surface-100">
              <p className="text-sm text-surface-500">
                Showing {(page - 1) * 20 + 1}–{Math.min(page * 20, total)} of {total}
              </p>
              <div className="flex items-center gap-2">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary !px-3 !py-1.5 disabled:opacity-30">
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="btn-secondary !px-3 !py-1.5 disabled:opacity-30">
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Status Update Modal */}
      {showStatusModal && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 animate-fade-in">
            <h3 className="text-lg font-semibold text-surface-900 mb-4">Update Application Status</h3>
            <p className="text-sm text-surface-500 mb-4">
              Current: <StatusBadge status={showStatusModal.status} />
            </p>
            <div className="space-y-4">
              <div>
                <label className="label-text">New Status</label>
                <select value={newStatus} onChange={(e) => setNewStatus(e.target.value)} className="input-field">
                  <option value="">Select status...</option>
                  {STATUS_OPTIONS.filter(Boolean).map((s) => (
                    <option key={s} value={s}>
                      {s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label-text">Reason (optional)</label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="input-field"
                  rows={3}
                  placeholder="Add a note about this status change..."
                />
              </div>
              <div className="flex gap-3 justify-end">
                <button onClick={() => setShowStatusModal(null)} className="btn-secondary">Cancel</button>
                <button onClick={handleStatusUpdate} disabled={!newStatus} className="btn-primary">
                  Update Status
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
