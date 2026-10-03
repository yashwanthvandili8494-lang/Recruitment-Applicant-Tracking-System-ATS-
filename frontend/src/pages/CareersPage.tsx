/**
 * Public careers page — shows published jobs to unauthenticated visitors.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import type { Job, JobListResponse } from '../types';
import StatusBadge from '../components/StatusBadge';
import {
  Briefcase, MapPin, Clock, Search, Filter,
  Building2, ArrowRight, Loader2, ChevronLeft, ChevronRight,
} from 'lucide-react';

export default function CareersPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [department, setDepartment] = useState('');
  const [workMode, setWorkMode] = useState('');

  useEffect(() => {
    const fetchJobs = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams({ page: String(page), page_size: '12' });
        if (search) params.append('search', search);
        if (department) params.append('department', department);
        if (workMode) params.append('work_mode', workMode);

        const { data } = await api.get<JobListResponse>(`/jobs/public?${params}`);
        setJobs(data.jobs);
        setTotal(data.total);
      } catch {
        setJobs([]);
      } finally {
        setLoading(false);
      }
    };
    fetchJobs();
  }, [page, search, department, workMode]);

  const totalPages = Math.ceil(total / 12);

  const formatSalary = (min?: number | null, max?: number | null) => {
    if (!min && !max) return null;
    const fmt = (n: number) => `$${(n / 1000).toFixed(0)}K`;
    if (min && max) return `${fmt(min)} – ${fmt(max)}`;
    if (min) return `From ${fmt(min)}`;
    return `Up to ${fmt(max!)}`;
  };

  return (
    <div className="min-h-screen bg-surface-50">
      {/* Hero */}
      <div className="gradient-primary text-white">
        <div className="max-w-7xl mx-auto px-6 py-16">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-white/20 backdrop-blur rounded-xl flex items-center justify-center">
              <Briefcase className="w-5 h-5" />
            </div>
            <span className="text-xl font-bold">RecruitFlow</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            Find Your Next<br />Opportunity
          </h1>
          <p className="text-lg text-white/80 max-w-xl mb-8">
            Explore open positions and take the next step in your career. We're looking for talented people to join our team.
          </p>

          {/* Search */}
          <div className="flex flex-col sm:flex-row gap-3 max-w-2xl">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/50" />
              <input
                type="text"
                placeholder="Search jobs..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                className="w-full pl-10 pr-4 py-3 bg-white/15 backdrop-blur border border-white/20 rounded-xl
                  text-white placeholder:text-white/50 outline-none focus:bg-white/20 focus:border-white/30 transition-all"
              />
            </div>
            <select
              value={workMode}
              onChange={(e) => { setWorkMode(e.target.value); setPage(1); }}
              className="px-4 py-3 bg-white/15 backdrop-blur border border-white/20 rounded-xl
                text-white outline-none focus:bg-white/20 appearance-none cursor-pointer"
            >
              <option value="" className="text-surface-900">All Work Modes</option>
              <option value="remote" className="text-surface-900">Remote</option>
              <option value="hybrid" className="text-surface-900">Hybrid</option>
              <option value="onsite" className="text-surface-900">On-site</option>
            </select>
          </div>
        </div>
      </div>

      {/* Job Grid */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="flex items-center justify-between mb-8">
          <p className="text-surface-600">
            <span className="font-semibold text-surface-900">{total}</span> open position{total !== 1 ? 's' : ''}
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-48">
            <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
          </div>
        ) : jobs.length === 0 ? (
          <div className="text-center py-16">
            <Briefcase className="w-12 h-12 text-surface-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-surface-700">No positions found</h3>
            <p className="text-surface-500 mt-1">Try adjusting your search or filters</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {jobs.map((job, i) => (
              <Link
                key={job.id}
                to={`/careers/${job.id}`}
                className={`card p-6 group cursor-pointer hover:border-primary-200 opacity-0 animate-fade-in stagger-${Math.min(i + 1, 6)}`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-10 h-10 gradient-primary rounded-xl flex items-center justify-center">
                    <Building2 className="w-5 h-5 text-white" />
                  </div>
                  <StatusBadge status={job.work_mode} />
                </div>
                <h3 className="text-lg font-semibold text-surface-900 group-hover:text-primary-600 transition-colors mb-2">
                  {job.title}
                </h3>
                {job.department && (
                  <p className="text-sm text-surface-500 mb-3">{job.department}</p>
                )}
                <div className="flex flex-wrap items-center gap-3 text-xs text-surface-500 mb-4">
                  {job.location && (
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3" />{job.location}
                    </span>
                  )}
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    <StatusBadge status={job.employment_type} size="sm" />
                  </span>
                </div>
                {formatSalary(job.salary_min, job.salary_max) && (
                  <p className="text-sm font-semibold text-primary-600 mb-3">
                    {formatSalary(job.salary_min, job.salary_max)}
                  </p>
                )}
                <div className="flex items-center text-sm text-primary-600 font-medium group-hover:gap-2 transition-all">
                  View Details <ArrowRight className="w-4 h-4 ml-1" />
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-10">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="btn-secondary !px-3 !py-2 disabled:opacity-30"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-4 py-2 text-sm text-surface-600">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="btn-secondary !px-3 !py-2 disabled:opacity-30"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
