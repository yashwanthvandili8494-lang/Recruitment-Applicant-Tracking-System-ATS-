/**
 * Status badge component with color coding for all application/job/interview statuses.
 */

const statusStyles: Record<string, string> = {
  // Application statuses
  applied: 'bg-blue-50 text-blue-700 ring-1 ring-blue-600/20',
  under_review: 'bg-amber-50 text-amber-700 ring-1 ring-amber-600/20',
  shortlisted: 'bg-indigo-50 text-indigo-700 ring-1 ring-indigo-600/20',
  interview_scheduled: 'bg-purple-50 text-purple-700 ring-1 ring-purple-600/20',
  interview_completed: 'bg-cyan-50 text-cyan-700 ring-1 ring-cyan-600/20',
  offered: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-600/20',
  hired: 'bg-green-50 text-green-700 ring-1 ring-green-600/20',
  rejected: 'bg-red-50 text-red-700 ring-1 ring-red-600/20',
  withdrawn: 'bg-gray-50 text-gray-700 ring-1 ring-gray-600/20',
  on_hold: 'bg-orange-50 text-orange-700 ring-1 ring-orange-600/20',

  // Job statuses
  draft: 'bg-slate-50 text-slate-700 ring-1 ring-slate-600/20',
  published: 'bg-green-50 text-green-700 ring-1 ring-green-600/20',
  paused: 'bg-yellow-50 text-yellow-700 ring-1 ring-yellow-600/20',
  closed: 'bg-red-50 text-red-700 ring-1 ring-red-600/20',
  archived: 'bg-gray-50 text-gray-500 ring-1 ring-gray-600/20',

  // Interview statuses
  scheduled: 'bg-blue-50 text-blue-700 ring-1 ring-blue-600/20',
  completed: 'bg-green-50 text-green-700 ring-1 ring-green-600/20',
  cancelled: 'bg-red-50 text-red-700 ring-1 ring-red-600/20',
  rescheduled: 'bg-amber-50 text-amber-700 ring-1 ring-amber-600/20',
  no_show: 'bg-gray-50 text-gray-700 ring-1 ring-gray-600/20',

  // Offer statuses
  pending_approval: 'bg-amber-50 text-amber-700 ring-1 ring-amber-600/20',
  sent: 'bg-blue-50 text-blue-700 ring-1 ring-blue-600/20',
  accepted: 'bg-green-50 text-green-700 ring-1 ring-green-600/20',
  declined: 'bg-red-50 text-red-700 ring-1 ring-red-600/20',
  expired: 'bg-gray-50 text-gray-500 ring-1 ring-gray-600/20',

  // Recommendation
  strong_yes: 'bg-green-50 text-green-700 ring-1 ring-green-600/20',
  yes: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-600/20',
  maybe: 'bg-yellow-50 text-yellow-700 ring-1 ring-yellow-600/20',
  no: 'bg-orange-50 text-orange-700 ring-1 ring-orange-600/20',
  strong_no: 'bg-red-50 text-red-700 ring-1 ring-red-600/20',
};

const statusLabels: Record<string, string> = {
  applied: 'Applied',
  under_review: 'Under Review',
  shortlisted: 'Shortlisted',
  interview_scheduled: 'Interview Scheduled',
  interview_completed: 'Interview Done',
  offered: 'Offered',
  hired: 'Hired',
  rejected: 'Rejected',
  withdrawn: 'Withdrawn',
  on_hold: 'On Hold',
  draft: 'Draft',
  published: 'Published',
  paused: 'Paused',
  closed: 'Closed',
  archived: 'Archived',
  scheduled: 'Scheduled',
  completed: 'Completed',
  cancelled: 'Cancelled',
  rescheduled: 'Rescheduled',
  no_show: 'No Show',
  pending_approval: 'Pending Approval',
  sent: 'Sent',
  accepted: 'Accepted',
  declined: 'Declined',
  expired: 'Expired',
  strong_yes: 'Strong Yes',
  yes: 'Yes',
  maybe: 'Maybe',
  no: 'No',
  strong_no: 'Strong No',
  full_time: 'Full Time',
  part_time: 'Part Time',
  contract: 'Contract',
  internship: 'Internship',
  temporary: 'Temporary',
  remote: 'Remote',
  hybrid: 'Hybrid',
  onsite: 'On-site',
};

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

export default function StatusBadge({ status, size = 'sm' }: StatusBadgeProps) {
  const style = statusStyles[status] || 'bg-gray-50 text-gray-600 ring-1 ring-gray-600/20';
  const label = statusLabels[status] || status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <span
      className={`status-badge ${style} ${
        size === 'sm' ? 'text-xs px-2.5 py-0.5' : 'text-sm px-3 py-1'
      }`}
    >
      {label}
    </span>
  );
}

export { statusLabels };
