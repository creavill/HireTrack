import React from 'react';
import { useNavigate } from 'react-router-dom';
import { MapPin, Clock, ChevronRight, Mail, FileText } from 'lucide-react';

// Generate a consistent color from company name hash
function getCompanyColor(company) {
  if (!company) return '#5A5A72'; // slate default
  const colors = ['#C45D30', '#5B8C6B', '#A0522D', '#5A5A72', '#E8C47C']; // copper, patina, rust, slate, cream
  let hash = 0;
  for (let i = 0; i < company.length; i++) {
    hash = company.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

// Get company initials (1-2 characters)
function getCompanyInitials(company) {
  if (!company) return '?';
  const words = company.trim().split(/\s+/);
  if (words.length === 1) {
    return words[0].substring(0, 2).toUpperCase();
  }
  return (words[0][0] + words[1][0]).toUpperCase();
}

// Format relative date (e.g., "2d ago", "3h ago")
function formatRelativeDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 60) return `${diffMins}m`;
  if (diffHours < 24) return `${diffHours}h`;
  if (diffDays < 30) return `${diffDays}d`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

const STATUS_CONFIG = {
  new: { label: 'New', borderColor: 'border-l-slate', bgColor: 'bg-slate/10', textColor: 'text-slate' },
  interested: { label: 'Interested', borderColor: 'border-l-copper', bgColor: 'bg-copper/10', textColor: 'text-copper' },
  applied: { label: 'Applied', borderColor: 'border-l-patina', bgColor: 'bg-patina/10', textColor: 'text-patina' },
  interviewing: { label: 'Interviewing', borderColor: 'border-l-cream', bgColor: 'bg-cream/20', textColor: 'text-ink' },
  rejected: { label: 'Rejected', borderColor: 'border-l-rust', bgColor: 'bg-rust/10', textColor: 'text-rust' },
  offer: { label: 'Offer', borderColor: 'border-l-copper', bgColor: 'bg-copper/20', textColor: 'text-copper' },
  passed: { label: 'Passed', borderColor: 'border-l-slate', bgColor: 'bg-slate/10', textColor: 'text-slate' },
};

export default function JobRow({ job, isSelected }) {
  const navigate = useNavigate();
  const config = STATUS_CONFIG[job.status] || STATUS_CONFIG.new;

  // Score styling based on value
  let scoreBorderColor = 'border-b-rust';
  if (job.score >= 80) scoreBorderColor = 'border-b-patina';
  else if (job.score >= 60) scoreBorderColor = 'border-b-cream';

  // Unread indicator - show if viewed is falsy (0, false, null, undefined)
  const isUnread = !job.viewed;

  // Activity count from followup emails
  const followupCount = job.followup_count || 0;

  // Check if job has description details
  const hasDescription = job.job_description || job.full_description;

  const handleClick = () => {
    navigate(`/jobs/${job.job_id}`);
  };

  return (
    <div
      onClick={handleClick}
      className={`
        group flex items-center gap-3 px-4 py-3
        bg-parchment border-l-[3px] ${config.borderColor}
        border-b border-warm-gray
        cursor-pointer transition-all duration-150
        hover:bg-warm-gray/50 hover:pl-5
        ${isSelected ? 'bg-warm-gray/30 border-l-copper' : ''}
        ${isUnread ? 'bg-copper/5' : ''}
      `}
    >
      {/* Unread Indicator */}
      <div className="w-2 flex-shrink-0 flex items-center justify-center">
        {isUnread && (
          <div className="w-2 h-2 rounded-full bg-copper" title="Unread" />
        )}
      </div>

      {/* Company Logo/Initials */}
      <div
        className="w-10 h-10 flex-shrink-0 flex items-center justify-center relative"
        style={{ backgroundColor: getCompanyColor(job.company) }}
      >
        <span className="text-parchment font-body font-semibold text-sm">
          {getCompanyInitials(job.company)}
        </span>
        {/* Activity Badge */}
        {followupCount > 0 && (
          <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-patina flex items-center justify-center">
            <Mail size={10} className="text-parchment" />
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 min-w-0">
        {/* Title Row */}
        <div className="flex items-center gap-2">
          <h3 className="font-body font-semibold text-ink truncate text-sm">
            {job.title}
          </h3>
          {hasDescription && (
            <FileText size={12} className="flex-shrink-0 text-patina" title="Has job description" />
          )}
        </div>

        {/* Company & Location Row */}
        <div className="flex items-center gap-3 text-xs text-slate mt-0.5">
          <span className="truncate">{job.company || 'Unknown Company'}</span>
          {job.location && (
            <>
              <span className="text-warm-gray">|</span>
              <span className="flex items-center gap-1 truncate">
                <MapPin size={10} />
                {job.location}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Score */}
      <div className="flex-shrink-0 w-10 text-center">
        <span className={`font-mono font-bold text-sm text-ink border-b-2 ${scoreBorderColor} px-1`}>
          {job.score || '—'}
        </span>
      </div>

      {/* Status Tag */}
      <div className="flex-shrink-0 w-24">
        <span className={`
          inline-block px-2 py-0.5 text-xs font-body uppercase tracking-wide
          ${config.bgColor} ${config.textColor}
        `}>
          {config.label}
        </span>
      </div>

      {/* Date */}
      <div className="flex-shrink-0 w-12 text-right">
        <span className="flex items-center justify-end gap-1 text-xs text-slate">
          <Clock size={10} />
          {formatRelativeDate(job.email_date || job.created_at)}
        </span>
      </div>

      {/* Chevron indicator */}
      <ChevronRight
        size={16}
        className="flex-shrink-0 text-slate/50 group-hover:text-copper transition-colors"
      />
    </div>
  );
}
