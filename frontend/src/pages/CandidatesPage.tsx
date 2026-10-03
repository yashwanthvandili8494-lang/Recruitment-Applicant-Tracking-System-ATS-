/**
 * Candidates list page — searchable, filterable candidate directory.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import type { CandidateSearch, CandidateListResponse } from '../types';
import StatusBadge from '../components/StatusBadge';
import {
  Users, Search, Loader2, MapPin, ChevronLeft, ChevronRight,
} from 'lucide-react';

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState<CandidateSearch[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams({ page: String(page), page_size: '20' });
        if (search) params.append('search', search);
        const { data } = await api.get<CandidateListResponse>(`/candidates?${params}`);
        setCandidates(data.candidates);
        setTotal(data.total);
      } catch {
        setCandidates([]);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [page, search]);

  const totalPages = Math.ceil(total / 20);

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-surface-900">Candidates</h1>
        <p className="text-surface-500 mt-1">{total} candidates</p>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
        <input
          type="text"
          placeholder="Search by name or email..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="input-field pl-10"
        />
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      ) : candidates.length === 0 ? (
        <div className="text-center py-16 card">
          <Users className="w-12 h-12 text-surface-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-surface-700">No candidates found</h3>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {candidates.map((c) => (
            <Link key={c.id} to={`/candidates/${c.user_id}`} className="card p-5 hover:border-primary-200 group">
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 gradient-primary rounded-full flex items-center justify-center text-white font-bold shrink-0">
                  {c.name.charAt(0)}
                </div>
                <div className="min-w-0">
                  <h3 className="font-semibold text-surface-900 group-hover:text-primary-600 truncate">{c.name}</h3>
                  <p className="text-sm text-surface-500 truncate">{c.email}</p>
                  {c.location && (
                    <p className="text-xs text-surface-400 flex items-center gap-1 mt-1">
                      <MapPin className="w-3 h-3" />{c.location}
                    </p>
                  )}
                </div>
              </div>
              {c.skills && c.skills.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {c.skills.slice(0, 4).map((skill) => (
                    <span key={skill} className="px-2 py-0.5 text-xs bg-primary-50 text-primary-700 rounded-full">
                      {skill}
                    </span>
                  ))}
                  {c.skills.length > 4 && (
                    <span className="px-2 py-0.5 text-xs bg-surface-100 text-surface-500 rounded-full">
                      +{c.skills.length - 4}
                    </span>
                  )}
                </div>
              )}
              {c.experience_years != null && (
                <p className="text-xs text-surface-500 mt-2">{c.experience_years} years experience</p>
              )}
            </Link>
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary !px-3 !py-2 disabled:opacity-30">
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-sm text-surface-600">Page {page} of {totalPages}</span>
          <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="btn-secondary !px-3 !py-2 disabled:opacity-30">
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}
