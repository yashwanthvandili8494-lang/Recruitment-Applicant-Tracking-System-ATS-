/**
 * Jobs management page — list, filter, and manage job postings.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import type { Job, JobListResponse } from '../types';
import StatusBadge from '../components/StatusBadge';
import {
  Plus, Search, Briefcase, Loader2,
  ChevronLeft, ChevronRight, MoreHorizontal,
} from 'lucide-react';
import toast from 'react-hot-toast';

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [activeMenu, setActiveMenu] = useState<string | null>(null);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: '20' });
      if (search) params.append('search', search);
      if (statusFilter) params.append('status', statusFilter);

      const { data } = await api.get<JobListResponse>(`/jobs?${params}`);
      setJobs(data.jobs);
      setTotal(data.total);
    } catch {
      toast.error('Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchJobs(); }, [page, search, statusFilter]);

  const handlePublish = async (jobId: string) => {
    try {
      await api.post(`/jobs/${jobId}/publish`);
      toast.success('Job published');
      fetchJobs();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to publish');
    }
    setActiveMenu(null);
  };

  const handleClose = async (jobId: string) => {
    try {
      await api.post(`/jobs/${jobId}/close`);
      toast.success('Job closed');
      fetchJobs();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to close');
    }
    setActiveMenu(null);
  };

  const totalPages = Math.ceil(total / 20);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Jobs</h1>
          <p className="text-surface-500 mt-1">{total} total job postings</p>
        </div>
        <Link to="/jobs/new" className="btn-primary">
          <Plus className="w-4 h-4" /> Create Job
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
          <input
            type="text"
            placeholder="Search jobs..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="input-field pl-10"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="input-field w-auto"
        >
          <option value="">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="published">Published</option>
          <option value="paused">Paused</option>
          <option value="closed">Closed</option>
          <option value="archived">Archived</option>
        </select>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-16 card">
          <Briefcase className="w-12 h-12 text-surface-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-surface-700">No jobs found</h3>
          <p className="text-surface-500 mt-1 mb-4">Get started by creating your first job posting</p>
          <Link to="/jobs/new" className="btn-primary">
            <Plus className="w-4 h-4" /> Create Job
          </Link>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-surface-50 border-b border-surface-100">
                <tr>
                  <th className="table-header">Title</th>
                  <th className="table-header">Department</th>
                  <th className="table-header">Location</th>
                  <th className="table-header">Type</th>
                  <th className="table-header">Status</th>
                  <th className="table-header">Deadline</th>
                  <th className="table-header w-12"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100">
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-surface-50/50 transition-colors">
                    <td className="table-cell">
                      <Link to={`/jobs/${job.id}`} className="font-semibold text-surface-900 hover:text-primary-600">
                        {job.title}
                      </Link>
                    </td>
                    <td className="table-cell text-surface-500">{job.department || '—'}</td>
                    <td className="table-cell text-surface-500">{job.location || '—'}</td>
                    <td className="table-cell"><StatusBadge status={job.employment_type} /></td>
                    <td className="table-cell"><StatusBadge status={job.status} /></td>
                    <td className="table-cell text-surface-500">
                      {job.deadline ? new Date(job.deadline).toLocaleDateString() : '—'}
                    </td>
                    <td className="table-cell relative">
                      <button
                        onClick={() => setActiveMenu(activeMenu === job.id ? null : job.id)}
                        className="p-1.5 hover:bg-surface-100 rounded-lg transition-colors"
                      >
                        <MoreHorizontal className="w-4 h-4 text-surface-400" />
                      </button>
                      {activeMenu === job.id && (
                        <div className="absolute right-6 top-12 w-40 bg-white rounded-xl shadow-lg border border-surface-100 py-1 z-10">
                          <Link
                            to={`/jobs/${job.id}/edit`}
                            className="block px-4 py-2 text-sm text-surface-700 hover:bg-surface-50"
                          >
                            Edit
                          </Link>
                          {(job.status === 'draft' || job.status === 'paused') && (
                            <button
                              onClick={() => handlePublish(job.id)}
                              className="block w-full text-left px-4 py-2 text-sm text-green-600 hover:bg-green-50"
                            >
                              Publish
                            </button>
                          )}
                          {job.status === 'published' && (
                            <button
                              onClick={() => handleClose(job.id)}
                              className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                            >
                              Close
                            </button>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-6 py-4 border-t border-surface-100">
              <p className="text-sm text-surface-500">
                Showing {(page - 1) * 20 + 1}–{Math.min(page * 20, total)} of {total}
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn-secondary !px-3 !py-1.5 disabled:opacity-30"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="btn-secondary !px-3 !py-1.5 disabled:opacity-30"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
