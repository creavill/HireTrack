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
  DollarSign,
  Search,
  Building2,
  AlertTriangle,
  Users,
  Archive,
  Copy,
  RefreshCw,
  GraduationCap,
  Shield,
  Award,
  Code,
  ChevronRight
} from 'lucide-react';

const API_BASE = '/api';

const STATUS_CONFIG = {
  new: { label: 'New', color: 'slate', icon: Clock },
  interested: { label: 'Interested', color: 'copper', icon: Star },
  applied: { label: 'Applied', color: 'patina', icon: CheckCircle },
  interviewing: { label: 'Interviewing', color: 'cream', icon: Briefcase },
  rejected: { label: 'Rejected', color: 'rust', icon: XCircle },
  offer: { label: 'Offer', color: 'copper', icon: Star },
  passed: { label: 'Passed', color: 'slate', icon: XCircle },
};

function getCompanyInitials(company) {
  if (!company) return '?';
  const words = company.trim().split(/\s+/);
  if (words.length === 1) return words[0].substring(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

function getCompanyColor(company) {
  if (!company) return '#5A5A72';
  const colors = ['#C45D30', '#5B8C6B', '#A0522D', '#5A5A72', '#E8C47C'];
  let hash = 0;
  for (let i = 0; i < company.length; i++) {
    hash = company.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

// Status dropdown component
function StatusDropdown({ status, onChange }) {
  const [isOpen, setIsOpen] = useState(false);
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.new;
  const Icon = config.icon;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-sm border bg-${config.color}/10 border-${config.color}/30 text-${config.color} text-sm font-medium hover:bg-${config.color}/20 transition-colors`}
      >
        <Icon size={14} />
        {config.label}
        <ChevronDown size={14} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      {isOpen && (
        <div className="absolute top-full left-0 mt-1 bg-parchment border border-warm-gray shadow-lg rounded-sm z-20 min-w-[140px]">
          {Object.entries(STATUS_CONFIG).map(([key, cfg]) => {
            const ItemIcon = cfg.icon;
            return (
              <button
                key={key}
                onClick={() => { onChange(key); setIsOpen(false); }}
                className={`w-full text-left px-3 py-2 flex items-center gap-2 text-sm hover:bg-warm-gray/30 ${key === status ? 'bg-warm-gray/20' : ''}`}
              >
                <ItemIcon size={14} className={`text-${cfg.color}`} />
                <span>{cfg.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Requirement badge component
function RequirementBadge({ item, type }) {
  const isMatched = item.matched !== false;

  const icons = {
    experience: Clock,
    education: GraduationCap,
    certification: Award,
    clearance: Shield,
    skill_required: Code,
  };

  const Icon = icons[item.type] || Code;

  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-sm text-sm ${
      isMatched
        ? 'bg-patina/10 text-patina border border-patina/20'
        : 'bg-rust/10 text-rust border border-rust/20'
    }`}>
      {isMatched ? <CheckCircle size={14} /> : <XCircle size={14} />}
      <span>{item.description}</span>
    </div>
  );
}

// Email Activity Component
function ActivityTimeline({ activities, loading }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 size={20} className="animate-spin text-copper" />
      </div>
    );
  }

  if (!activities || activities.length === 0) {
    return (
      <div className="text-center py-6 text-slate text-sm">
        <Mail size={20} className="mx-auto mb-2 opacity-50" />
        No email activity yet
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {activities.slice(0, 5).map((activity, index) => (
        <div
          key={activity.id || index}
          className={`flex gap-3 p-3 rounded-sm bg-warm-gray/10 border-l-2 ${
            activity.classification === 'interview' ? 'border-l-patina' :
            activity.classification === 'offer' ? 'border-l-copper' :
            activity.classification === 'rejection' ? 'border-l-rust' :
            'border-l-slate'
          }`}
        >
          <Mail size={14} className="text-slate flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-sm text-ink truncate">{activity.subject}</p>
            <p className="text-xs text-slate mt-1">{formatDate(activity.date)}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function JobDetailPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();

  // State
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notes, setNotes] = useState('');
  const [notesSaving, setNotesSaving] = useState(false);
  const [activities, setActivities] = useState([]);
  const [activitiesLoading, setActivitiesLoading] = useState(false);
  const [enrichment, setEnrichment] = useState(null);
  const [analysis, setAnalysis] = useState({});
  const [hiringManagerInfo, setHiringManagerInfo] = useState(null);

  // Action states
  const [coverLetterGenerating, setCoverLetterGenerating] = useState(false);
  const [findingHM, setFindingHM] = useState(false);
  const [archiving, setArchiving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [rescoring, setRescoring] = useState(false);

  // Fetch job data
  const fetchJob = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/jobs/${jobId}`);
      if (!res.ok) throw new Error('Job not found');
      const data = await res.json();
      const jobData = data.job || data;  // API returns {job: {...}}
      setJob(jobData);
      setNotes(jobData.notes || '');

      // Parse enrichment data
      if (jobData.last_enriched) {
        setEnrichment({
          is_enriched: true,
          salary_estimate: jobData.salary_estimate,
          full_description: jobData.full_description,
          last_enriched: jobData.last_enriched,
          enrichment_source: jobData.enrichment_source,
          salary_confidence: jobData.salary_confidence,
        });
      }

      // Parse analysis data
      try {
        setAnalysis({
          strengths: jobData.fit_pros ? JSON.parse(jobData.fit_pros) : [],
          gaps: jobData.fit_gaps ? JSON.parse(jobData.fit_gaps) : [],
          fit_score: jobData.fit_score,
          recommendation: jobData.resume_recommendation,
          resume_to_use: jobData.recommended_resume_id,
        });
      } catch (e) { console.error('Failed to parse analysis:', e); }

      // Parse hiring manager info
      if (jobData.hiring_manager_info) {
        try {
          setHiringManagerInfo(typeof jobData.hiring_manager_info === 'string'
            ? JSON.parse(jobData.hiring_manager_info)
            : jobData.hiring_manager_info);
        } catch (e) { console.error('Failed to parse hiring manager info:', e); }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  // Fetch activities
  const fetchActivities = useCallback(async () => {
    try {
      setActivitiesLoading(true);
      const res = await fetch(`${API_BASE}/jobs/${jobId}/activities`);
      if (res.ok) {
        const data = await res.json();
        setActivities(data.activities || []);
      }
    } catch (err) {
      console.error('Failed to fetch activities:', err);
    } finally {
      setActivitiesLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    fetchJob();
    fetchActivities();
  }, [fetchJob, fetchActivities]);

  // Handlers
  const handleStatusChange = async (newStatus) => {
    try {
      await fetch(`${API_BASE}/jobs/${jobId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      setJob(prev => ({ ...prev, status: newStatus }));
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  const handleNotesSave = async () => {
    try {
      setNotesSaving(true);
      await fetch(`${API_BASE}/jobs/${jobId}/notes`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes }),
      });
    } catch (err) {
      console.error('Failed to save notes:', err);
    } finally {
      setNotesSaving(false);
    }
  };

  const handleGenerateCoverLetter = async () => {
    try {
      setCoverLetterGenerating(true);
      const res = await fetch(`${API_BASE}/jobs/${jobId}/cover-letter`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setJob(prev => ({ ...prev, cover_letter: data.cover_letter }));
      }
    } catch (err) {
      console.error('Failed to generate cover letter:', err);
    } finally {
      setCoverLetterGenerating(false);
    }
  };

  const handleFindHiringManager = async () => {
    try {
      setFindingHM(true);
      const res = await fetch(`${API_BASE}/jobs/${jobId}/hiring-manager`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setHiringManagerInfo(data);
      }
    } catch (err) {
      console.error('Failed to find hiring manager:', err);
    } finally {
      setFindingHM(false);
    }
  };

  const handleArchive = async () => {
    try {
      setArchiving(true);
      const res = await fetch(`${API_BASE}/jobs/${jobId}/archive`, { method: 'POST' });
      if (res.ok) navigate('/');
    } catch (err) {
      console.error('Failed to archive:', err);
    } finally {
      setArchiving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Delete this job permanently?')) return;
    try {
      setDeleting(true);
      const res = await fetch(`${API_BASE}/jobs/${jobId}`, { method: 'DELETE' });
      if (res.ok) navigate('/');
    } catch (err) {
      console.error('Failed to delete:', err);
    } finally {
      setDeleting(false);
    }
  };

  const handleRescore = async () => {
    try {
      setRescoring(true);
      const res = await fetch(`${API_BASE}/jobs/${jobId}/rescore`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setJob(prev => ({ ...prev, score: data.new_score, baseline_score: data.new_score }));
      }
    } catch (err) {
      console.error('Failed to rescore:', err);
    } finally {
      setRescoring(false);
    }
  };

  const handleCopyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 size={32} className="animate-spin text-copper" />
      </div>
    );
  }

  // Error state
  if (error || !job) {
    return (
      <div className="text-center py-12">
        <p className="text-rust">{error || 'Job not found'}</p>
        <button onClick={() => navigate('/')} className="mt-4 text-copper hover:underline">
          Back to Jobs
        </button>
      </div>
    );
  }

  // Parse structured requirements
  let structuredReqs = null;
  let reqsMatch = null;
  try {
    if (job.structured_requirements) {
      structuredReqs = typeof job.structured_requirements === 'string'
        ? JSON.parse(job.structured_requirements)
        : job.structured_requirements;
    }
    if (job.requirements_match) {
      reqsMatch = typeof job.requirements_match === 'string'
        ? JSON.parse(job.requirements_match)
        : job.requirements_match;
    }
  } catch (e) { console.error('Failed to parse requirements:', e); }

  // Parse tech stack overlap
  let techOverlap = null;
  try {
    if (job.tech_stack_overlap) {
      techOverlap = typeof job.tech_stack_overlap === 'string'
        ? JSON.parse(job.tech_stack_overlap)
        : job.tech_stack_overlap;
    }
  } catch (e) { console.error('Failed to parse tech overlap:', e); }

  // Parse comprehensive job analysis
  let jobAnalysis = null;
  try {
    if (job.job_analysis) {
      jobAnalysis = typeof job.job_analysis === 'string'
        ? JSON.parse(job.job_analysis)
        : job.job_analysis;
    }
  } catch (e) { console.error('Failed to parse job analysis:', e); }

  const score = job.score || job.baseline_score || 0;
  const statusConfig = STATUS_CONFIG[job.status] || STATUS_CONFIG.new;
  const description = job.full_description || job.job_description;

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-6">
        <div className="flex items-start gap-4">
          <button
            onClick={() => navigate('/')}
            className="p-2 hover:bg-warm-gray/30 rounded-sm transition-colors"
          >
            <ArrowLeft size={20} className="text-slate" />
          </button>

          <div
            className="w-12 h-12 rounded-sm flex items-center justify-center text-parchment font-display text-lg flex-shrink-0"
            style={{ backgroundColor: getCompanyColor(job.company) }}
          >
            {getCompanyInitials(job.company)}
          </div>

          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-display text-ink">{job.title}</h1>
              {job.is_aggregator && (
                <span className="px-2 py-0.5 bg-cream/20 text-cream text-xs font-medium rounded-sm flex items-center gap-1">
                  <AlertTriangle size={12} />
                  Staffing
                </span>
              )}
            </div>
            <p className="text-lg text-slate">{job.company || 'Unknown Company'}</p>
            <div className="flex items-center gap-3 mt-2 flex-wrap">
              {job.location && (
                <span className="flex items-center gap-1 text-sm text-slate">
                  <MapPin size={14} />
                  {job.location}
                </span>
              )}
              {(enrichment?.salary_estimate || job.salary_estimate) && (
                <span className="flex items-center gap-1 text-sm text-patina font-medium">
                  <DollarSign size={14} />
                  {enrichment?.salary_estimate || job.salary_estimate}
                </span>
              )}
              <span className="flex items-center gap-1 text-sm text-slate">
                <Calendar size={14} />
                {formatDate(job.created_at)}
              </span>
            </div>
          </div>
        </div>

        {/* Score & Status */}
        <div className="flex items-center gap-4">
          <div className={`text-3xl font-mono font-bold ${
            score >= 70 ? 'text-patina' : score >= 50 ? 'text-cream' : 'text-rust'
          }`}>
            {score}
          </div>
          <StatusDropdown status={job.status} onChange={handleStatusChange} />
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-2 mb-6 flex-wrap">
        {job.url && (
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 bg-copper text-parchment rounded-sm text-sm font-medium hover:bg-copper/90 transition-colors"
          >
            <ExternalLink size={14} />
            View Original
          </a>
        )}
        {!job.cover_letter && (
          <button
            onClick={handleGenerateCoverLetter}
            disabled={coverLetterGenerating}
            className="inline-flex items-center gap-2 px-4 py-2 border border-copper text-copper rounded-sm text-sm font-medium hover:bg-copper/10 disabled:opacity-50 transition-colors"
          >
            {coverLetterGenerating ? <Loader2 size={14} className="animate-spin" /> : <FileText size={14} />}
            Generate Cover Letter
          </button>
        )}
        <button
          onClick={handleFindHiringManager}
          disabled={findingHM}
          className="inline-flex items-center gap-2 px-4 py-2 border border-slate/30 text-slate rounded-sm text-sm font-medium hover:bg-warm-gray/20 disabled:opacity-50 transition-colors"
        >
          {findingHM ? <Loader2 size={14} className="animate-spin" /> : <Users size={14} />}
          Find Hiring Manager
        </button>
        <button
          onClick={handleRescore}
          disabled={rescoring}
          className="inline-flex items-center gap-2 px-4 py-2 border border-slate/30 text-slate rounded-sm text-sm font-medium hover:bg-warm-gray/20 disabled:opacity-50 transition-colors"
        >
          {rescoring ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
          Rescore
        </button>
        <button
          onClick={handleArchive}
          disabled={archiving}
          className="inline-flex items-center gap-2 px-4 py-2 border border-slate/30 text-slate rounded-sm text-sm font-medium hover:bg-warm-gray/20 disabled:opacity-50 transition-colors"
        >
          {archiving ? <Loader2 size={14} className="animate-spin" /> : <Archive size={14} />}
          Archive
        </button>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="inline-flex items-center gap-2 px-4 py-2 border border-rust/30 text-rust rounded-sm text-sm font-medium hover:bg-rust/10 disabled:opacity-50 transition-colors"
        >
          {deleting ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
          Delete
        </button>
      </div>

      {/* AI Recommendation Banner */}
      {jobAnalysis && (
        <div className={`mb-6 p-5 rounded-sm border ${
          jobAnalysis.recommendation === 'apply' ? 'bg-patina/10 border-patina/30' :
          jobAnalysis.recommendation === 'skip' ? 'bg-rust/10 border-rust/30' :
          'bg-cream/10 border-cream/30'
        }`}>
          <div className="flex items-start gap-4">
            {/* Recommendation Badge */}
            <div className={`flex-shrink-0 px-4 py-2 rounded-sm font-display text-lg font-bold ${
              jobAnalysis.recommendation === 'apply' ? 'bg-patina text-parchment' :
              jobAnalysis.recommendation === 'skip' ? 'bg-rust text-parchment' :
              'bg-cream text-ink'
            }`}>
              {jobAnalysis.recommendation === 'apply' ? 'Apply' :
               jobAnalysis.recommendation === 'skip' ? 'Skip' : 'Maybe'}
            </div>

            {/* Recommendation Details */}
            <div className="flex-1">
              <p className={`text-sm font-medium mb-2 ${
                jobAnalysis.recommendation === 'apply' ? 'text-patina' :
                jobAnalysis.recommendation === 'skip' ? 'text-rust' :
                'text-cream'
              }`}>
                {jobAnalysis.recommendation_reason}
              </p>

              {/* Key Dealbreakers */}
              {jobAnalysis.key_dealbreakers?.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-semibold text-rust uppercase tracking-wide mb-2">Dealbreakers:</p>
                  <div className="flex flex-wrap gap-2">
                    {jobAnalysis.key_dealbreakers.slice(0, 4).map((db, i) => (
                      <span key={i} className="inline-flex items-center gap-1.5 px-2 py-1 bg-rust/10 text-rust text-xs rounded-sm">
                        <XCircle size={12} />
                        {db.requirement}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Experience Gaps */}
              {jobAnalysis.experience_gaps?.length > 0 && !jobAnalysis.key_dealbreakers?.length && (
                <div className="mt-3">
                  <p className="text-xs font-semibold text-slate uppercase tracking-wide mb-2">Experience Gaps:</p>
                  <div className="flex flex-wrap gap-2">
                    {jobAnalysis.experience_gaps.slice(0, 4).map((gap, i) => (
                      <span key={i} className="inline-flex items-center gap-1.5 px-2 py-1 bg-warm-gray/20 text-slate text-xs rounded-sm">
                        <Clock size={12} />
                        {gap.years_required}+ yrs {gap.skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Strengths */}
              {jobAnalysis.strengths?.length > 0 && jobAnalysis.recommendation !== 'skip' && (
                <div className="mt-3">
                  <p className="text-xs font-semibold text-patina uppercase tracking-wide mb-2">Your Strengths:</p>
                  <div className="flex flex-wrap gap-2">
                    {jobAnalysis.strengths.slice(0, 5).map((str, i) => (
                      <span key={i} className="inline-flex items-center gap-1.5 px-2 py-1 bg-patina/10 text-patina text-xs rounded-sm">
                        <CheckCircle size={12} />
                        {str}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Red Flags */}
              {jobAnalysis.red_flags?.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-semibold text-rust uppercase tracking-wide mb-2">
                    <AlertTriangle size={12} className="inline mr-1" />
                    Red Flags:
                  </p>
                  <div className="space-y-1">
                    {jobAnalysis.red_flags.slice(0, 3).map((flag, i) => (
                      <p key={i} className={`text-xs ${
                        flag.severity === 'critical' ? 'text-rust' :
                        flag.severity === 'warning' ? 'text-cream' : 'text-slate'
                      }`}>
                        • {flag.reason}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* Resume Recommendation */}
              {jobAnalysis.resume_recommendation && (
                <div className="mt-3 pt-3 border-t border-warm-gray/30">
                  <p className="text-xs text-slate">
                    <span className="font-semibold">Recommended Resume:</span>{' '}
                    <span className="text-copper">{jobAnalysis.resume_recommendation.name}</span>
                    <span className="text-slate/60"> ({jobAnalysis.resume_recommendation.match_percentage}% match)</span>
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Requirements & Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Requirements Match Section */}
          {reqsMatch && (reqsMatch.matched?.length > 0 || reqsMatch.missing?.length > 0) && (
            <div className="bg-parchment border border-warm-gray rounded-sm">
              <div className="px-5 py-4 border-b border-warm-gray flex items-center justify-between">
                <h2 className="font-display text-lg text-ink flex items-center gap-2">
                  <CheckCircle size={18} className="text-copper" />
                  Requirements Match
                </h2>
                <div className={`px-3 py-1 rounded-sm text-sm font-mono font-bold ${
                  (reqsMatch.match_summary?.match_percentage || 0) >= 70 ? 'bg-patina/20 text-patina' :
                  (reqsMatch.match_summary?.match_percentage || 0) >= 50 ? 'bg-cream/20 text-cream' :
                  'bg-rust/20 text-rust'
                }`}>
                  {reqsMatch.match_summary?.match_percentage || 0}% Match
                </div>
              </div>
              <div className="p-5">
                {/* Match Summary Bar */}
                <div className="mb-5">
                  <div className="flex items-center justify-between text-xs text-slate mb-2">
                    <span>{reqsMatch.match_summary?.matched_count || 0} of {reqsMatch.match_summary?.total_requirements || 0} requirements met</span>
                  </div>
                  <div className="h-2 bg-warm-gray/30 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all ${
                        (reqsMatch.match_summary?.match_percentage || 0) >= 70 ? 'bg-patina' :
                        (reqsMatch.match_summary?.match_percentage || 0) >= 50 ? 'bg-cream' : 'bg-rust'
                      }`}
                      style={{ width: `${reqsMatch.match_summary?.match_percentage || 0}%` }}
                    />
                  </div>
                </div>

                {/* What You Have */}
                {reqsMatch.matched?.length > 0 && (
                  <div className="mb-5">
                    <h3 className="text-sm font-semibold text-patina uppercase tracking-wide mb-3 flex items-center gap-2">
                      <CheckCircle size={14} />
                      What You Have ({reqsMatch.matched.length})
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {reqsMatch.matched.map((item, i) => (
                        <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-patina/10 text-patina text-sm rounded-sm">
                          <CheckCircle size={12} />
                          {item.description}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* What You're Missing */}
                {reqsMatch.missing?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-rust uppercase tracking-wide mb-3 flex items-center gap-2">
                      <XCircle size={14} />
                      Gaps to Address ({reqsMatch.missing.length})
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {reqsMatch.missing.map((item, i) => (
                        <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-rust/10 text-rust text-sm rounded-sm">
                          <XCircle size={12} />
                          {item.description}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Structured Requirements Section */}
          {structuredReqs && (
            <div className="bg-parchment border border-warm-gray rounded-sm">
              <div className="px-5 py-4 border-b border-warm-gray">
                <h2 className="font-display text-lg text-ink flex items-center gap-2">
                  <FileText size={18} className="text-copper" />
                  Job Requirements
                </h2>
              </div>
              <div className="p-5 space-y-5">
                {/* Experience Requirements */}
                {structuredReqs.experience?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-ink uppercase tracking-wide mb-3 flex items-center gap-2">
                      <Clock size={14} className="text-slate" />
                      Experience Required
                    </h3>
                    <div className="space-y-2">
                      {structuredReqs.experience.map((exp, i) => (
                        <div key={i} className="flex items-center gap-3 text-sm">
                          <span className="px-2 py-1 bg-copper/10 text-copper font-mono font-bold rounded-sm">
                            {exp.years}{exp.years_max ? `-${exp.years_max}` : '+'}yr
                          </span>
                          <span className="text-ink">{exp.skill}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Education */}
                {structuredReqs.education?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-ink uppercase tracking-wide mb-3 flex items-center gap-2">
                      <GraduationCap size={14} className="text-slate" />
                      Education
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {structuredReqs.education.map((edu, i) => (
                        <span key={i} className="px-3 py-1.5 bg-warm-gray/20 text-ink text-sm rounded-sm">
                          {edu.level} {edu.field ? `in ${edu.field}` : 'degree'}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Certifications */}
                {structuredReqs.certifications?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-ink uppercase tracking-wide mb-3 flex items-center gap-2">
                      <Award size={14} className="text-slate" />
                      Certifications
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {structuredReqs.certifications.map((cert, i) => (
                        <span key={i} className={`px-3 py-1.5 text-sm rounded-sm ${
                          cert.required ? 'bg-rust/10 text-rust' : 'bg-warm-gray/20 text-slate'
                        }`}>
                          {cert.name}
                          {cert.required && <span className="ml-1 text-xs">(Required)</span>}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Clearance */}
                {structuredReqs.clearance && (
                  <div>
                    <h3 className="text-sm font-semibold text-ink uppercase tracking-wide mb-3 flex items-center gap-2">
                      <Shield size={14} className="text-slate" />
                      Security Clearance
                    </h3>
                    <div className="flex items-center gap-2">
                      <span className="px-3 py-1.5 bg-rust/10 text-rust text-sm font-medium rounded-sm">
                        {structuredReqs.clearance.level}
                      </span>
                      {structuredReqs.clearance.must_obtain && (
                        <span className="text-xs text-slate">(Ability to obtain)</span>
                      )}
                    </div>
                  </div>
                )}

                {/* Required Skills */}
                {structuredReqs.skills_required?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-ink uppercase tracking-wide mb-3 flex items-center gap-2">
                      <Code size={14} className="text-slate" />
                      Required Skills
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {structuredReqs.skills_required.map((skill, i) => (
                        <span key={i} className="px-3 py-1.5 bg-copper/10 text-copper text-sm rounded-sm">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Preferred Skills */}
                {structuredReqs.skills_preferred?.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-slate uppercase tracking-wide mb-3">
                      Nice to Have
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {structuredReqs.skills_preferred.map((skill, i) => (
                        <span key={i} className="px-3 py-1.5 bg-warm-gray/20 text-slate text-sm rounded-sm">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Tech Stack Overlap */}
          {techOverlap && (
            <div className="bg-parchment border border-warm-gray rounded-sm">
              <div className="px-5 py-4 border-b border-warm-gray flex items-center justify-between">
                <h2 className="font-display text-lg text-ink flex items-center gap-2">
                  <Briefcase size={18} className="text-copper" />
                  Tech Stack Match
                </h2>
                <span className={`px-3 py-1 rounded-sm text-sm font-mono font-bold ${
                  techOverlap.match_percentage >= 70 ? 'bg-patina/20 text-patina' :
                  techOverlap.match_percentage >= 50 ? 'bg-cream/20 text-cream' :
                  'bg-rust/20 text-rust'
                }`}>
                  {techOverlap.match_percentage}%
                </span>
              </div>
              <div className="p-5">
                <div className="h-3 bg-warm-gray/30 rounded-full overflow-hidden mb-4">
                  <div
                    className={`h-full transition-all ${
                      techOverlap.match_percentage >= 70 ? 'bg-patina' :
                      techOverlap.match_percentage >= 50 ? 'bg-cream' : 'bg-rust'
                    }`}
                    style={{ width: `${techOverlap.match_percentage}%` }}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h3 className="text-xs font-semibold text-patina uppercase tracking-wide mb-2">
                      Matched ({techOverlap.summary?.matched_count || 0})
                    </h3>
                    <div className="flex flex-wrap gap-1">
                      {Object.values(techOverlap.matched || {}).flat().slice(0, 12).map((skill, i) => (
                        <span key={i} className="px-2 py-1 bg-patina/10 text-patina text-xs rounded-sm">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-xs font-semibold text-rust uppercase tracking-wide mb-2">
                      Missing ({techOverlap.summary?.missing_count || 0})
                    </h3>
                    <div className="flex flex-wrap gap-1">
                      {Object.values(techOverlap.missing || {}).flat().slice(0, 8).map((skill, i) => (
                        <span key={i} className="px-2 py-1 bg-rust/10 text-rust text-xs rounded-sm">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Job Description */}
          {description && (
            <div className="bg-parchment border border-warm-gray rounded-sm">
              <div className="px-5 py-4 border-b border-warm-gray flex items-center justify-between">
                <h2 className="font-display text-lg text-ink flex items-center gap-2">
                  <Briefcase size={18} className="text-copper" />
                  Full Job Description
                </h2>
                {enrichment?.enrichment_source && (
                  <a
                    href={enrichment.enrichment_source}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-copper hover:underline flex items-center gap-1"
                  >
                    <ExternalLink size={12} />
                    Source
                  </a>
                )}
              </div>
              <div className="p-5">
                <div className="prose prose-sm max-w-none text-ink leading-relaxed whitespace-pre-wrap">
                  {description}
                </div>
              </div>
            </div>
          )}

          {/* Cover Letter */}
          {job.cover_letter && (
            <div className="bg-parchment border border-warm-gray rounded-sm">
              <div className="px-5 py-4 border-b border-warm-gray flex items-center justify-between">
                <h2 className="font-display text-lg text-ink flex items-center gap-2">
                  <FileText size={18} className="text-copper" />
                  Cover Letter
                </h2>
                <button
                  onClick={() => handleCopyToClipboard(job.cover_letter)}
                  className="text-xs text-copper hover:text-copper/80 flex items-center gap-1"
                >
                  <Copy size={12} />
                  Copy
                </button>
              </div>
              <div className="p-5">
                <div className="text-sm text-ink leading-relaxed whitespace-pre-wrap bg-warm-gray/10 p-4 rounded-sm">
                  {job.cover_letter}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Sidebar */}
        <div className="space-y-6">
          {/* Notes */}
          <div className="bg-parchment border border-warm-gray rounded-sm">
            <div className="px-4 py-3 border-b border-warm-gray flex items-center justify-between">
              <h3 className="font-display text-sm text-ink flex items-center gap-2">
                <Edit2 size={14} className="text-copper" />
                Notes
              </h3>
              {notesSaving && (
                <span className="text-xs text-patina flex items-center gap-1">
                  <Loader2 size={10} className="animate-spin" />
                  Saving
                </span>
              )}
            </div>
            <div className="p-4">
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                onBlur={handleNotesSave}
                placeholder="Add notes about this job..."
                className="w-full px-3 py-2 text-sm border border-warm-gray bg-warm-gray/10 text-ink resize-none outline-none focus:border-copper rounded-sm min-h-[120px]"
              />
            </div>
          </div>

          {/* Hiring Manager Info */}
          {hiringManagerInfo && (
            <div className="bg-parchment border border-warm-gray rounded-sm">
              <div className="px-4 py-3 border-b border-warm-gray">
                <h3 className="font-display text-sm text-ink flex items-center gap-2">
                  <Users size={14} className="text-copper" />
                  Hiring Manager
                </h3>
              </div>
              <div className="p-4 space-y-3">
                {hiringManagerInfo.linkedin_search && (
                  <div>
                    <p className="text-xs text-slate uppercase tracking-wide mb-1">LinkedIn Search</p>
                    <div className="flex items-center gap-2">
                      <p className="text-sm text-ink flex-1 truncate">{hiringManagerInfo.linkedin_search}</p>
                      <a
                        href={`https://www.linkedin.com/search/results/people/?keywords=${encodeURIComponent(hiringManagerInfo.linkedin_search)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1 text-copper hover:text-copper/80"
                      >
                        <ExternalLink size={14} />
                      </a>
                    </div>
                  </div>
                )}
                {hiringManagerInfo.outreach_template && (
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-xs text-slate uppercase tracking-wide">Outreach Template</p>
                      <button
                        onClick={() => handleCopyToClipboard(hiringManagerInfo.outreach_template)}
                        className="text-xs text-copper"
                      >
                        <Copy size={12} />
                      </button>
                    </div>
                    <p className="text-xs text-ink bg-warm-gray/20 p-2 rounded-sm whitespace-pre-wrap">
                      {hiringManagerInfo.outreach_template}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Email Activity */}
          <div className="bg-parchment border border-warm-gray rounded-sm">
            <div className="px-4 py-3 border-b border-warm-gray">
              <h3 className="font-display text-sm text-ink flex items-center gap-2">
                <Mail size={14} className="text-copper" />
                Email Activity
              </h3>
            </div>
            <div className="p-4">
              <ActivityTimeline activities={activities} loading={activitiesLoading} />
            </div>
          </div>

          {/* Enrichment Info */}
          {enrichment?.is_enriched && (
            <div className="bg-parchment border border-warm-gray rounded-sm">
              <div className="px-4 py-3 border-b border-warm-gray">
                <h3 className="font-display text-sm text-ink flex items-center gap-2">
                  <Search size={14} className="text-copper" />
                  Enrichment
                </h3>
              </div>
              <div className="p-4 text-sm">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate">Last enriched</span>
                  <span className="text-ink">{formatDate(enrichment.last_enriched)}</span>
                </div>
                {enrichment.salary_confidence && enrichment.salary_confidence !== 'none' && (
                  <div className="flex items-center justify-between text-xs mt-2">
                    <span className="text-slate">Salary confidence</span>
                    <span className={`capitalize ${
                      enrichment.salary_confidence === 'high' ? 'text-patina' : 'text-cream'
                    }`}>
                      {enrichment.salary_confidence}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
