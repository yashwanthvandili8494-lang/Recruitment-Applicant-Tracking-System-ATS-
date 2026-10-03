/**
 * Candidate Detail Page.
 * Displays candidate profile, skills, education, and application history.
 */

import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import type { CandidateProfile, Application, ApplicationListResponse } from '../types';
import StatusBadge from '../components/StatusBadge';
import {
  User, Mail, Phone, MapPin, Briefcase, GraduationCap,
  Calendar, ExternalLink, ArrowLeft, Loader2, AlertCircle,
  FileText, Globe, Eye,
} from 'lucide-react';

export default function CandidateDetailPage() {
  const { candidateId, id } = useParams<{ candidateId?: string; id?: string }>();
  const effectiveId = candidateId || id;

  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!effectiveId) return;

    const fetchCandidateData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [profileRes, appsRes] = await Promise.all([
          api.get<CandidateProfile>(`/candidates/${effectiveId}`),
          api.get<ApplicationListResponse>(`/candidates/${effectiveId}/applications`),
        ]);

        setProfile(profileRes.data);
        setApplications(appsRes.data.applications || []);
      } catch (err: any) {
        if (err.response?.status === 404) {
          setError('Candidate profile not found.');
        } else if (err.response?.status === 403) {
          setError('You do not have permission to view this candidate profile.');
        } else {
          setError('Failed to load candidate information.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchCandidateData();
  }, [effectiveId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-primary-600 animate-spin mx-auto mb-3" />
          <p className="text-surface-500 text-sm">Loading candidate profile...</p>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Link to="/candidates" className="inline-flex items-center gap-1.5 text-sm font-medium text-surface-600 hover:text-primary-600">
          <ArrowLeft className="w-4 h-4" /> Back to Candidates
        </Link>
        <div className="card p-12 text-center max-w-md mx-auto">
          <div className="w-14 h-14 bg-red-50 text-red-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-7 h-7" />
          </div>
          <h2 className="text-xl font-bold text-surface-900 mb-2">Candidate Not Found</h2>
          <p className="text-surface-500 text-sm mb-6">{error || 'This candidate does not exist.'}</p>
          <Link to="/candidates" className="btn-primary w-full justify-center">
            Return to Candidates
          </Link>
        </div>
      </div>
    );
  }

  const candidateName = profile.name || 'Candidate Profile';
  const candidateEmail = profile.email || 'No email provided';

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          to="/candidates"
          className="inline-flex items-center gap-2 text-sm font-medium text-surface-600 hover:text-primary-600 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Candidates
        </Link>

        {profile.email && (
          <a
            href={`mailto:${profile.email}`}
            className="btn-secondary !py-1.5 !px-3 text-xs"
          >
            <Mail className="w-3.5 h-3.5" /> Email Candidate
          </a>
        )}
      </div>

      {/* Profile Header Card */}
      <div className="card p-6 md:p-8">
        <div className="flex flex-col md:flex-row items-start md:items-center gap-6 justify-between">
          <div className="flex items-center gap-5">
            <div className="w-20 h-20 gradient-primary rounded-2xl flex items-center justify-center text-white text-3xl font-extrabold shadow-lg shadow-primary-500/20 shrink-0">
              {candidateName.charAt(0)}
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-surface-900">{candidateName}</h1>
              <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-sm text-surface-500 mt-1.5">
                <span className="flex items-center gap-1.5">
                  <Mail className="w-4 h-4 text-surface-400" />
                  {candidateEmail}
                </span>
                {profile.phone && (
                  <span className="flex items-center gap-1.5">
                    <Phone className="w-4 h-4 text-surface-400" />
                    {profile.phone}
                  </span>
                )}
                {profile.location && (
                  <span className="flex items-center gap-1.5">
                    <MapPin className="w-4 h-4 text-surface-400" />
                    {profile.location}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Quick stats pills */}
          <div className="flex items-center gap-3">
            {profile.experience_years !== null && profile.experience_years !== undefined && (
              <div className="px-3 py-1.5 rounded-xl bg-primary-50 border border-primary-200 text-xs font-semibold text-primary-700">
                {profile.experience_years} Years Experience
              </div>
            )}
            <div className="px-3 py-1.5 rounded-xl bg-surface-100 border border-surface-200 text-xs font-semibold text-surface-700">
              {applications.length} Application{applications.length !== 1 ? 's' : ''}
            </div>
          </div>
        </div>

        {/* Social / External Links */}
        {(profile.linkedin_url || profile.github_url || profile.portfolio_url) && (
          <div className="flex flex-wrap items-center gap-3 mt-6 pt-6 border-t border-surface-100">
            {profile.linkedin_url && (
              <a
                href={profile.linkedin_url}
                target="_blank"
                rel="noreferrer"
                className="btn-secondary !py-1.5 !px-3 text-xs"
              >
                <Linkedin className="w-3.5 h-3.5 text-blue-600" /> LinkedIn Profile
              </a>
            )}
            {profile.github_url && (
              <a
                href={profile.github_url}
                target="_blank"
                rel="noreferrer"
                className="btn-secondary !py-1.5 !px-3 text-xs"
              >
                <Github className="w-3.5 h-3.5 text-surface-800" /> GitHub Profile
              </a>
            )}
            {profile.portfolio_url && (
              <a
                href={profile.portfolio_url}
                target="_blank"
                rel="noreferrer"
                className="btn-secondary !py-1.5 !px-3 text-xs"
              >
                <Globe className="w-3.5 h-3.5 text-emerald-600" /> Portfolio Website
              </a>
            )}
          </div>
        )}
      </div>

      {/* Grid: Details & Applications */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Summary, Skills, Education */}
        <div className="lg:col-span-1 space-y-6">
          {/* Summary */}
          {profile.summary && (
            <div className="card p-6 space-y-3">
              <h3 className="font-bold text-surface-900 text-sm flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary-600" /> Professional Summary
              </h3>
              <p className="text-sm text-surface-600 leading-relaxed whitespace-pre-line">
                {profile.summary}
              </p>
            </div>
          )}

          {/* Skills */}
          {profile.skills && profile.skills.length > 0 && (
            <div className="card p-6 space-y-3">
              <h3 className="font-bold text-surface-900 text-sm flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-primary-600" /> Skills & Competencies
              </h3>
              <div className="flex flex-wrap gap-2 pt-1">
                {profile.skills.map((skill) => (
                  <span
                    key={skill}
                    className="px-2.5 py-1 text-xs font-medium rounded-lg bg-primary-50 text-primary-700 border border-primary-100"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Education */}
          {profile.education && profile.education.length > 0 && (
            <div className="card p-6 space-y-4">
              <h3 className="font-bold text-surface-900 text-sm flex items-center gap-2">
                <GraduationCap className="w-4 h-4 text-primary-600" /> Education
              </h3>
              <div className="space-y-3">
                {profile.education.map((edu, idx) => (
                  <div key={idx} className="p-3 bg-surface-50 rounded-xl border border-surface-200/60 text-xs">
                    <p className="font-semibold text-surface-900 text-sm">{edu.degree}</p>
                    <p className="text-surface-600 mt-0.5">{edu.university}</p>
                    {edu.year && <p className="text-surface-400 mt-1">Class of {edu.year}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Applications History */}
        <div className="lg:col-span-2 space-y-4">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-surface-900 flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-primary-600" />
                Applications Submitted ({applications.length})
              </h2>
            </div>

            {applications.length === 0 ? (
              <div className="text-center py-12 bg-surface-50 rounded-xl border border-dashed border-surface-200">
                <Briefcase className="w-10 h-10 text-surface-300 mx-auto mb-2" />
                <p className="text-sm font-medium text-surface-600">No applications on record</p>
                <p className="text-xs text-surface-400 mt-0.5">This candidate has not applied to any positions yet.</p>
              </div>
            ) : (
              <div className="divide-y divide-surface-100">
                {applications.map((app) => (
                  <div key={app.id} className="py-4 first:pt-0 last:pb-0 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-3">
                        <Link
                          to={`/applications/${app.id}`}
                          className="font-semibold text-surface-900 hover:text-primary-600 transition-colors"
                        >
                          {app.job_title || 'Position Application'}
                        </Link>
                        <StatusBadge status={app.status} />
                      </div>
                      <div className="flex items-center gap-4 text-xs text-surface-500">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3.5 h-3.5 text-surface-400" />
                          Applied {new Date(app.applied_at).toLocaleDateString()}
                        </span>
                        {app.updated_at && app.updated_at !== app.applied_at && (
                          <span className="text-surface-400">
                            Updated {new Date(app.updated_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                      {app.cover_letter && (
                        <p className="text-xs text-surface-600 line-clamp-2 mt-2 bg-surface-50 p-2.5 rounded-lg border border-surface-200/50">
                          "{app.cover_letter}"
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <Link
                        to={`/applications/${app.id}`}
                        className="btn-secondary !py-1.5 !px-3 text-xs"
                      >
                        <Eye className="w-3.5 h-3.5" /> View Application
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
