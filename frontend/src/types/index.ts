/**
 * API types matching the backend Pydantic schemas.
 * These ensure type safety between frontend and backend.
 */

// ───────────────── Auth ─────────────────

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  organization_id: string | null;
  created_at: string;
  updated_at: string;
}

export type UserRole = 'admin' | 'recruiter' | 'hiring_manager' | 'interviewer' | 'candidate';

// ───────────────── Jobs ─────────────────

export interface Job {
  id: string;
  organization_id: string;
  title: string;
  description: string;
  responsibilities: string | null;
  requirements: string | null;
  preferred_skills: string | null;
  department: string | null;
  employment_type: string;
  work_mode: string;
  location: string | null;
  experience_min: number | null;
  experience_max: number | null;
  salary_min: number | null;
  salary_max: number | null;
  openings: number;
  deadline: string | null;
  hiring_manager_id: string | null;
  status: JobStatus;
  created_at: string;
  updated_at: string;
  application_count?: number;
}

export type JobStatus = 'draft' | 'published' | 'paused' | 'closed' | 'archived';
export type EmploymentType = 'full_time' | 'part_time' | 'contract' | 'internship' | 'temporary';
export type WorkMode = 'remote' | 'hybrid' | 'onsite';

export interface JobCreateRequest {
  title: string;
  description: string;
  responsibilities?: string;
  requirements?: string;
  preferred_skills?: string;
  department?: string;
  employment_type: string;
  work_mode: string;
  location?: string;
  experience_min?: number;
  experience_max?: number;
  salary_min?: number;
  salary_max?: number;
  openings: number;
  deadline?: string;
  hiring_manager_id?: string;
}

// ───────────────── Applications ─────────────────

export interface Application {
  id: string;
  job_id: string;
  candidate_id: string;
  resume_id: string | null;
  status: ApplicationStatus;
  cover_letter: string | null;
  applied_at: string;
  updated_at: string;
  job_title?: string;
  candidate_name?: string;
}

export type ApplicationStatus =
  | 'applied'
  | 'under_review'
  | 'shortlisted'
  | 'interview_scheduled'
  | 'interview_completed'
  | 'offered'
  | 'hired'
  | 'rejected'
  | 'withdrawn'
  | 'on_hold';

export interface StatusHistory {
  id: string;
  previous_status: string | null;
  new_status: string;
  changed_by: string | null;
  changed_by_name: string | null;
  reason: string | null;
  created_at: string;
}

export interface CandidateApplicationStatus {
  id: string;
  job_title: string;
  status: string;
  status_display: string;
  applied_at: string;
  updated_at: string;
}

// ───────────────── Candidates ─────────────────

export interface CandidateProfile {
  id: string;
  user_id: string;
  name?: string;
  email?: string;
  phone: string | null;
  location: string | null;
  skills: string[] | null;
  experience_years: number | null;
  education: Education[] | null;
  portfolio_url: string | null;
  github_url: string | null;
  linkedin_url: string | null;
  summary: string | null;
  created_at: string;
  updated_at: string;
}

export interface Education {
  degree: string;
  university: string;
  year: number;
}

export interface CandidateSearch {
  id: string;
  user_id: string;
  name: string;
  email: string;
  phone: string | null;
  location: string | null;
  skills: string[] | null;
  experience_years: number | null;
  created_at: string;
}

// ───────────────── Interviews ─────────────────

export interface Interview {
  id: string;
  application_id: string;
  interview_round: number;
  interview_type: string;
  start_time: string;
  end_time: string;
  timezone: string;
  meeting_location: string | null;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
  interviewers: InterviewerInfo[] | null;
  candidate_name: string | null;
  job_title: string | null;
}

export interface InterviewerInfo {
  user_id: string;
  name: string;
  role: string;
}

export interface InterviewFeedback {
  id: string;
  interview_id: string;
  interviewer_id: string;
  interviewer_name: string | null;
  criterion_scores: Record<string, number> | null;
  strengths: string | null;
  concerns: string | null;
  recommendation: string | null;
  overall_notes: string | null;
  submitted_at: string;
}

// ───────────────── Offers ─────────────────

export interface Offer {
  id: string;
  application_id: string;
  compensation_details: Record<string, any> | null;
  status: string;
  issued_by: string | null;
  approved_by: string | null;
  notes: string | null;
  issued_at: string | null;
  expires_at: string | null;
  candidate_response_at: string | null;
  created_at: string;
  updated_at: string;
  candidate_name: string | null;
  job_title: string | null;
}

// ───────────────── Resume ─────────────────

export interface Resume {
  id: string;
  candidate_id: string;
  original_filename: string;
  content_type: string;
  file_size: number;
  is_active: boolean;
  created_at: string;
}

// ───────────────── Dashboard ─────────────────

export interface DashboardOverview {
  total_open_jobs: number;
  total_applications: number;
  applications_awaiting_review: number;
  interviews_scheduled: number;
  offers_pending: number;
  candidates_hired: number;
}

export interface RecruitmentFunnel {
  stage: string;
  count: number;
}

export interface ActivityItem {
  action: string;
  resource_type: string;
  actor_name: string | null;
  created_at: string;
}

// ───────────────── Paginated Responses ─────────────────

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  [key: string]: T[] | number;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApplicationListResponse {
  applications: Application[];
  total: number;
  page: number;
  page_size: number;
}

export interface CandidateListResponse {
  candidates: CandidateSearch[];
  total: number;
  page: number;
  page_size: number;
}

export interface InterviewListResponse {
  interviews: Interview[];
  total: number;
  page: number;
  page_size: number;
}

export interface OfferListResponse {
  offers: Offer[];
  total: number;
  page: number;
  page_size: number;
}

export interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  page_size: number;
}
