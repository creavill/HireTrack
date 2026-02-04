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
  AlertTriangle
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
  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 size={20} className="animate-spin text-slate" />
      </div>
    );
  }

  if (!activities || activities.length === 0) {
    return (
      <div className="text-center py-6 text-slate text-sm font-body">
        No email activity yet
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {activities.map((activity, index) => (
        <div
          key={index}
          className="flex gap-3 p-3 bg-warm-gray/30 border-l-[3px] border-l-slate"
        >
          <Mail size={16} className="text-slate flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-sm text-ink font-body truncate">{activity.subject}</p>
            <p className="text-xs text-slate mt-1">{formatDate(activity.date)}</p>
          </div>
          {activity.classification && (
            <span className={`
              text-xs px-2 py-0.5 flex-shrink-0
              ${activity.classification === 'interview' ? 'bg-patina/10 text-patina' :
                activity.classification === 'offer' ? 'bg-copper/10 text-copper' :
                activity.classification === 'rejection' ? 'bg-rust/10 text-rust' :
                'bg-slate/10 text-slate'}
            `}>
              {activity.classification}
            </span>
          )}
        </div>
      ))}
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
    <div>
      {/* Back button */}
      <button
        onClick={() => navigate('/')}
        className="flex items-center gap-2 text-slate hover:text-copper transition-colors mb-6"
      >
        <ArrowLeft size={20} />
        <span className="font-body uppercase tracking-wide text-sm">Back to Jobs</span>
      </button>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Job Info (2/3 width on large screens) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Job Header Card */}
          <div className="bg-parchment border border-warm-gray p-6">
            <div className="flex items-start gap-4">
              {/* Company Logo */}
              {job.logo_url ? (
                <img
                  src={job.logo_url}
                  alt={job.company}
                  className="w-16 h-16 flex-shrink-0 object-contain bg-white border border-warm-gray"
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'flex';
                  }}
                />
              ) : null}
              <div
                className="w-16 h-16 flex-shrink-0 flex items-center justify-center"
                style={{
                  backgroundColor: getCompanyColor(job.company),
                  display: job.logo_url ? 'none' : 'flex'
                }}
              >
                <span className="text-parchment font-body font-semibold text-xl">
                  {getCompanyInitials(job.company)}
                </span>
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h1 className="font-display text-2xl text-ink">{job.title}</h1>
                  {job.is_aggregator && (
                    <span className="px-2 py-0.5 bg-cream/20 text-cream text-xs font-semibold uppercase tracking-wide flex items-center gap-1">
                      <AlertTriangle size={12} />
                      Staffing
                    </span>
                  )}
                </div>
                <p className="text-lg text-slate font-body">{job.company || 'Unknown Company'}</p>
                <div className="flex items-center gap-3 mt-1">
                  {job.location && (
                    <span className="flex items-center gap-1 text-sm text-slate">
                      <MapPin size={14} />
                      {job.location}
                    </span>
                  )}
                  {(enrichment?.salary_estimate || job.salary_estimate) && (
                    <span className="flex items-center gap-1 text-sm text-patina font-semibold">
                      <DollarSign size={14} />
                      {enrichment?.salary_estimate || job.salary_estimate}
                    </span>
                  )}
                </div>
              </div>

              {/* Score */}
              <div className="flex-shrink-0 text-center">
                <div className={`font-mono font-bold text-3xl text-ink border-b-4 ${scoreBorderColor} px-2 pb-1`}>
                  {job.score || '—'}
                </div>
                <p className="text-xs text-slate mt-1 uppercase tracking-wide">Match Score</p>
              </div>
            </div>

            {/* Quick Info Row */}
            <div className="flex items-center gap-4 mt-4 pt-4 border-t border-warm-gray text-sm text-slate">
              <span className="flex items-center gap-1">
                <Calendar size={14} />
                Added {formatDate(job.created_at)}
              </span>
              {job.email_date && (
                <span className="flex items-center gap-1">
                  <Mail size={14} />
                  Posted {formatDate(job.email_date)}
                </span>
              )}
              {enrichment?.is_enriched && (
                <span className="flex items-center gap-1 text-patina">
                  <CheckCircle size={14} />
                  Enriched
                </span>
              )}
            </div>
          </div>

          {/* AI Analysis */}
          {(analysis.recommendation || analysis.strengths?.length > 0 || analysis.gaps?.length > 0) && (
            <div className="bg-parchment border border-warm-gray p-6">
              <h2 className="font-display text-lg text-ink mb-4">AI Analysis</h2>

              {analysis.recommendation && (
                <p className="text-ink font-body mb-4 pb-4 border-b border-warm-gray">
                  {analysis.recommendation}
                </p>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {analysis.strengths?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-body font-semibold text-patina uppercase tracking-wide mb-2">
                      Strengths
                    </h3>
                    <ul className="space-y-2">
                      {analysis.strengths.map((s, i) => (
                        <li key={i} className="text-sm text-ink font-body flex items-start gap-2">
                          <CheckCircle size={14} className="text-patina flex-shrink-0 mt-0.5" />
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {analysis.gaps?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-body font-semibold text-rust uppercase tracking-wide mb-2">
                      Gaps
                    </h3>
                    <ul className="space-y-2">
                      {analysis.gaps.map((g, i) => (
                        <li key={i} className="text-sm text-ink font-body flex items-start gap-2">
                          <XCircle size={14} className="text-rust flex-shrink-0 mt-0.5" />
                          {g}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {analysis.resume_to_use && (
                <p className="text-sm text-slate mt-4 pt-4 border-t border-warm-gray">
                  Recommended resume: <span className="text-ink font-medium">{analysis.resume_to_use}</span>
                </p>
              )}
            </div>
          )}

          {/* Enrichment Data */}
          {enrichment?.is_enriched && (
            <div className="bg-parchment border border-warm-gray p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-display text-lg text-ink">Enriched Data</h2>
                <span className="text-xs text-slate">
                  Last enriched: {formatDate(enrichment.last_enriched)}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {enrichment.salary_estimate && (
                  <div className="p-3 bg-patina/10 border-l-[3px] border-l-patina">
                    <span className="text-xs text-patina uppercase tracking-wide font-semibold">Salary Range</span>
                    <p className="text-lg font-semibold text-ink mt-1">{enrichment.salary_estimate}</p>
                    {enrichment.salary_confidence && (
                      <span className={`text-xs ${
                        enrichment.salary_confidence === 'high' ? 'text-patina' :
                        enrichment.salary_confidence === 'medium' ? 'text-cream' : 'text-slate'
                      }`}>
                        {enrichment.salary_confidence} confidence
                      </span>
                    )}
                  </div>
                )}

                {enrichment.enrichment_source && (
                  <div className="p-3 bg-warm-gray/30 border-l-[3px] border-l-slate">
                    <span className="text-xs text-slate uppercase tracking-wide font-semibold">Source</span>
                    <a
                      href={enrichment.enrichment_source}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-copper hover:underline flex items-center gap-1 mt-1"
                    >
                      <ExternalLink size={12} />
                      View Original Posting
                    </a>
                  </div>
                )}
              </div>

              {enrichment.full_description && (
                <div className="mt-4 pt-4 border-t border-warm-gray">
                  <h3 className="text-sm font-body font-semibold text-ink uppercase tracking-wide mb-2">
                    Full Description (Preview)
                  </h3>
                  <p className="text-sm text-slate font-body line-clamp-4">
                    {enrichment.full_description}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Job Description */}
          {job.job_description && (
            <div className="bg-parchment border border-warm-gray p-6">
              <h2 className="font-display text-lg text-ink mb-4">Job Description</h2>
              <div className="prose prose-sm max-w-none text-ink font-body whitespace-pre-wrap">
                {job.job_description}
              </div>
            </div>
          )}

          {/* Cover Letter */}
          {job.cover_letter && (
            <div className="bg-parchment border border-warm-gray p-6">
              <h2 className="font-display text-lg text-ink mb-4">Cover Letter</h2>
              <pre className="text-sm text-ink font-body whitespace-pre-wrap bg-warm-gray/30 p-4 border border-warm-gray">
                {job.cover_letter}
              </pre>
            </div>
          )}
        </div>

        {/* Right Column - Tracking & Timeline (1/3 width on large screens) */}
        <div className="space-y-6">
          {/* Status Card */}
          <div className="bg-parchment border border-warm-gray">
            <div className="p-4 border-b border-warm-gray">
              <h2 className="font-body font-semibold text-ink uppercase tracking-wide text-sm">Status</h2>
            </div>
            <StatusDropdown status={job.status} onChange={handleStatusChange} />
          </div>

          {/* Actions Card */}
          <div className="bg-parchment border border-warm-gray p-4 space-y-3">
            <h2 className="font-body font-semibold text-ink uppercase tracking-wide text-sm mb-3">Actions</h2>

            {job.url && (
              <a
                href={job.url}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-copper text-parchment font-body uppercase tracking-wide text-sm hover:bg-copper/90 transition-colors"
              >
                <ExternalLink size={16} />
                View Original
              </a>
            )}

            {!job.cover_letter && (
              <button
                onClick={handleGenerateCoverLetter}
                disabled={coverLetterGenerating}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-transparent border border-copper text-copper font-body uppercase tracking-wide text-sm hover:bg-copper/10 disabled:opacity-50 transition-colors"
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
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-transparent border border-patina text-patina font-body uppercase tracking-wide text-sm hover:bg-patina/10 disabled:opacity-50 transition-colors"
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
              onClick={handleDelete}
              disabled={deleting}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-rust/10 text-rust font-body uppercase tracking-wide text-sm hover:bg-rust/20 disabled:opacity-50 transition-colors"
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

          {/* Notes Card */}
          <div className="bg-parchment border border-warm-gray">
            <div className="p-4 border-b border-warm-gray flex items-center justify-between">
              <h2 className="font-body font-semibold text-ink uppercase tracking-wide text-sm">Notes</h2>
              {notesSaving && (
                <span className="text-xs text-slate">Saving...</span>
              )}
            </div>
            <div className="p-4">
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                onBlur={handleNotesSave}
                placeholder="Add notes, interview dates, key takeaways..."
                className="w-full px-3 py-2 text-sm border-b border-warm-gray bg-transparent text-ink font-body placeholder-slate focus:border-b-copper focus:bg-warm-gray/50 transition-colors resize-none outline-none min-h-[120px]"
              />
            </div>
          </div>

          {/* Email Activity Timeline */}
          <div className="bg-parchment border border-warm-gray">
            <div className="p-4 border-b border-warm-gray">
              <h2 className="font-body font-semibold text-ink uppercase tracking-wide text-sm">Email Activity</h2>
            </div>
            <div className="p-4">
              <ActivityTimeline activities={activities} loading={activitiesLoading} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
