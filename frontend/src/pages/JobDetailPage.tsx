/**
 * Job Detail & Public Application Page.
 * Displays full job specifications and allows candidates to apply directly.
 */

import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate, useLocation } from 'react-router-dom';
import api from '../services/api';
import type { Job, ApplicationListResponse } from '../types';
import StatusBadge from '../components/StatusBadge';
import { useAuth } from '../hooks/useAuth';
import {
  Briefcase, MapPin, Clock, DollarSign, Calendar, Users,
  ArrowLeft, Upload, FileText, CheckCircle, AlertCircle,
  Share2, Building2, Loader2, Sparkles, Check, X, Award,
} from 'lucide-react';
import toast from 'react-hot-toast';

export default function JobDetailPage() {
  const { jobId, id } = useParams<{ jobId?: string; id?: string }>();
  const effectiveJobId = jobId || id;
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, user, login } = useAuth();

  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Application state
  const [hasApplied, setHasApplied] = useState(false);
  const [existingStatus, setExistingStatus] = useState<string | null>(null);
  const [appliedDate, setAppliedDate] = useState<string | null>(null);
  const [checkingApplication, setCheckingApplication] = useState(false);

  // Form state
  const [coverLetter, setCoverLetter] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [quickLoginLoading, setQuickLoginLoading] = useState(false);

  // Fetch job details
  useEffect(() => {
    if (!effectiveJobId) return;

    const fetchJob = async () => {
      setLoading(true);
      setError(null);
      try {
        const { data } = await api.get<Job>(`/jobs/public/${effectiveJobId}`);
        setJob(data);
      } catch (err: any) {
        if (err.response?.status === 404) {
          setError('This position does not exist or has been closed.');
        } else {
          setError('Failed to load job details. Please try again later.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchJob();
  }, [effectiveJobId]);

  // Check if current user has already applied (if candidate)
  useEffect(() => {
    if (!isAuthenticated || user?.role !== 'candidate' || !effectiveJobId) {
      setHasApplied(false);
      setExistingStatus(null);
      return;
    }

    const checkApplication = async () => {
      setCheckingApplication(true);
      try {
        const { data } = await api.get<ApplicationListResponse>(`/applications?job_id=${effectiveJobId}`);
        if (data.applications && data.applications.length > 0) {
          setHasApplied(true);
          setExistingStatus(data.applications[0].status);
          setAppliedDate(data.applications[0].applied_at);
        } else {
          setHasApplied(false);
        }
      } catch {
        // Silently ignore check failure
      } finally {
        setCheckingApplication(false);
      }
    };

    checkApplication();
  }, [isAuthenticated, user, effectiveJobId]);

  // Quick 1-click Demo Login as candidate
  const handleQuickDemoLogin = async () => {
    setQuickLoginLoading(true);
    try {
      await login({ email: 'alex@example.com', password: 'Demo1234!' });
      toast.success('Logged in as Alex Johnson (Demo Candidate)');
    } catch {
      toast.error('Quick demo login failed');
    } finally {
      setQuickLoginLoading(false);
    }
  };

  // Submit Application
  const handleApply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!effectiveJobId) return;

    setSubmitting(true);
    try {
      let resumeId: string | null = null;

      // 1. Upload resume if selected
      if (selectedFile) {
        const formData = new FormData();
        formData.append('file', selectedFile);
        const { data: resumeData } = await api.post('/resumes', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        resumeId = resumeData.id;
      }

      // 2. Submit application
      const payload: { resume_id?: string | null; cover_letter?: string | null } = {
        cover_letter: coverLetter.trim() || null,
      };
      if (resumeId) {
        payload.resume_id = resumeId;
      }

      const { data: appData } = await api.post(`/applications/jobs/${effectiveJobId}/apply`, payload);

      toast.success('Application submitted successfully!');
      setHasApplied(true);
      setExistingStatus(appData.status || 'applied');
      setAppliedDate(appData.applied_at || new Date().toISOString());
      setSelectedFile(null);
      setCoverLetter('');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to submit application';
      toast.error(msg);
      if (err.response?.status === 409) {
        setHasApplied(true);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    toast.success('Link copied to clipboard!');
  };

  const formatSalary = (min?: number | null, max?: number | null) => {
    if (!min && !max) return null;
    const fmt = (n: number) => `$${(n / 1000).toFixed(0)}K`;
    if (min && max) return `${fmt(min)} – ${fmt(max)} / year`;
    if (min) return `From ${fmt(min)} / year`;
    return `Up to ${fmt(max!)} / year`;
  };

  // Parse bullet-pointed text (split by newlines or bullets)
  const renderList = (text?: string | null) => {
    if (!text) return null;
    const items = text
      .split('\n')
      .map((s) => s.replace(/^[\s•\-\*]+/, '').trim())
      .filter(Boolean);

    if (items.length <= 1 && !text.includes('\n')) {
      return <p className="text-surface-600 leading-relaxed">{text}</p>;
    }

    return (
      <ul className="space-y-2.5">
        {items.map((item, idx) => (
          <li key={idx} className="flex items-start gap-3 text-surface-600 text-sm leading-relaxed">
            <span className="w-1.5 h-1.5 rounded-full bg-primary-500 mt-2 shrink-0" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-surface-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-primary-600 animate-spin mx-auto mb-4" />
          <p className="text-surface-500 text-sm font-medium">Loading position details...</p>
        </div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="min-h-screen bg-surface-50 flex flex-col items-center justify-center px-4 py-16">
        <div className="card max-w-md w-full p-8 text-center animate-fade-in">
          <div className="w-16 h-16 bg-red-50 text-red-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold text-surface-900 mb-2">Position Not Found</h2>
          <p className="text-surface-500 mb-6 text-sm">
            {error || "The job posting you're looking for is either no longer available or the link is incorrect."}
          </p>
          <Link to="/careers" className="btn-primary w-full">
            <ArrowLeft className="w-4 h-4" /> Browse All Open Positions
          </Link>
        </div>
      </div>
    );
  }

  const isCandidate = user?.role === 'candidate';
  const isStaff = isAuthenticated && !isCandidate;

  return (
    <div className="min-h-screen bg-surface-50">
      {/* Top Navbar */}
      <header className="bg-white/80 backdrop-blur-md border-b border-surface-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/careers" className="flex items-center gap-2.5 font-bold text-surface-900">
              <div className="w-8 h-8 gradient-primary rounded-lg flex items-center justify-center text-white">
                <Briefcase className="w-4 h-4" />
              </div>
              <span>RecruitFlow</span>
            </Link>
            <span className="hidden sm:inline-block text-surface-300">/</span>
            <Link
              to="/careers"
              className="hidden sm:flex items-center gap-1.5 text-sm font-medium text-surface-600 hover:text-primary-600 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Back to All Positions
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleShare}
              className="btn-secondary !py-1.5 !px-3 text-xs"
              title="Copy link to job"
            >
              <Share2 className="w-3.5 h-3.5" /> Share
            </button>

            {isAuthenticated ? (
              <Link
                to={isCandidate ? '/my-dashboard' : '/dashboard'}
                className="btn-primary !py-1.5 !px-4 text-xs"
              >
                Dashboard
              </Link>
            ) : (
              <Link
                to="/login"
                state={{ from: location }}
                className="btn-secondary !py-1.5 !px-4 text-xs font-semibold"
              >
                Sign In
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* Hero Header */}
      <div className="gradient-primary text-white relative overflow-hidden">
        <div className="absolute inset-0 opacity-10 pointer-events-none">
          <div className="absolute -top-24 -right-24 w-96 h-96 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-1/3 w-80 h-80 bg-white rounded-full blur-2xl" />
        </div>

        <div className="max-w-7xl mx-auto px-6 py-12 relative z-10">
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <Link
              to="/careers"
              className="sm:hidden inline-flex items-center gap-1 text-xs text-white/80 hover:text-white mb-2"
            >
              <ArrowLeft className="w-3 h-3" /> All Positions
            </Link>
            {job.department && (
              <span className="px-3 py-1 bg-white/15 backdrop-blur-sm rounded-full text-xs font-medium">
                {job.department}
              </span>
            )}
            <StatusBadge status={job.work_mode} />
            <StatusBadge status={job.employment_type} />
          </div>

          <h1 className="text-3xl md:text-4xl lg:text-5xl font-extrabold tracking-tight mb-4">
            {job.title}
          </h1>

          <div className="flex flex-wrap items-center gap-y-2 gap-x-6 text-sm text-white/90">
            {job.location && (
              <div className="flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-white/70" />
                <span>{job.location}</span>
              </div>
            )}
            {formatSalary(job.salary_min, job.salary_max) && (
              <div className="flex items-center gap-1.5">
                <DollarSign className="w-4 h-4 text-white/70" />
                <span className="font-semibold">{formatSalary(job.salary_min, job.salary_max)}</span>
              </div>
            )}
            {job.openings > 0 && (
              <div className="flex items-center gap-1.5">
                <Users className="w-4 h-4 text-white/70" />
                <span>{job.openings} opening{job.openings > 1 ? 's' : ''}</span>
              </div>
            )}
            {job.deadline && (
              <div className="flex items-center gap-1.5">
                <Calendar className="w-4 h-4 text-white/70" />
                <span>Apply before {new Date(job.deadline).toLocaleDateString()}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content Layout */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Job Description & Details */}
          <div className="lg:col-span-8 space-y-8">
            {/* Overview */}
            <div className="card p-6 md:p-8 space-y-4">
              <h2 className="text-xl font-bold text-surface-900 flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-primary-600" />
                About the Role
              </h2>
              <p className="text-surface-700 leading-relaxed whitespace-pre-line text-base">
                {job.description}
              </p>
            </div>

            {/* Responsibilities */}
            {job.responsibilities && (
              <div className="card p-6 md:p-8 space-y-4">
                <h2 className="text-xl font-bold text-surface-900 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-primary-600" />
                  Key Responsibilities
                </h2>
                {renderList(job.responsibilities)}
              </div>
            )}

            {/* Requirements */}
            {job.requirements && (
              <div className="card p-6 md:p-8 space-y-4">
                <h2 className="text-xl font-bold text-surface-900 flex items-center gap-2">
                  <Award className="w-5 h-5 text-primary-600" />
                  Requirements & Qualifications
                </h2>
                {renderList(job.requirements)}
              </div>
            )}

            {/* Preferred Skills */}
            {job.preferred_skills && (
              <div className="card p-6 md:p-8 space-y-4">
                <h2 className="text-xl font-bold text-surface-900 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-primary-600" />
                  Preferred Skills & Experience
                </h2>
                {renderList(job.preferred_skills)}
              </div>
            )}

            {/* Company Culture & Perks */}
            <div className="card p-6 md:p-8 space-y-4 bg-gradient-to-br from-white to-primary-50/30">
              <h2 className="text-xl font-bold text-surface-900 flex items-center gap-2">
                <Building2 className="w-5 h-5 text-primary-600" />
                Why Join RecruitFlow?
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                <div className="p-4 rounded-xl bg-white border border-surface-200">
                  <h4 className="font-semibold text-surface-900 text-sm mb-1">Competitive Compensation</h4>
                  <p className="text-xs text-surface-600">Top-tier base salary plus comprehensive health, dental, and vision insurance.</p>
                </div>
                <div className="p-4 rounded-xl bg-white border border-surface-200">
                  <h4 className="font-semibold text-surface-900 text-sm mb-1">Growth & Learning</h4>
                  <p className="text-xs text-surface-600">Annual professional development budget and clear career advancement tracks.</p>
                </div>
                <div className="p-4 rounded-xl bg-white border border-surface-200">
                  <h4 className="font-semibold text-surface-900 text-sm mb-1">Work-Life Balance</h4>
                  <p className="text-xs text-surface-600">Flexible hybrid/remote options and generous paid time off.</p>
                </div>
                <div className="p-4 rounded-xl bg-white border border-surface-200">
                  <h4 className="font-semibold text-surface-900 text-sm mb-1">Modern Tech Stack</h4>
                  <p className="text-xs text-surface-600">Work with contemporary architecture, high impact engineering, and great tooling.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Application Form & Snapshot */}
          <div className="lg:col-span-4 space-y-6 lg:sticky lg:top-24">
            {/* Staff Banner (if viewing as admin/recruiter) */}
            {isStaff && (
              <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-sm space-y-3">
                <div className="flex items-center gap-2 font-semibold">
                  <AlertCircle className="w-4 h-4 text-amber-600" />
                  <span>Staff Preview Mode</span>
                </div>
                <p className="text-xs text-amber-800">
                  You are viewing this job as <strong>{user?.name}</strong> ({user?.role}).
                </p>
                <div className="flex flex-col gap-2 pt-1">
                  <Link
                    to={`/applications?job_id=${effectiveJobId}`}
                    className="btn-secondary !text-xs !py-1.5 w-full justify-center"
                  >
                    View Applications for this Job
                  </Link>
                  <Link
                    to="/jobs"
                    className="text-xs text-amber-800 hover:text-amber-950 font-medium text-center"
                  >
                    Back to Jobs Management
                  </Link>
                </div>
              </div>
            )}

            {/* Application Card */}
            <div className="card p-6 md:p-7 shadow-lg border-primary-100">
              <h3 className="text-xl font-bold text-surface-900 mb-2">Apply for this Role</h3>
              <p className="text-xs text-surface-500 mb-6">
                Take the next step in your career with RecruitFlow.
              </p>

              {checkingApplication ? (
                <div className="py-8 text-center">
                  <Loader2 className="w-6 h-6 text-primary-500 animate-spin mx-auto mb-2" />
                  <p className="text-xs text-surface-500">Checking your application status...</p>
                </div>
              ) : hasApplied ? (
                /* Already Applied State */
                <div className="p-5 rounded-xl bg-emerald-50 border border-emerald-200 text-center space-y-3 animate-fade-in">
                  <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
                    <Check className="w-6 h-6 stroke-[3]" />
                  </div>
                  <h4 className="font-bold text-emerald-900 text-base">Application Submitted!</h4>
                  <p className="text-xs text-emerald-700 leading-relaxed">
                    You have applied for this position. Our hiring team is reviewing your profile.
                  </p>
                  {existingStatus && (
                    <div className="pt-2">
                      <span className="text-[11px] text-surface-500 block mb-1">Current Status:</span>
                      <StatusBadge status={existingStatus} />
                    </div>
                  )}
                  {appliedDate && (
                    <p className="text-[11px] text-surface-400">
                      Submitted on {new Date(appliedDate).toLocaleDateString()}
                    </p>
                  )}
                  <div className="pt-3">
                    <Link to="/my-applications" className="btn-primary !text-xs !py-2 w-full justify-center">
                      Track in My Applications
                    </Link>
                  </div>
                </div>
              ) : isAuthenticated && isCandidate ? (
                /* Candidate Apply Form */
                <form onSubmit={handleApply} className="space-y-4">
                  {/* Candidate Info Pill */}
                  <div className="p-3 bg-surface-50 rounded-xl border border-surface-200 text-xs">
                    <p className="font-semibold text-surface-800">{user?.name}</p>
                    <p className="text-surface-500">{user?.email}</p>
                  </div>

                  {/* Resume Upload */}
                  <div>
                    <label className="label-text">
                      Resume <span className="text-surface-400 font-normal">(PDF or DOCX, max 10MB)</span>
                    </label>

                    {selectedFile ? (
                      <div className="flex items-center justify-between p-3 bg-primary-50 border border-primary-200 rounded-xl text-xs">
                        <div className="flex items-center gap-2 overflow-hidden">
                          <FileText className="w-4 h-4 text-primary-600 shrink-0" />
                          <span className="font-medium text-primary-900 truncate">
                            {selectedFile.name}
                          </span>
                          <span className="text-surface-400 shrink-0">
                            ({(selectedFile.size / 1024 / 1024).toFixed(1)} MB)
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => setSelectedFile(null)}
                          className="p-1 hover:bg-primary-100 rounded-lg text-primary-700 transition-colors"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ) : (
                      <label className="border-2 border-dashed border-surface-200 hover:border-primary-400 hover:bg-primary-50/50 rounded-xl p-4 flex flex-col items-center justify-center cursor-pointer transition-all">
                        <Upload className="w-6 h-6 text-surface-400 mb-1" />
                        <span className="text-xs font-semibold text-surface-700">Click to upload resume</span>
                        <span className="text-[11px] text-surface-400">PDF, DOCX up to 10MB</span>
                        <input
                          type="file"
                          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) {
                              if (file.size > 10 * 1024 * 1024) {
                                toast.error('File size exceeds 10MB limit');
                                return;
                              }
                              setSelectedFile(file);
                            }
                          }}
                          className="hidden"
                        />
                      </label>
                    )}
                  </div>

                  {/* Cover Letter */}
                  <div>
                    <label className="label-text">
                      Cover Letter / Note <span className="text-surface-400 font-normal">(Optional)</span>
                    </label>
                    <textarea
                      rows={4}
                      value={coverLetter}
                      onChange={(e) => setCoverLetter(e.target.value)}
                      placeholder="Share a brief introduction or why you are excited about this opportunity..."
                      className="input-field text-xs resize-none"
                      maxLength={5000}
                    />
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={submitting}
                    className="btn-primary w-full justify-center !py-2.5 mt-2"
                  >
                    {submitting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" /> Submitting...
                      </>
                    ) : (
                      <>Submit Application</>
                    )}
                  </button>
                </form>
              ) : (
                /* Unauthenticated Visitor State */
                <div className="space-y-4">
                  <p className="text-xs text-surface-600 leading-relaxed">
                    Sign in with your candidate account or register in seconds to apply for this position.
                  </p>

                  <div className="flex flex-col gap-2">
                    <Link
                      to="/login"
                      state={{ from: location }}
                      className="btn-primary w-full justify-center"
                    >
                      Sign In to Apply
                    </Link>
                    <Link
                      to="/register"
                      state={{ from: location }}
                      className="btn-secondary w-full justify-center"
                    >
                      Create Candidate Account
                    </Link>
                  </div>

                  {/* Quick 1-Click Demo Apply */}
                  <div className="pt-3 border-t border-surface-100">
                    <p className="text-[11px] font-semibold text-surface-500 mb-2 uppercase tracking-wider">
                      Demo Evaluation
                    </p>
                    <button
                      type="button"
                      onClick={handleQuickDemoLogin}
                      disabled={quickLoginLoading}
                      className="w-full text-xs py-2 px-3 rounded-xl bg-primary-50 text-primary-700 hover:bg-primary-100 font-semibold border border-primary-200 transition-colors flex items-center justify-center gap-1.5"
                    >
                      {quickLoginLoading ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Sparkles className="w-3.5 h-3.5" />
                      )}
                      1-Click Apply as Demo Candidate
                    </button>
                    <p className="text-[10px] text-surface-400 mt-1 text-center">
                      Auto-fills Alex Johnson (Candidate)
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Quick Job Facts Card */}
            <div className="card p-6 space-y-4 text-xs">
              <h4 className="font-bold text-surface-900 text-sm">Role Summary</h4>
              <div className="space-y-3 text-surface-600">
                <div className="flex justify-between py-1 border-b border-surface-100">
                  <span className="text-surface-400">Department</span>
                  <span className="font-semibold text-surface-800">{job.department || 'General'}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-surface-100">
                  <span className="text-surface-400">Employment Type</span>
                  <span className="capitalize font-semibold text-surface-800">
                    {job.employment_type.replace('_', ' ')}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-surface-100">
                  <span className="text-surface-400">Work Mode</span>
                  <span className="capitalize font-semibold text-surface-800">{job.work_mode}</span>
                </div>
                {job.experience_min !== null && job.experience_min !== undefined && (
                  <div className="flex justify-between py-1 border-b border-surface-100">
                    <span className="text-surface-400">Experience</span>
                    <span className="font-semibold text-surface-800">
                      {job.experience_min}
                      {job.experience_max ? ` – ${job.experience_max} yrs` : '+ yrs'}
                    </span>
                  </div>
                )}
                {job.location && (
                  <div className="flex justify-between py-1 border-b border-surface-100">
                    <span className="text-surface-400">Location</span>
                    <span className="font-semibold text-surface-800">{job.location}</span>
                  </div>
                )}
                {job.deadline && (
                  <div className="flex justify-between py-1 border-b border-surface-100">
                    <span className="text-surface-400">Deadline</span>
                    <span className="font-semibold text-surface-800">
                      {new Date(job.deadline).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
