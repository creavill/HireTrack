import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  ExternalLink,
  FileText,
  Trash2,
  Loader2,
  MapPin,
  Clock,
  ChevronDown,
  CheckCircle,
  XCircle,
  Star,
  Briefcase,
  Mail,
  Calendar,
  Edit2,
  Save,
  DollarSign,
  Search,
  Building2,
  AlertTriangle,
  Users,
  Archive,
  Copy,
  TrendingUp,
  AlertCircle,
  Award
} from 'lucide-react';

const API_BASE = '/api';

const STATUS_CONFIG = {
  new: { label: 'New', borderColor: 'border-l-slate', bgColor: 'bg-slate/10', textColor: 'text-slate', icon: Clock },
  interested: { label: 'Interested', borderColor: 'border-l-copper', bgColor: 'bg-copper/10', textColor: 'text-copper', icon: Star },
  applied: { label: 'Applied', borderColor: 'border-l-patina', bgColor: 'bg-patina/10', textColor: 'text-patina', icon: CheckCircle },
  interviewing: { label: 'Interviewing', borderColor: 'border-l-cream', bgColor: 'bg-cream/20', textColor: 'text-ink', icon: Briefcase },
  rejected: { label: 'Rejected', borderColor: 'border-l-rust', bgColor: 'bg-rust/10', textColor: 'text-rust', icon: XCircle },
  offer: { label: 'Offer', borderColor: 'border-l-copper', bgColor: 'bg-copper/20', textColor: 'text-copper', icon: Star },
  passed: { label: 'Passed', borderColor: 'border-l-slate', bgColor: 'bg-slate/10', textColor: 'text-slate', icon: XCircle },
};

// Generate a consistent color from company name hash
function getCompanyColor(company) {
  if (!company) return '#5A5A72';
  const colors = ['#C45D30', '#5B8C6B', '#A0522D', '#5A5A72', '#E8C47C'];
  let hash = 0;
  for (let i = 0; i < company.length; i++) {
    hash = company.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

function getCompanyInitials(company) {
  if (!company) return '?';
  const words = company.trim().split(/\s+/);
  if (words.length === 1) {
    return words[0].substring(0, 2).toUpperCase();
  }
  return (words[0][0] + words[1][0]).toUpperCase();
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
}

function StatusDropdown({ status, onChange }) {
  const [isOpen, setIsOpen] = useState(false);
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.new;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`
          w-full flex items-center justify-between gap-2 px-4 py-3
          border-l-[3px] ${config.borderColor} ${config.bgColor}
          font-body uppercase tracking-wide text-sm
          hover:bg-warm-gray/50 transition-colors
        `}
      >
        <span className={config.textColor}>{config.label}</span>
        <ChevronDown size={16} className={`text-slate transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-parchment border border-warm-gray shadow-lg z-10">
          {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
            <button
              key={key}
              onClick={() => { onChange(key); setIsOpen(false); }}
              className={`
                w-full text-left px-4 py-2 flex items-center gap-2
                border-l-[3px] ${cfg.borderColor}
                ${cfg.textColor} hover:bg-warm-gray/50
                font-body uppercase tracking-wide text-xs
                ${key === status ? 'bg-warm-gray/30' : ''}
              `}
            >
              {cfg.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function ActivityTimeline({ activities, loading }) {
  const [expandedId, setExpandedId] = useState(null);
  const [fullEmails, setFullEmails] = useState({});
  const [loadingEmail, setLoadingEmail] = useState(null);

  const handleExpandEmail = async (activity) => {
    if (expandedId === activity.id) {
      setExpandedId(null);
      return;
    }

    setExpandedId(activity.id);

    // If we already have the full body in the activity or cached, use it
    if (activity.full_body || fullEmails[activity.id]) {
      return;
    }

    // Fetch full email from API
    if (activity.id && activity.gmail_message_id) {
      setLoadingEmail(activity.id);
      try {
        const res = await fetch(`/api/followups/${activity.id}/full-email`);
        const data = await res.json();
        if (data.full_body) {
          setFullEmails(prev => ({ ...prev, [activity.id]: data.full_body }));
        }
      } catch (err) {
        console.error('Failed to fetch full email:', err);
      } finally {
        setLoadingEmail(null);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-10">
        <Loader2 size={24} className="animate-spin text-copper" />
      </div>
    );
  }

  if (!activities || activities.length === 0) {
    return (
      <div className="text-center py-8 text-slate text-sm font-body">
        <Mail size={24} className="mx-auto mb-2 opacity-50" />
        No email activity yet
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {activities.map((activity, index) => {
        const isExpanded = expandedId === activity.id;
        const fullBody = activity.full_body || fullEmails[activity.id];
        const canExpand = activity.id && (activity.gmail_message_id || activity.full_body || fullEmails[activity.id]);

        return (
          <div
            key={activity.id || index}
            className={`bg-warm-gray/20 border-l-4 rounded-r-sm ${
              activity.classification === 'interview' ? 'border-l-patina' :
              activity.classification === 'offer' ? 'border-l-copper' :
              activity.classification === 'rejection' ? 'border-l-rust' :
              'border-l-slate'
            }`}
          >
            <div
              className={`flex gap-3 p-4 ${canExpand ? 'cursor-pointer hover:bg-warm-gray/40 transition-colors' : ''}`}
              onClick={() => canExpand && handleExpandEmail(activity)}
            >
              <Mail size={16} className="text-slate flex-shrink-0 mt-1" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-ink font-body font-medium leading-snug">{activity.subject}</p>
                <div className="flex items-center gap-2 mt-2 flex-wrap">
                  <p className="text-xs text-slate">{formatDate(activity.date)}</p>
                  {activity.sender_email && (
                    <p className="text-xs text-slate truncate">from {activity.sender_email}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {activity.classification && (
                  <span className={`
                    text-xs px-2 py-1 rounded-sm font-medium
                    ${activity.classification === 'interview' ? 'bg-patina/15 text-patina' :
                      activity.classification === 'offer' ? 'bg-copper/15 text-copper' :
                      activity.classification === 'rejection' ? 'bg-rust/15 text-rust' :
                      'bg-slate/15 text-slate'}
                  `}>
                    {activity.classification}
                  </span>
                )}
                {canExpand && (
                  <ChevronDown
                    size={18}
                    className={`text-slate transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
                  />
                )}
              </div>
            </div>

            {/* Expanded email content */}
            {isExpanded && (
              <div className="px-4 pb-4">
                <div className="bg-parchment border border-warm-gray p-5 rounded-sm">
                  {loadingEmail === activity.id ? (
                    <div className="flex items-center justify-center py-6">
                      <Loader2 size={20} className="animate-spin text-copper" />
                      <span className="ml-2 text-sm text-slate">Loading email...</span>
                    </div>
                  ) : fullBody ? (
                    <div className="text-sm text-ink whitespace-pre-wrap font-body leading-relaxed">
                      {fullBody}
                    </div>
                  ) : activity.snippet ? (
                    <div>
                      <div className="text-sm text-ink whitespace-pre-wrap font-body leading-relaxed">
                        {activity.snippet}
                      </div>
                      <p className="text-xs text-slate mt-4 italic border-t border-warm-gray pt-3">
                        Full email not available. Showing preview only.
                      </p>
                    </div>
                  ) : (
                    <p className="text-sm text-slate italic text-center py-4">No email content available</p>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function JobDetailPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activities, setActivities] = useState([]);
  const [activitiesLoading, setActivitiesLoading] = useState(true);
  const [notes, setNotes] = useState('');
  const [notesSaving, setNotesSaving] = useState(false);
  const [coverLetterGenerating, setCoverLetterGenerating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [enriching, setEnriching] = useState(false);
  const [enrichment, setEnrichment] = useState(null);
  const [findingHM, setFindingHM] = useState(false);
  const [hiringManagerInfo, setHiringManagerInfo] = useState(null);
  const [archiving, setArchiving] = useState(false);

  const fetchJob = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/jobs/${jobId}`);
      if (res.ok) {
        const data = await res.json();
        setJob(data.job || data);
        setNotes(data.job?.notes || data.notes || '');
      } else {
        console.error('Job not found');
      }
    } catch (err) {
      console.error('Failed to fetch job:', err);
    }
    setLoading(false);
  }, [jobId]);

  const fetchActivities = useCallback(async () => {
    setActivitiesLoading(true);
    try {
      const res = await fetch(`${API_BASE}/jobs/${jobId}/activity`);
      if (res.ok) {
        const data = await res.json();
        setActivities(data.activities || []);
      }
    } catch (err) {
      console.error('Failed to fetch activities:', err);
    }
    setActivitiesLoading(false);
  }, [jobId]);

  const fetchEnrichment = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/jobs/${jobId}/enrichment`);
      if (res.ok) {
        const data = await res.json();
        setEnrichment(data);
      }
    } catch (err) {
      console.error('Failed to fetch enrichment:', err);
    }
  }, [jobId]);

  const handleEnrich = async () => {
    setEnriching(true);
    try {
      const res = await fetch(`${API_BASE}/jobs/${jobId}/enrich`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force: false })
      });
      if (res.ok) {
        // Refresh job and enrichment data
        await fetchJob();
        await fetchEnrichment();
      }
    } catch (err) {
      console.error('Enrichment failed:', err);
    }
    setEnriching(false);
  };

  useEffect(() => {
    fetchJob();
    fetchActivities();
    fetchEnrichment();
  }, [fetchJob, fetchActivities, fetchEnrichment]);

  const handleStatusChange = async (newStatus) => {
    try {
      await fetch(`${API_BASE}/jobs/${jobId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      setJob(prev => ({ ...prev, status: newStatus }));
    } catch (err) {
      console.error('Status update failed:', err);
    }
  };

  const handleNotesSave = async () => {
    if (notes === job.notes) return;
    setNotesSaving(true);
    try {
      await fetch(`${API_BASE}/jobs/${jobId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes }),
      });
      setJob(prev => ({ ...prev, notes }));
    } catch (err) {
      console.error('Notes save failed:', err);
    }
    setNotesSaving(false);
  };

  const handleGenerateCoverLetter = async () => {
    setCoverLetterGenerating(true);
    try {
      await fetch(`${API_BASE}/jobs/${jobId}/cover-letter`, { method: 'POST' });
      // Refresh job to get the generated cover letter
      setTimeout(fetchJob, 3000);
      setTimeout(fetchJob, 8000);
    } catch (err) {
      console.error('Cover letter generation failed:', err);
    }
    setCoverLetterGenerating(false);
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this job?')) return;
    setDeleting(true);
    try {
      await fetch(`${API_BASE}/jobs/${jobId}`, { method: 'DELETE' });
      navigate('/');
    } catch (err) {
      console.error('Delete failed:', err);
      setDeleting(false);
    }
  };

  const handleArchive = async () => {
    setArchiving(true);
    try {
      await fetch(`${API_BASE}/jobs/${jobId}/archive`, { method: 'POST' });
      navigate('/');
    } catch (err) {
      console.error('Archive failed:', err);
      setArchiving(false);
    }
  };

  const handleFindHiringManager = async () => {
    setFindingHM(true);
    try {
      const res = await fetch(`${API_BASE}/jobs/${jobId}/find-hiring-manager`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setHiringManagerInfo(data.suggestions);
      }
    } catch (err) {
      console.error('Find hiring manager failed:', err);
    } finally {
      setFindingHM(false);
    }
  };

  const handleCopyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 size={32} className="animate-spin text-copper" />
      </div>
    );
  }

  if (!job) {
    return (
      <div>
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-slate hover:text-copper transition-colors mb-4"
        >
          <ArrowLeft size={20} />
          <span className="font-body">Back to Jobs</span>
        </button>
        <div className="text-center py-12">
          <p className="text-slate font-body">Job not found.</p>
        </div>
      </div>
    );
  }

  const analysis = job.analysis || {};
  const scoreBorderColor = job.score >= 80 ? 'border-b-patina' :
                           job.score >= 60 ? 'border-b-cream' : 'border-b-rust';

  return (
    <div className="max-w-7xl mx-auto">
      {/* Back button */}
      <button
        onClick={() => navigate('/')}
        className="flex items-center gap-2 text-slate hover:text-copper transition-colors mb-8"
      >
        <ArrowLeft size={20} />
        <span className="font-body uppercase tracking-wide text-sm">Back to Jobs</span>
      </button>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column - Job Info (2/3 width on large screens) */}
        <div className="lg:col-span-2 space-y-8">
          {/* Job Header Card */}
          <div className="bg-parchment border border-warm-gray rounded-sm shadow-sm">
            <div className="p-8">
              <div className="flex items-start gap-6">
                {/* Company Logo */}
                {job.logo_url ? (
                  <img
                    src={job.logo_url}
                    alt={job.company}
                    className="w-20 h-20 flex-shrink-0 object-contain bg-white border border-warm-gray rounded-sm"
                    onError={(e) => {
                      e.target.onerror = null;
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'flex';
                    }}
                  />
                ) : null}
                <div
                  className="w-20 h-20 flex-shrink-0 flex items-center justify-center rounded-sm"
                  style={{
                    backgroundColor: getCompanyColor(job.company),
                    display: job.logo_url ? 'none' : 'flex'
                  }}
                >
                  <span className="text-parchment font-body font-semibold text-2xl">
                    {getCompanyInitials(job.company)}
                  </span>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-start gap-3 mb-2">
                    <h1 className="font-display text-3xl text-ink leading-tight">{job.title}</h1>
                    {job.is_aggregator && (
                      <span className="px-2 py-1 bg-cream/20 text-cream text-xs font-semibold uppercase tracking-wide flex items-center gap-1 flex-shrink-0 mt-1">
                        <AlertTriangle size={12} />
                        Staffing
                      </span>
                    )}
                  </div>
                  <p className="text-xl text-slate font-body mb-3">{job.company || 'Unknown Company'}</p>
                  <div className="flex items-center gap-4 flex-wrap">
                    {job.location && (
                      <span className="flex items-center gap-1.5 text-sm text-slate bg-warm-gray/30 px-3 py-1.5 rounded-sm">
                        <MapPin size={14} />
                        {job.location}
                      </span>
                    )}
                    {(enrichment?.salary_estimate || job.salary_estimate) && (
                      <span className="flex items-center gap-1.5 text-sm text-patina font-semibold bg-patina/10 px-3 py-1.5 rounded-sm">
                        <DollarSign size={14} />
                        {enrichment?.salary_estimate || job.salary_estimate}
                      </span>
                    )}
                  </div>
                </div>

                {/* Score */}
                <div className="flex-shrink-0 text-center bg-warm-gray/20 px-6 py-4 rounded-sm">
                  <div className={`font-mono font-bold text-4xl text-ink border-b-4 ${scoreBorderColor} pb-2`}>
                    {job.score || '—'}
                  </div>
                  <p className="text-xs text-slate mt-2 uppercase tracking-wide font-semibold">Match Score</p>
                </div>
              </div>
            </div>

            {/* Quick Info Row */}
            <div className="flex items-center gap-6 px-8 py-4 border-t border-warm-gray bg-warm-gray/10 text-sm text-slate">
              <span className="flex items-center gap-1.5">
                <Calendar size={14} />
                Added {formatDate(job.created_at)}
              </span>
              {job.email_date && (
                <span className="flex items-center gap-1.5">
                  <Mail size={14} />
                  Posted {formatDate(job.email_date)}
                </span>
              )}
              {enrichment?.is_enriched && (
                <span className="flex items-center gap-1.5 text-patina font-medium">
                  <CheckCircle size={14} />
                  Enriched
                </span>
              )}
            </div>
          </div>

          {/* AI Analysis */}
          {(analysis.recommendation || analysis.strengths?.length > 0 || analysis.gaps?.length > 0) && (
            <div className="bg-parchment border border-warm-gray rounded-sm shadow-sm">
              <div className="px-8 py-5 border-b border-warm-gray bg-warm-gray/10">
                <h2 className="font-display text-xl text-ink">AI Analysis</h2>
              </div>
              <div className="p-8">
                {analysis.recommendation && (
                  <div className="bg-copper/5 border-l-4 border-l-copper p-5 mb-6 rounded-r-sm">
                    <p className="text-ink font-body text-base leading-relaxed">
                      {analysis.recommendation}
                    </p>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  {analysis.strengths?.length > 0 && (
                    <div className="bg-patina/5 p-5 rounded-sm">
                      <h3 className="text-sm font-body font-semibold text-patina uppercase tracking-wide mb-4 flex items-center gap-2">
                        <CheckCircle size={16} />
                        Strengths
                      </h3>
                      <ul className="space-y-3">
                        {analysis.strengths.map((s, i) => (
                          <li key={i} className="text-sm text-ink font-body flex items-start gap-3 leading-relaxed">
                            <CheckCircle size={14} className="text-patina flex-shrink-0 mt-1" />
                            {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {analysis.gaps?.length > 0 && (
                    <div className="bg-rust/5 p-5 rounded-sm">
                      <h3 className="text-sm font-body font-semibold text-rust uppercase tracking-wide mb-4 flex items-center gap-2">
                        <XCircle size={16} />
                        Gaps
                      </h3>
                      <ul className="space-y-3">
                        {analysis.gaps.map((g, i) => (
                          <li key={i} className="text-sm text-ink font-body flex items-start gap-3 leading-relaxed">
                            <XCircle size={14} className="text-rust flex-shrink-0 mt-1" />
                            {g}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {analysis.resume_to_use && (
                  <div className="mt-6 pt-6 border-t border-warm-gray">
                    <p className="text-sm text-slate flex items-center gap-2">
                      <FileText size={14} />
                      Recommended resume: <span className="text-ink font-semibold">{analysis.resume_to_use}</span>
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Experience Requirements */}
          {job.experience_requirements && (() => {
            try {
              const requirements = typeof job.experience_requirements === 'string'
                ? JSON.parse(job.experience_requirements)
                : job.experience_requirements;
              if (requirements && requirements.length > 0) {
                return (
                  <div className="bg-parchment border border-warm-gray rounded-sm shadow-sm">
                    <div className="px-8 py-5 border-b border-warm-gray bg-warm-gray/10">
                      <h2 className="font-display text-xl text-ink flex items-center gap-2">
                        <Clock size={18} className="text-copper" />
                        Experience Requirements
                      </h2>
                    </div>
                    <div className="p-8">
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {requirements.map((req, i) => (
                          <div
                            key={i}
                            className="p-4 bg-warm-gray/20 border-l-4 border-l-copper rounded-r-sm"
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-semibold text-ink text-sm">{req.skill}</span>
                              <span className="text-copper font-mono font-bold">
                                {req.years_min}{req.years_max ? `-${req.years_max}` : '+'} yrs
                              </span>
                            </div>
                            {req.raw_text && (
                              <p className="text-xs text-slate italic mt-1 leading-snug">
                                "{req.raw_text.substring(0, 60)}..."
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              }
            } catch (e) {
              console.error('Failed to parse experience_requirements:', e);
            }
            return null;
          })()}

          {/* Fit Analysis - Pros & Gaps */}
          {(job.fit_pros || job.fit_gaps) && (() => {
            try {
              const pros = job.fit_pros
                ? (typeof job.fit_pros === 'string' ? JSON.parse(job.fit_pros) : job.fit_pros)
                : [];
              const gaps = job.fit_gaps
                ? (typeof job.fit_gaps === 'string' ? JSON.parse(job.fit_gaps) : job.fit_gaps)
                : [];

              if (pros.length > 0 || gaps.length > 0) {
                return (
                  <div className="bg-parchment border border-warm-gray rounded-sm shadow-sm">
                    <div className="px-8 py-5 border-b border-warm-gray bg-warm-gray/10 flex items-center justify-between">
                      <h2 className="font-display text-xl text-ink flex items-center gap-2">
                        <TrendingUp size={18} className="text-patina" />
                        Fit Analysis
                      </h2>
                      {job.fit_score && (
                        <span className={`px-3 py-1 rounded-sm font-mono font-bold text-sm ${
                          job.fit_score >= 70 ? 'bg-patina/20 text-patina' :
                          job.fit_score >= 50 ? 'bg-cream/20 text-cream' :
                          'bg-rust/20 text-rust'
                        }`}>
                          {job.fit_score}% Match
                        </span>
                      )}
                    </div>
                    <div className="p-8">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Pros - Your Strengths */}
                        {pros.length > 0 && (
                          <div className="bg-patina/5 p-5 rounded-sm">
                            <h3 className="text-sm font-body font-semibold text-patina uppercase tracking-wide mb-4 flex items-center gap-2">
                              <Award size={16} />
                              Your Strengths
                            </h3>
                            <div className="space-y-4">
                              {pros.map((pro, i) => (
                                <div key={i} className="border-l-2 border-patina pl-3">
                                  <p className="font-semibold text-ink text-sm">{pro.title}</p>
                                  <p className="text-sm text-slate mt-1">{pro.description}</p>
                                  {pro.skills && pro.skills.length > 0 && (
                                    <div className="flex flex-wrap gap-1 mt-2">
                                      {pro.skills.slice(0, 5).map((skill, j) => (
                                        <span key={j} className="px-2 py-0.5 bg-patina/20 text-patina text-xs rounded-sm">
                                          {skill}
                                        </span>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Gaps - Areas to Address */}
                        {gaps.length > 0 && (
                          <div className="bg-rust/5 p-5 rounded-sm">
                            <h3 className="text-sm font-body font-semibold text-rust uppercase tracking-wide mb-4 flex items-center gap-2">
                              <AlertCircle size={16} />
                              Areas to Address
                            </h3>
                            <div className="space-y-4">
                              {gaps.map((gap, i) => (
                                <div key={i} className={`border-l-2 pl-3 ${
                                  gap.severity === 'high' ? 'border-rust' :
                                  gap.severity === 'medium' ? 'border-cream' : 'border-slate'
                                }`}>
                                  <div className="flex items-center gap-2">
                                    <p className="font-semibold text-ink text-sm">{gap.title}</p>
                                    {gap.severity && (
                                      <span className={`text-[10px] px-1.5 py-0.5 rounded-sm uppercase ${
                                        gap.severity === 'high' ? 'bg-rust/20 text-rust' :
                                        gap.severity === 'medium' ? 'bg-cream/20 text-cream' :
                                        'bg-slate/20 text-slate'
                                      }`}>
                                        {gap.severity}
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-sm text-slate mt-1">{gap.description}</p>
                                  {gap.years_required && (
                                    <p className="text-xs text-rust mt-1">
                                      Requires {gap.years_required}+ years experience
                                    </p>
                                  )}
                                  {gap.skills && gap.skills.length > 0 && (
                                    <div className="flex flex-wrap gap-1 mt-2">
                                      {gap.skills.slice(0, 5).map((skill, j) => (
                                        <span key={j} className="px-2 py-0.5 bg-rust/20 text-rust text-xs rounded-sm">
                                          {skill}
                                        </span>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              }
            } catch (e) {
              console.error('Failed to parse fit analysis:', e);
            }
            return null;
          })()}

          {/* Enrichment Data */}
          {enrichment?.is_enriched && (
            <div className="bg-parchment border border-warm-gray rounded-sm shadow-sm">
              <div className="px-8 py-5 border-b border-warm-gray bg-warm-gray/10 flex items-center justify-between">
                <h2 className="font-display text-xl text-ink flex items-center gap-2">
                  <Search size={18} className="text-patina" />
                  Enriched Data
                </h2>
                <span className="text-xs text-slate bg-warm-gray/50 px-2 py-1 rounded-sm">
                  Last enriched: {formatDate(enrichment.last_enriched)}
                </span>
              </div>
              <div className="p-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {enrichment.salary_estimate && (
                    <div className="p-5 bg-patina/10 border-l-4 border-l-patina rounded-r-sm">
                      <span className="text-xs text-patina uppercase tracking-wide font-semibold flex items-center gap-1">
                        <DollarSign size={12} />
                        Salary Range
                      </span>
                      <p className="text-2xl font-semibold text-ink mt-2">{enrichment.salary_estimate}</p>
                      {enrichment.salary_confidence && (
                        <span className={`text-xs mt-1 inline-block ${
                          enrichment.salary_confidence === 'high' ? 'text-patina' :
                          enrichment.salary_confidence === 'medium' ? 'text-cream' : 'text-slate'
                        }`}>
                          {enrichment.salary_confidence} confidence
                        </span>
                      )}
                    </div>
                  )}

                  {enrichment.enrichment_source && (
                    <div className="p-5 bg-warm-gray/30 border-l-4 border-l-copper rounded-r-sm">
                      <span className="text-xs text-slate uppercase tracking-wide font-semibold">Source</span>
                      <a
                        href={enrichment.enrichment_source}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-base text-copper hover:underline flex items-center gap-2 mt-2 font-medium"
                      >
                        <ExternalLink size={16} />
                        View Original Posting
                      </a>
                    </div>
                  )}
                </div>

                {enrichment.full_description && (
                  <div className="mt-6 pt-6 border-t border-warm-gray">
                    <h3 className="text-sm font-body font-semibold text-ink uppercase tracking-wide mb-3">
                      Full Description
                    </h3>
                    <p className="text-sm text-slate font-body leading-relaxed whitespace-pre-wrap">
                      {enrichment.full_description}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Job Description */}
          {job.job_description && (
            <div className="bg-parchment border border-warm-gray rounded-sm shadow-sm">
              <div className="px-8 py-5 border-b border-warm-gray bg-warm-gray/10">
                <h2 className="font-display text-xl text-ink flex items-center gap-2">
                  <Briefcase size={18} className="text-copper" />
                  Job Description
                </h2>
              </div>
              <div className="p-8">
                <div className="prose prose-slate max-w-none text-ink font-body text-base leading-7 whitespace-pre-wrap">
                  {job.job_description}
                </div>
              </div>
            </div>
          )}

          {/* Cover Letter */}
          {job.cover_letter && (
            <div className="bg-parchment border border-warm-gray rounded-sm shadow-sm">
              <div className="px-8 py-5 border-b border-warm-gray bg-warm-gray/10 flex items-center justify-between">
                <h2 className="font-display text-xl text-ink flex items-center gap-2">
                  <FileText size={18} className="text-copper" />
                  Cover Letter
                </h2>
                <button
                  onClick={() => handleCopyToClipboard(job.cover_letter)}
                  className="text-xs text-copper hover:text-copper/80 flex items-center gap-1 px-2 py-1 bg-copper/10 rounded-sm"
                >
                  <Copy size={12} /> Copy
                </button>
              </div>
              <div className="p-8">
                <div className="text-ink font-body text-base leading-7 whitespace-pre-wrap bg-warm-gray/20 p-6 border border-warm-gray rounded-sm">
                  {job.cover_letter}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Tracking & Timeline (1/3 width on large screens) */}
        <div className="space-y-6">
          {/* Status Card */}
          <div className="bg-parchment border border-warm-gray rounded-sm shadow-sm">
            <div className="px-5 py-4 border-b border-warm-gray bg-warm-gray/10">
              <h2 className="font-body font-semibold text-ink uppercase tracking-wide text-sm">Status</h2>
            </div>
            <StatusDropdown status={job.status} onChange={handleStatusChange} />
          </div>

          {/* Actions Card */}
          <div className="bg-parchment border border-warm-gray rounded-sm shadow-sm">
            <div className="px-5 py-4 border-b border-warm-gray bg-warm-gray/10">
              <h2 className="font-body font-semibold text-ink uppercase tracking-wide text-sm">Actions</h2>
            </div>
            <div className="p-5 space-y-3">
              {job.url && (
                <a
                  href={job.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-copper text-parchment font-body uppercase tracking-wide text-sm hover:bg-copper/90 transition-colors rounded-sm"
                >
                  <ExternalLink size={16} />
                  View Original
                </a>
              )}

              {!job.cover_letter && (
                <button
                  onClick={handleGenerateCoverLetter}
                  disabled={coverLetterGenerating}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-transparent border border-copper text-copper font-body uppercase tracking-wide text-sm hover:bg-copper/10 disabled:opacity-50 transition-colors rounded-sm"
                >
                  {coverLetterGenerating ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <FileText size={16} />
                      Generate Cover Letter
                    </>
                  )}
                </button>
              )}

              {!enrichment?.is_enriched && (
                <button
                  onClick={handleEnrich}
                  disabled={enriching}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-transparent border border-patina text-patina font-body uppercase tracking-wide text-sm hover:bg-patina/10 disabled:opacity-50 transition-colors rounded-sm"
                >
                  {enriching ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Enriching...
                    </>
                  ) : (
                    <>
                      <Search size={16} />
                      Enrich Job Data
                    </>
                  )}
                </button>
              )}

              <button
                onClick={handleFindHiringManager}
                disabled={findingHM}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-transparent border border-copper text-copper font-body uppercase tracking-wide text-sm hover:bg-copper/10 disabled:opacity-50 transition-colors rounded-sm"
              >
                {findingHM ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Finding...
                  </>
                ) : (
                  <>
                    <Users size={16} />
                    Find Hiring Manager
                  </>
                )}
              </button>

              <div className="pt-2 mt-2 border-t border-warm-gray space-y-3">
                <button
                  onClick={handleArchive}
                  disabled={archiving}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-transparent border border-slate text-slate font-body uppercase tracking-wide text-sm hover:bg-slate/10 disabled:opacity-50 transition-colors rounded-sm"
                >
                  {archiving ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Archiving...
                    </>
                  ) : (
                    <>
                      <Archive size={16} />
                      Archive Job
                    </>
                  )}
                </button>

                <button
                  onClick={handleDelete}
                  disabled={deleting}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-rust/10 text-rust font-body uppercase tracking-wide text-sm hover:bg-rust/20 disabled:opacity-50 transition-colors rounded-sm"
                >
                  {deleting ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Deleting...
                    </>
                  ) : (
                    <>
                      <Trash2 size={16} />
                      Delete Job
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Hiring Manager Info Card */}
          {hiringManagerInfo && (
            <div className="bg-parchment border border-warm-gray rounded-sm shadow-sm">
              <div className="px-5 py-4 border-b border-warm-gray bg-warm-gray/10 flex items-center justify-between">
                <h2 className="font-body font-semibold text-ink uppercase tracking-wide text-sm flex items-center gap-2">
                  <Users size={14} className="text-copper" />
                  Hiring Manager
                </h2>
                <button
                  onClick={() => setHiringManagerInfo(null)}
                  className="text-slate hover:text-ink transition-colors"
                >
                  <XCircle size={16} />
                </button>
              </div>
              <div className="p-5 space-y-5">
                {/* Likely Titles */}
                {hiringManagerInfo.likely_titles && (
                  <div>
                    <h3 className="text-xs font-semibold text-slate uppercase tracking-wide mb-3">Likely Job Titles</h3>
                    <div className="flex flex-wrap gap-2">
                      {hiringManagerInfo.likely_titles.map((title, i) => (
                        <span key={i} className="px-3 py-1.5 bg-warm-gray/50 text-ink text-sm rounded-sm">{title}</span>
                      ))}
                    </div>
                  </div>
                )}

                {/* LinkedIn Search */}
                {hiringManagerInfo.linkedin_search && (
                  <div>
                    <h3 className="text-xs font-semibold text-slate uppercase tracking-wide mb-3">LinkedIn Search</h3>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 px-3 py-2 bg-warm-gray/30 text-sm text-ink rounded-sm">{hiringManagerInfo.linkedin_search}</code>
                      <button
                        onClick={() => handleCopyToClipboard(hiringManagerInfo.linkedin_search)}
                        className="p-2 text-copper hover:text-copper/80 transition-colors"
                        title="Copy"
                      >
                        <Copy size={16} />
                      </button>
                      <a
                        href={`https://www.linkedin.com/search/results/people/?keywords=${encodeURIComponent(hiringManagerInfo.linkedin_search)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2 text-copper hover:text-copper/80 transition-colors"
                        title="Search on LinkedIn"
                      >
                        <ExternalLink size={16} />
                      </a>
                    </div>
                  </div>
                )}

                {/* Tips */}
                {hiringManagerInfo.tips && (
                  <div>
                    <h3 className="text-xs font-semibold text-slate uppercase tracking-wide mb-3">Tips</h3>
                    <ul className="space-y-2 text-sm text-ink">
                      {hiringManagerInfo.tips.map((tip, i) => (
                        <li key={i} className="flex items-start gap-2 leading-relaxed">
                          <span className="text-copper mt-0.5">•</span>
                          {tip}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Outreach Template */}
                {hiringManagerInfo.outreach_template && (
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-xs font-semibold text-slate uppercase tracking-wide">Outreach Template</h3>
                      <button
                        onClick={() => handleCopyToClipboard(hiringManagerInfo.outreach_template)}
                        className="text-xs text-copper hover:text-copper/80 flex items-center gap-1 px-2 py-1 bg-copper/10 rounded-sm"
                      >
                        <Copy size={12} /> Copy
                      </button>
                    </div>
                    <p className="px-4 py-3 bg-warm-gray/30 text-sm text-ink whitespace-pre-wrap leading-relaxed rounded-sm">{hiringManagerInfo.outreach_template}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Notes Card */}
          <div className="bg-parchment border border-warm-gray rounded-sm shadow-sm">
            <div className="px-5 py-4 border-b border-warm-gray bg-warm-gray/10 flex items-center justify-between">
              <h2 className="font-body font-semibold text-ink uppercase tracking-wide text-sm flex items-center gap-2">
                <Edit2 size={14} className="text-copper" />
                Notes
              </h2>
              {notesSaving && (
                <span className="text-xs text-patina flex items-center gap-1">
                  <Loader2 size={12} className="animate-spin" />
                  Saving...
                </span>
              )}
            </div>
            <div className="p-5">
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                onBlur={handleNotesSave}
                placeholder="Add notes, interview dates, key takeaways..."
                className="w-full px-4 py-3 text-sm border border-warm-gray bg-warm-gray/20 text-ink font-body placeholder-slate focus:border-copper focus:bg-parchment transition-colors resize-none outline-none min-h-[140px] rounded-sm leading-relaxed"
              />
            </div>
          </div>

          {/* Email Activity Timeline */}
          <div className="bg-parchment border border-warm-gray rounded-sm shadow-sm">
            <div className="px-5 py-4 border-b border-warm-gray bg-warm-gray/10">
              <h2 className="font-body font-semibold text-ink uppercase tracking-wide text-sm flex items-center gap-2">
                <Mail size={14} className="text-copper" />
                Email Activity
              </h2>
            </div>
            <div className="p-5">
              <ActivityTimeline activities={activities} loading={activitiesLoading} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
