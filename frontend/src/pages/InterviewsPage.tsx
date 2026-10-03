/**
 * Interviews list/calendar page.
 */

import { useState, useEffect } from 'react';
import api from '../services/api';
import type { Interview, InterviewListResponse } from '../types';
import StatusBadge from '../components/StatusBadge';
import { Calendar, Video, Phone, Users, MapPin, Clock, Loader2 } from 'lucide-react';

const typeIcons: Record<string, any> = {
  video: Video,
  phone: Phone,
  in_person: MapPin,
  technical: Users,
  behavioral: Users,
  panel: Users,
};

export default function InterviewsPage() {
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams({ page_size: '50' });
        if (statusFilter) params.append('status', statusFilter);
        const { data } = await api.get<InterviewListResponse>(`/interviews?${params}`);
        setInterviews(data.interviews);
      } catch {
        setInterviews([]);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [statusFilter]);

  const formatTime = (dt: string) => {
    return new Date(dt).toLocaleString(undefined, {
      dateStyle: 'medium', timeStyle: 'short',
    });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Interviews</h1>
          <p className="text-surface-500 mt-1">{interviews.length} total</p>
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="input-field w-auto"
        >
          <option value="">All Statuses</option>
          <option value="scheduled">Scheduled</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      ) : interviews.length === 0 ? (
        <div className="text-center py-16 card">
          <Calendar className="w-12 h-12 text-surface-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-surface-700">No interviews scheduled</h3>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {interviews.map((interview) => {
            const TypeIcon = typeIcons[interview.interview_type] || Calendar;
            return (
              <div key={interview.id} className="card p-5 hover:border-primary-200">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-primary-50 rounded-xl flex items-center justify-center">
                      <TypeIcon className="w-5 h-5 text-primary-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-surface-900">
                        Round {interview.interview_round}
                      </h3>
                      <p className="text-xs text-surface-500">
                        {interview.interview_type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                      </p>
                    </div>
                  </div>
                  <StatusBadge status={interview.status} />
                </div>

                {interview.job_title && (
                  <p className="text-sm text-surface-700 mb-1">
                    <span className="font-medium">Job:</span> {interview.job_title}
                  </p>
                )}
                {interview.candidate_name && (
                  <p className="text-sm text-surface-700 mb-3">
                    <span className="font-medium">Candidate:</span> {interview.candidate_name}
                  </p>
                )}

                <div className="flex items-center gap-2 text-xs text-surface-500 mb-2">
                  <Clock className="w-3 h-3" />
                  {formatTime(interview.start_time)} — {formatTime(interview.end_time)}
                </div>

                {interview.meeting_location && (
                  <div className="flex items-center gap-2 text-xs text-primary-600 mb-2">
                    <MapPin className="w-3 h-3" />
                    <a href={interview.meeting_location} target="_blank" rel="noopener" className="hover:underline truncate">
                      {interview.meeting_location}
                    </a>
                  </div>
                )}

                {interview.interviewers && interview.interviewers.length > 0 && (
                  <div className="flex items-center gap-1 mt-3 pt-3 border-t border-surface-100">
                    <Users className="w-3 h-3 text-surface-400" />
                    <span className="text-xs text-surface-500">
                      {interview.interviewers.map((i) => i.name).join(', ')}
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
