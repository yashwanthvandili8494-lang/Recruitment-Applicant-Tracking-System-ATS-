/**
 * Recruiter/Admin Dashboard — real database-backed metrics.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import type { DashboardOverview, RecruitmentFunnel } from '../types';
import {
  Briefcase, FileText, Clock, Calendar, Gift, UserCheck,
  TrendingUp, ArrowRight, Loader2,
} from 'lucide-react';

export default function DashboardPage() {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [funnel, setFunnel] = useState<RecruitmentFunnel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [overviewRes, funnelRes] = await Promise.all([
          api.get<DashboardOverview>('/dashboard/overview'),
          api.get<RecruitmentFunnel[]>('/dashboard/recruitment-funnel'),
        ]);
        setOverview(overviewRes.data);
        setFunnel(funnelRes.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-2xl text-red-700">
        {error}
      </div>
    );
  }

  const metrics = [
    { label: 'Open Positions', value: overview?.total_open_jobs ?? 0, icon: Briefcase, color: 'from-blue-500 to-blue-600', bgColor: 'bg-blue-50', textColor: 'text-blue-600' },
    { label: 'Total Applications', value: overview?.total_applications ?? 0, icon: FileText, color: 'from-purple-500 to-purple-600', bgColor: 'bg-purple-50', textColor: 'text-purple-600' },
    { label: 'Awaiting Review', value: overview?.applications_awaiting_review ?? 0, icon: Clock, color: 'from-amber-500 to-amber-600', bgColor: 'bg-amber-50', textColor: 'text-amber-600' },
    { label: 'Interviews Scheduled', value: overview?.interviews_scheduled ?? 0, icon: Calendar, color: 'from-cyan-500 to-cyan-600', bgColor: 'bg-cyan-50', textColor: 'text-cyan-600' },
    { label: 'Offers Pending', value: overview?.offers_pending ?? 0, icon: Gift, color: 'from-emerald-500 to-emerald-600', bgColor: 'bg-emerald-50', textColor: 'text-emerald-600' },
    { label: 'Candidates Hired', value: overview?.candidates_hired ?? 0, icon: UserCheck, color: 'from-green-500 to-green-600', bgColor: 'bg-green-50', textColor: 'text-green-600' },
  ];

  const stageColors: Record<string, string> = {
    applied: '#3b82f6',
    under_review: '#f59e0b',
    shortlisted: '#6366f1',
    interview_scheduled: '#8b5cf6',
    interview_completed: '#06b6d4',
    offered: '#10b981',
    hired: '#22c55e',
    rejected: '#ef4444',
    withdrawn: '#6b7280',
    on_hold: '#f97316',
  };

  const totalApps = funnel.reduce((sum, f) => sum + f.count, 0);

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-surface-900">Dashboard</h1>
        <p className="text-surface-500 mt-1">Recruitment pipeline overview</p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {metrics.map((metric, i) => (
          <div
            key={metric.label}
            className={`metric-card opacity-0 animate-fade-in stagger-${i + 1}`}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-surface-500">{metric.label}</p>
                <p className="text-3xl font-bold text-surface-900 mt-2">{metric.value}</p>
              </div>
              <div className={`w-12 h-12 ${metric.bgColor} rounded-xl flex items-center justify-center`}>
                <metric.icon className={`w-6 h-6 ${metric.textColor}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recruitment Funnel */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary-500" />
            <h2 className="text-lg font-semibold text-surface-900">Recruitment Funnel</h2>
          </div>
          <Link to="/applications" className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
            View all <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {funnel.length === 0 ? (
          <p className="text-surface-400 text-center py-8">No applications yet</p>
        ) : (
          <div className="space-y-3">
            {funnel.map((item) => {
              const percentage = totalApps > 0 ? (item.count / totalApps) * 100 : 0;
              const color = stageColors[item.stage] || '#6b7280';
              const label = item.stage.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

              return (
                <div key={item.stage} className="flex items-center gap-4">
                  <div className="w-40 text-sm font-medium text-surface-700 truncate">{label}</div>
                  <div className="flex-1 h-8 bg-surface-100 rounded-lg overflow-hidden relative">
                    <div
                      className="h-full rounded-lg transition-all duration-1000 ease-out"
                      style={{ width: `${Math.max(percentage, 2)}%`, backgroundColor: color }}
                    />
                  </div>
                  <div className="w-12 text-right text-sm font-semibold text-surface-700">
                    {item.count}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link to="/jobs" className="card p-5 group cursor-pointer hover:border-primary-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-50 rounded-xl flex items-center justify-center group-hover:bg-primary-100 transition-colors">
              <Briefcase className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <p className="font-semibold text-surface-900">Manage Jobs</p>
              <p className="text-xs text-surface-500">Create and publish vacancies</p>
            </div>
          </div>
        </Link>
        <Link to="/applications" className="card p-5 group cursor-pointer hover:border-primary-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-50 rounded-xl flex items-center justify-center group-hover:bg-purple-100 transition-colors">
              <FileText className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="font-semibold text-surface-900">Review Applications</p>
              <p className="text-xs text-surface-500">Screen and evaluate candidates</p>
            </div>
          </div>
        </Link>
        <Link to="/interviews" className="card p-5 group cursor-pointer hover:border-primary-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-cyan-50 rounded-xl flex items-center justify-center group-hover:bg-cyan-100 transition-colors">
              <Calendar className="w-5 h-5 text-cyan-600" />
            </div>
            <div>
              <p className="font-semibold text-surface-900">Schedule Interviews</p>
              <p className="text-xs text-surface-500">Organize upcoming interviews</p>
            </div>
          </div>
        </Link>
      </div>
    </div>
  );
}
