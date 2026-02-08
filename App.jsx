import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Search, RefreshCw, FileText, ExternalLink, ChevronDown, ChevronUp, Filter, Briefcase, CheckCircle, XCircle, Clock, Star, Plus, Mail, Phone, User, Upload, Edit2, Trash2, Sparkles, AlertCircle, Menu, X, Settings, Building2, FileStack, Map, BarChart3, Archive, Download, Copy, FileDown, HelpCircle, ArrowUpDown, Trophy } from 'lucide-react';
import JobRow from './components/JobRow.jsx';
import JobDetailPage from './components/JobDetailPage.jsx';
// ActionBanner removed - all jobs are scored on import
import AIProviderSettings from './components/AIProviderSettings.jsx';
import EmailSourcesSettings from './components/EmailSourcesSettings.jsx';
import { GamificationWidget, AchievementsView } from './components/GamificationWidget.jsx';

// Sidebar component for vertical navigation
function Sidebar({ activeView, setActiveView, counts, sidebarOpen, setSidebarOpen, onNavigateHome }) {
  const navItems = [
    { id: 'all_applications', label: 'Jobs', icon: Briefcase, count: counts.jobs },
    { id: 'achievements', label: 'Progress', icon: Trophy, count: null },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, count: null },
    { id: 'followups', label: 'Follow-ups', icon: Mail, count: counts.followups },
    { id: 'resumes', label: 'Resumes', icon: FileStack, count: counts.resumes },
    { id: 'templates', label: 'Templates', icon: FileText, count: null },
    { id: 'companies', label: 'Companies', icon: Building2, count: counts.companies },
    { id: 'settings', label: 'Settings', icon: Settings, count: null },
  ];

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-56 bg-charcoal flex flex-col transform transition-transform duration-200 ease-in-out ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      }`}>
        {/* Close button for mobile */}
        <button
          onClick={() => setSidebarOpen(false)}
          className="absolute top-4 right-4 text-slate hover:text-white lg:hidden"
        >
          <X size={20} />
        </button>

        {/* Wordmark */}
        <div className="p-6 pb-4">
          <h1 className="font-display text-cream text-2xl">Hammy</h1>
          <p className="font-body text-slate text-xs tracking-widest uppercase mt-1">the hire tracker</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id || (item.id === 'all_applications' && activeView === 'roadmap');

            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveView(item.id);
                  setSidebarOpen(false);
                  // Navigate to home to close any open job detail pages
                  if (onNavigateHome) onNavigateHome();
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 mb-1 font-body uppercase tracking-wider text-sm transition-colors ${
                  isActive
                    ? 'text-cream border-l-[3px] border-copper bg-white/5'
                    : 'text-slate hover:text-white border-l-[3px] border-transparent'
                }`}
              >
                <Icon size={18} />
                <span>{item.label}</span>
                {item.count !== null && (
                  <span className={`ml-auto font-mono text-xs ${isActive ? 'text-cream' : 'text-slate'}`}>
                    {item.count}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Gamification Widget */}
        <GamificationWidget onClick={() => {
          setActiveView('achievements');
          setSidebarOpen(false);
          if (onNavigateHome) onNavigateHome();
        }} />
      </aside>
    </>
  );
}

// Help Modal Component - explains how everything works
function HelpModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  const sections = [
    {
      title: 'Getting Started',
      icon: '1',
      content: [
        'Add at least one resume in the Resumes tab',
        'Configure your job preferences in Settings (location, salary, seniority)',
        'Click "Process Emails" to scan your Gmail for job alerts',
      ],
    },
    {
      title: 'How Scanning Works',
      icon: '2',
      content: [
        'Phase 1: Scans Gmail for job alert emails (LinkedIn, Indeed, Greenhouse, etc.)',
        'Phase 2: Filters jobs by your location and seniority preferences',
        'Phase 3: Enriches jobs with web search data (full description, salary)',
        'Phase 4: AI scores each job against your resume (1-100)',
        'Phase 5: Stores follow-up emails (confirmations, rejections, interviews)',
      ],
    },
    {
      title: 'Job Scores',
      icon: '3',
      content: [
        '85-100: Excellent match - apply ASAP',
        '70-84: Good match - worth considering',
        '50-69: Moderate match - review carefully',
        'Below 50: Weak match - likely filtered',
      ],
    },
    {
      title: 'Status Workflow',
      icon: '4',
      content: [
        'New → Interested → Applied → Interviewing → Offer/Rejected',
        'Use "Pass" to archive jobs you\'re not interested in',
        'Jobs are enriched exactly once to save API costs',
      ],
    },
    {
      title: 'Tips',
      icon: '5',
      content: [
        'The sparkle icon (✨) means a job has enriched data',
        'Check the Follow-ups tab for application confirmations and rejections',
        'Use keyboard shortcuts: j/k to navigate, Enter to open, ? for help',
      ],
    },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-parchment border border-warm-gray shadow-xl max-w-2xl w-full max-h-[85vh] overflow-y-auto">
        <div className="sticky top-0 bg-parchment border-b border-warm-gray p-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <HelpCircle size={24} className="text-copper" />
            <h2 className="font-display text-xl text-ink">How Hammy Works</h2>
          </div>
          <button onClick={onClose} className="p-1 text-slate hover:text-ink">
            <X size={20} />
          </button>
        </div>

        <div className="p-4 space-y-6">
          {sections.map((section, idx) => (
            <div key={idx} className="border-l-[3px] border-copper pl-4">
              <h3 className="font-body font-semibold text-ink uppercase tracking-wide text-sm mb-2 flex items-center gap-2">
                <span className="w-6 h-6 bg-copper text-parchment rounded-full flex items-center justify-center text-xs font-bold">
                  {section.icon}
                </span>
                {section.title}
              </h3>
              <ul className="space-y-1">
                {section.content.map((item, i) => (
                  <li key={i} className="text-sm text-slate flex items-start gap-2">
                    <span className="text-copper mt-1">•</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="sticky bottom-0 bg-parchment border-t border-warm-gray p-4">
          <button
            onClick={onClose}
            className="w-full py-2 bg-copper text-parchment font-body uppercase tracking-wide text-sm hover:bg-copper/90 transition-colors"
          >
            Got it!
          </button>
        </div>
      </div>
    </div>
  );
}

// Resume Required Modal - shown when trying to scan without resumes
function ResumeRequiredModal({ isOpen, onClose, onGoToResumes }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-parchment border border-warm-gray shadow-xl max-w-md w-full">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-rust/10 rounded-full flex items-center justify-center">
              <AlertCircle size={24} className="text-rust" />
            </div>
            <div>
              <h2 className="font-display text-xl text-ink">Resume Required</h2>
              <p className="text-sm text-slate">Add a resume before scanning</p>
            </div>
          </div>

          <p className="text-slate text-sm mb-6">
            Hammy needs at least one resume to score jobs against your qualifications.
            Without a resume, job matching won't work properly.
          </p>

          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 py-2 border border-warm-gray text-slate font-body uppercase tracking-wide text-sm hover:border-copper hover:text-ink transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={onGoToResumes}
              className="flex-1 py-2 bg-copper text-parchment font-body uppercase tracking-wide text-sm hover:bg-copper/90 transition-colors"
            >
              Add Resume
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Processing Progress Modal - shows scan progress
function ProcessingModal({ isOpen, phase, stats }) {
  if (!isOpen) return null;

  const phases = [
    { id: 1, name: 'Scanning Emails', icon: Mail },
    { id: 2, name: 'Filtering Jobs', icon: Filter },
    { id: 3, name: 'Enriching Data', icon: Search },
    { id: 4, name: 'AI Scoring', icon: Sparkles },
    { id: 5, name: 'Storing Follow-ups', icon: CheckCircle },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-parchment border border-warm-gray shadow-xl max-w-md w-full">
        <div className="p-6">
          <div className="flex items-center justify-center mb-6">
            <RefreshCw size={40} className="animate-spin text-copper" />
          </div>

          <h2 className="font-display text-xl text-ink text-center mb-2">Processing Emails</h2>
          <p className="text-sm text-slate text-center mb-6">
            Please wait while Hammy scans and analyzes your job alerts...
          </p>

          <div className="space-y-3">
            {phases.map((p) => {
              const Icon = p.icon;
              const isActive = phase === p.id;
              const isComplete = phase > p.id;

              return (
                <div
                  key={p.id}
                  className={`flex items-center gap-3 p-2 rounded ${
                    isActive ? 'bg-copper/10' : ''
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      isComplete
                        ? 'bg-patina text-parchment'
                        : isActive
                        ? 'bg-copper text-parchment'
                        : 'bg-warm-gray text-slate'
                    }`}
                  >
                    {isComplete ? <CheckCircle size={16} /> : <Icon size={16} />}
                  </div>
                  <span
                    className={`text-sm font-body ${
                      isComplete ? 'text-patina' : isActive ? 'text-ink font-medium' : 'text-slate'
                    }`}
                  >
                    {p.name}
                    {isActive && '...'}
                  </span>
                  {isActive && (
                    <RefreshCw size={14} className="animate-spin text-copper ml-auto" />
                  )}
                </div>
              );
            })}
          </div>

          {stats && (
            <div className="mt-6 pt-4 border-t border-warm-gray grid grid-cols-3 gap-2 text-center">
              <div>
                <div className="text-lg font-mono font-bold text-ink">{stats.jobs || 0}</div>
                <div className="text-xs text-slate uppercase">Jobs Found</div>
              </div>
              <div>
                <div className="text-lg font-mono font-bold text-ink">{stats.enriched || 0}</div>
                <div className="text-xs text-slate uppercase">Enriched</div>
              </div>
              <div>
                <div className="text-lg font-mono font-bold text-ink">{stats.scored || 0}</div>
                <div className="text-xs text-slate uppercase">Scored</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const API_BASE = '/api';

const STATUS_CONFIG = {
  new: { label: 'New', borderColor: 'border-l-slate', textColor: 'text-slate', icon: Clock },
  interested: { label: 'Interested', borderColor: 'border-l-copper', textColor: 'text-copper', icon: Star },
  applied: { label: 'Applied', borderColor: 'border-l-cream', textColor: 'text-ink', icon: CheckCircle },
  interviewing: { label: 'Interviewing', borderColor: 'border-l-patina', textColor: 'text-patina', icon: Briefcase },
  rejected: { label: 'Rejected', borderColor: 'border-l-rust', textColor: 'text-rust', icon: XCircle },
  offer: { label: 'Offer', borderColor: 'border-l-copper', textColor: 'text-copper', icon: Star },
  passed: { label: 'Passed', borderColor: 'border-l-slate', textColor: 'text-slate', icon: XCircle },
};

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

function ScoreBadge({ score }) {
  // Determine border color based on score
  let borderColor = 'border-b-rust'; // default for low scores
  if (score >= 80) borderColor = 'border-b-patina';
  else if (score >= 60) borderColor = 'border-b-cream';

  return (
    <span className={`font-mono font-bold text-ink border-b-2 ${borderColor} px-1`}>
      {score || '—'}
    </span>
  );
}

function StatusBadge({ status, onChange, statusConfig }) {
  const config_to_use = statusConfig || STATUS_CONFIG;
  const config = config_to_use[status] || config_to_use.new || config_to_use.applied;
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-1 px-2 py-1 border-l-[3px] ${config.borderColor} ${config.textColor} bg-warm-gray/30 uppercase tracking-wide text-xs font-body hover:bg-warm-gray/50 transition-colors`}
      >
        {config.label}
        <ChevronDown size={12} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 bg-parchment border border-warm-gray shadow-lg z-10 min-w-32">
          {Object.entries(config_to_use).map(([key, cfg]) => (
            <button
              key={key}
              onClick={() => { onChange(key); setIsOpen(false); }}
              className={`w-full text-left px-3 py-2 ${cfg.textColor} hover:bg-warm-gray/50 flex items-center gap-2 uppercase tracking-wide text-xs font-body border-l-[3px] ${cfg.borderColor} ${key === status ? 'bg-warm-gray/30' : ''}`}
            >
              {cfg.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function JobCard({ job, onStatusChange, onGenerateCoverLetter, onRecommendResume, onDelete, expanded, onToggle, onUpdateNotes, isSelected }) {
  const analysis = job.analysis || {};
  const [loadingRecommendation, setLoadingRecommendation] = useState(false);
  const [notes, setNotes] = useState(job.notes || '');
  const [saveStatus, setSaveStatus] = useState(''); // 'saving' or 'saved'
  const [jobDescription, setJobDescription] = useState(job.job_description || job.full_description || '');
  const [descriptionSaveStatus, setDescriptionSaveStatus] = useState(''); // '', 'saving', 'rescoring', 'saved'

  // Parse resume recommendation if available
  let resumeRec = null;
  if (job.resume_recommendation) {
    try {
      resumeRec = typeof job.resume_recommendation === 'string'
        ? JSON.parse(job.resume_recommendation)
        : job.resume_recommendation;
    } catch (e) {
      console.error('Failed to parse resume recommendation:', e);
    }
  }

  const handleGetRecommendation = async () => {
    setLoadingRecommendation(true);
    await onRecommendResume(job.job_id);
    setLoadingRecommendation(false);
  };

  const handleNotesChange = (e) => {
    setNotes(e.target.value);
  };

  const handleNotesSave = async () => {
    if (notes === job.notes) return; // No changes
    setSaveStatus('saving');
    await onUpdateNotes(job.job_id, notes);
    setSaveStatus('saved');
    setTimeout(() => setSaveStatus(''), 2000);
  };

  const handleJobDescriptionChange = (e) => {
    setJobDescription(e.target.value);
  };

  const handleJobDescriptionSave = async () => {
    if (jobDescription === job.job_description) return; // No changes
    if (!jobDescription.trim()) return; // Don't save empty description

    setDescriptionSaveStatus('saving');

    try {
      const response = await fetch(`/api/jobs/${job.job_id}/description`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_description: jobDescription }),
      });

      if (response.ok) {
        const data = await response.json();
        setDescriptionSaveStatus('saved');

        // Trigger parent to refresh the job data to get new score
        if (onUpdateNotes) {
          // Reuse the notes callback to trigger a refresh
          await onUpdateNotes(job.job_id, notes);
        }

        setTimeout(() => setDescriptionSaveStatus(''), 2000);
      } else {
        setDescriptionSaveStatus('');
        console.error('Failed to save job description');
      }
    } catch (err) {
      setDescriptionSaveStatus('');
      console.error('Job description save failed:', err);
    }
  };

  // Format date for display
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className={`bg-parchment border border-warm-gray overflow-hidden transition-all hover:border-copper hover:shadow-[0_2px_8px_rgba(43,43,61,0.08)] hover:-translate-y-px ${
      isSelected ? 'border-copper ring-1 ring-copper/20' : ''
    }`}>
      <div className="p-4">
        <div className="flex items-center gap-4">
          {/* Company logo placeholder */}
          <div
            className="w-10 h-10 rounded-sm flex items-center justify-center flex-shrink-0"
            style={{ backgroundColor: getCompanyColor(job.company) }}
          >
            <span className="text-parchment font-body font-semibold text-sm">
              {getCompanyInitials(job.company)}
            </span>
          </div>

          {/* Main info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <h3 className="font-body font-semibold text-ink truncate">{job.title}</h3>
              {(job.job_description || job.full_description) && (
                <span className="flex-shrink-0" title="Enriched with web search data">
                  <Sparkles size={14} className="text-copper" />
                </span>
              )}
            </div>
            <p className="text-slate text-sm">{job.company || 'Unknown Company'}</p>
            <p className="text-slate text-xs">{job.location || 'Location not specified'}</p>
          </div>

          {/* Score */}
          <div className="flex-shrink-0">
            <ScoreBadge score={job.score} />
          </div>

          {/* Status */}
          <div className="flex-shrink-0">
            <StatusBadge status={job.status} onChange={(s) => onStatusChange(job.job_id, s)} />
          </div>

          {/* Date */}
          <div className="flex-shrink-0 text-xs text-slate w-16 text-right">
            {formatDate(job.created_at)}
          </div>
        </div>

        {analysis.recommendation && (
          <p className="mt-2 text-sm text-slate pl-14">{analysis.recommendation}</p>
        )}
      </div>

      {expanded && (
        <div className="border-t border-warm-gray px-4 py-3 bg-warm-gray/30 space-y-3">
          {analysis.strengths?.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-patina uppercase mb-1 tracking-wide">Strengths</h4>
              <ul className="text-sm text-ink space-y-1">
                {analysis.strengths.map((s, i) => <li key={i}>• {s}</li>)}
              </ul>
            </div>
          )}

          {analysis.gaps?.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-rust uppercase mb-1 tracking-wide">Gaps</h4>
              <ul className="text-sm text-ink space-y-1">
                {analysis.gaps.map((g, i) => <li key={i}>• {g}</li>)}
              </ul>
            </div>
          )}

          {job.cover_letter && (
            <div>
              <h4 className="text-xs font-semibold text-ink uppercase mb-1 tracking-wide">Cover Letter</h4>
              <pre className="text-sm text-ink whitespace-pre-wrap bg-parchment p-3 border border-warm-gray max-h-48 overflow-y-auto font-body">
                {job.cover_letter}
              </pre>
            </div>
          )}

          {/* Job Description Section */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-semibold text-ink uppercase tracking-wide">
                Job Description
              </h4>
              {descriptionSaveStatus && (
                <span className="text-xs text-slate">
                  {descriptionSaveStatus === 'saving' && 'Saving...'}
                  {descriptionSaveStatus === 'rescoring' && 'Rescoring...'}
                  {descriptionSaveStatus === 'saved' && 'Saved & Rescored'}
                </span>
              )}
            </div>
            <textarea
              value={jobDescription}
              onChange={handleJobDescriptionChange}
              onBlur={handleJobDescriptionSave}
              placeholder="Paste the full job description here for better AI analysis..."
              className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-sm text-ink font-body placeholder-slate focus:border-b-copper focus:bg-warm-gray/50 transition-colors min-h-[200px] resize-y outline-none"
              rows={10}
            />
            <p className="text-xs text-slate mt-1">
              Adding the full job description will automatically rescore the job with better accuracy
            </p>
          </div>

          {/* Notes Section */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <h4 className="text-xs font-semibold text-ink uppercase tracking-wide">Notes</h4>
              {saveStatus && (
                <span className={`text-xs ${saveStatus === 'saving' ? 'text-slate' : 'text-patina'}`}>
                  {saveStatus === 'saving' ? 'Saving...' : 'Saved'}
                </span>
              )}
            </div>
            <textarea
              value={notes}
              onChange={handleNotesChange}
              onBlur={handleNotesSave}
              placeholder="Add notes, interview dates, key takeaways..."
              className="w-full px-3 py-2 text-sm border-b border-warm-gray bg-transparent text-ink font-body placeholder-slate focus:border-b-copper focus:bg-warm-gray/50 transition-colors resize-none outline-none"
              rows="3"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2 pt-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                window.open(job.url, '_blank', 'width=1200,height=800,left=100,top=100');
              }}
              className="flex items-center gap-1 px-3 py-1.5 bg-copper text-parchment rounded-none text-sm font-body uppercase tracking-wide hover:bg-copper/90 active:translate-y-px transition-all"
            >
              <ExternalLink size={14} /> <span className="hidden sm:inline">View Job</span><span className="sm:hidden">View</span>
            </button>

            {!job.cover_letter && (
              <button
                onClick={(e) => { e.stopPropagation(); onGenerateCoverLetter(job.job_id); }}
                className="flex items-center gap-1 px-3 py-1.5 bg-transparent border border-copper text-copper rounded-none text-sm font-body uppercase tracking-wide hover:bg-copper/10 transition-all"
              >
                <FileText size={14} /> <span className="hidden sm:inline">Generate Cover Letter</span><span className="sm:hidden">Cover</span>
              </button>
            )}

            <button
              onClick={(e) => { e.stopPropagation(); onDelete(job.job_id); }}
              className="flex items-center gap-1 px-3 py-1.5 bg-rust text-parchment rounded-none text-sm font-body uppercase tracking-wide hover:bg-rust/90 active:translate-y-px transition-all sm:ml-auto"
            >
              <Trash2 size={14} /> Delete
            </button>
          </div>

          <div className="text-xs text-slate">
            Added: {new Date(job.created_at).toLocaleDateString()} •
            Resume: {analysis.resume_to_use || 'fullstack'}
          </div>
        </div>
      )}
    </div>
  );
}

function StatsBar({ stats }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4 mb-6">
      {[
        { label: 'Total', value: stats.total, borderColor: 'border-l-slate' },
        { label: 'New', value: stats.new, borderColor: 'border-l-slate' },
        { label: 'Interested', value: stats.interested, borderColor: 'border-l-copper' },
        { label: 'Applied', value: stats.applied, borderColor: 'border-l-cream' },
        { label: 'Avg Score', value: Math.round(stats.avg_score), borderColor: 'border-l-patina' },
      ].map(({ label, value, borderColor }) => (
        <div key={label} className={`bg-parchment border border-warm-gray border-l-[3px] ${borderColor} p-3 sm:p-4 text-center hover:border-copper transition-colors`}>
          <div className="text-2xl sm:text-3xl font-mono font-bold text-ink">{value}</div>
          <div className="text-xs text-slate font-body uppercase tracking-wide mt-1">{label}</div>
        </div>
      ))}
    </div>
  );
}

function ResumeCard({ resume, onEdit, onDelete, onResearch, expanded, onToggle }) {
  const [researching, setResearching] = useState(false);
  const [showFullContent, setShowFullContent] = useState(false);

  const handleResearch = async (e) => {
    e.stopPropagation();
    setResearching(true);
    await onResearch(resume.resume_id, resume.name);
    setResearching(false);
  };

  // Truncate for preview, show full when expanded
  const previewLength = 500;
  const isLong = resume.content && resume.content.length > previewLength;
  const displayContent = showFullContent ? resume.content : resume.content?.substring(0, previewLength);

  return (
    <div className="bg-parchment border border-warm-gray overflow-hidden hover:border-copper transition-all">
      <div
        className="p-4 cursor-pointer hover:bg-warm-gray/30 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <h3 className="font-body font-semibold text-ink mb-1">{resume.name}</h3>
            {resume.focus_areas && (
              <p className="text-sm text-slate mb-1">
                <span className="font-medium">Focus:</span> {resume.focus_areas}
              </p>
            )}
            {resume.target_roles && (
              <p className="text-sm text-slate">
                <span className="font-medium">Target Roles:</span> {resume.target_roles}
              </p>
            )}
          </div>
          <div className="flex flex-col items-end gap-2">
            <span className="px-2 py-1 border-l-[3px] border-l-copper bg-warm-gray/30 text-xs font-body uppercase tracking-wide text-copper">
              Used {resume.usage_count || 0}x
            </span>
            <div className="flex gap-1">
              <button
                onClick={handleResearch}
                disabled={researching}
                className="p-1.5 text-copper hover:bg-copper/10 transition-colors disabled:opacity-50"
                title="Find jobs for this resume"
              >
                {researching ? <RefreshCw size={16} className="animate-spin" /> : <Sparkles size={16} />}
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); onEdit(resume); }}
                className="p-1.5 text-slate hover:bg-warm-gray/50 transition-colors"
                title="Edit resume"
              >
                <Edit2 size={16} />
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(resume.resume_id); }}
                className="p-1.5 text-rust hover:bg-rust/10 transition-colors"
                title="Delete resume"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-warm-gray px-4 py-4 bg-warm-gray/30 space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-xs text-slate">
              Created: {new Date(resume.created_at).toLocaleDateString()}
              {resume.content && <span className="ml-2">• {resume.content.length.toLocaleString()} characters</span>}
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); onEdit(resume); }}
              className="text-xs text-copper hover:text-copper/80 flex items-center gap-1 px-2 py-1 bg-copper/10 rounded-sm"
            >
              <Edit2 size={12} />
              Edit Resume
            </button>
          </div>
          <div className={`${showFullContent ? 'max-h-[60vh]' : 'max-h-60'} overflow-y-auto`}>
            <pre className="text-sm text-ink whitespace-pre-wrap font-body bg-parchment p-4 border border-warm-gray leading-relaxed">
              {displayContent}
              {isLong && !showFullContent && '...'}
            </pre>
          </div>
          {isLong && (
            <button
              onClick={(e) => { e.stopPropagation(); setShowFullContent(!showFullContent); }}
              className="text-xs text-copper hover:underline"
            >
              {showFullContent ? 'Show less' : `Show all (${resume.content.length.toLocaleString()} characters)`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function ResumeUploadModal({ onClose, onSave }) {
  const [formData, setFormData] = useState({
    name: '',
    focus_areas: '',
    target_roles: '',
    content: ''
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadMode, setUploadMode] = useState('paste'); // 'paste' or 'file'

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      // Auto-fill name from filename if empty
      if (!formData.name) {
        const nameWithoutExt = file.name.replace(/\.[^/.]+$/, '');
        setFormData({ ...formData, name: nameWithoutExt });
      }

      // Read file content for preview (text files only for now)
      if (file.name.endsWith('.txt') || file.name.endsWith('.md')) {
        const reader = new FileReader();
        reader.onload = (event) => {
          setFormData({ ...formData, content: event.target.result });
        };
        reader.readAsText(file);
      } else {
        setFormData({ ...formData, content: `[${file.name} - Text will be extracted on upload]` });
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validate based on upload mode
    if (uploadMode === 'file' && !selectedFile) {
      setError('Please select a file to upload');
      return;
    }
    if (uploadMode === 'paste' && !formData.content) {
      setError('Please paste resume content');
      return;
    }
    if (!formData.name) {
      setError('Resume name is required');
      return;
    }

    setSaving(true);
    try {
      // Use different endpoints based on mode
      if (uploadMode === 'file') {
        // File upload mode - use FormData
        const uploadFormData = new FormData();
        uploadFormData.append('file', selectedFile);
        uploadFormData.append('name', formData.name);
        uploadFormData.append('focus_areas', formData.focus_areas);
        uploadFormData.append('target_roles', formData.target_roles);

        const response = await fetch(`${API_BASE}/resumes/upload`, {
          method: 'POST',
          body: uploadFormData
        });

        const data = await response.json();

        if (response.ok) {
          onSave();
          onClose();
        } else {
          setError(data.error || 'Failed to upload resume');
        }
      } else {
        // Paste mode - use JSON
        const response = await fetch(`${API_BASE}/resumes`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok) {
          onSave();
          onClose();
        } else {
          setError(data.error || 'Failed to save resume');
        }
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    }
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-2 sm:p-4">
      <div className="bg-parchment border border-warm-gray shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="font-display text-2xl text-ink mb-4">Add New Resume</h2>

          {error && (
            <div className="mb-4 p-3 bg-rust/10 border-l-[3px] border-l-rust flex items-start gap-2">
              <AlertCircle size={20} className="text-rust flex-shrink-0 mt-0.5" />
              <p className="text-sm text-rust font-body">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Upload Mode Toggle */}
            <div className="flex gap-2 p-1 bg-warm-gray">
              <button
                type="button"
                onClick={() => setUploadMode('file')}
                className={`flex-1 px-4 py-2 text-sm font-body uppercase tracking-wide transition ${
                  uploadMode === 'file'
                    ? 'bg-parchment text-ink border-l-[3px] border-l-copper'
                    : 'text-slate hover:text-ink'
                }`}
              >
                Upload File
              </button>
              <button
                type="button"
                onClick={() => setUploadMode('paste')}
                className={`flex-1 px-4 py-2 text-sm font-body uppercase tracking-wide transition ${
                  uploadMode === 'paste'
                    ? 'bg-parchment text-ink border-l-[3px] border-l-copper'
                    : 'text-slate hover:text-ink'
                }`}
              >
                Paste Text
              </button>
            </div>

            {/* File Upload Mode */}
            {uploadMode === 'file' && (
              <div className="border-2 border-dashed border-warm-gray p-6 text-center bg-warm-gray/30">
                <Upload size={40} className="mx-auto mb-3 text-slate" />
                <label className="cursor-pointer">
                  <span className="text-sm text-slate font-body">
                    {selectedFile ? (
                      <span className="text-patina font-medium">
                        {selectedFile.name}
                      </span>
                    ) : (
                      <>
                        Click to upload or drag and drop
                        <br />
                        <span className="text-xs text-gray-500 dark:text-gray-400">PDF, TXT, or MD files</span>
                      </>
                    )}
                  </span>
                  <input
                    type="file"
                    accept=".pdf,.txt,.md"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </label>
              </div>
            )}

            <div>
              <label className="block text-sm font-body font-medium text-ink mb-1">
                Resume Name *
              </label>
              <input
                type="text"
                placeholder="e.g., Backend Python AWS"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-ink font-body placeholder-slate focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-body font-medium text-ink mb-1">
                Focus Areas
              </label>
              <input
                type="text"
                placeholder="e.g., Python, AWS, FastAPI, PostgreSQL"
                value={formData.focus_areas}
                onChange={(e) => setFormData({ ...formData, focus_areas: e.target.value })}
                className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-ink font-body placeholder-slate focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-body font-medium text-ink mb-1">
                Target Roles
              </label>
              <input
                type="text"
                placeholder="e.g., Backend Engineer, API Developer"
                value={formData.target_roles}
                onChange={(e) => setFormData({ ...formData, target_roles: e.target.value })}
                className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-ink font-body placeholder-slate focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none"
              />
            </div>

            {/* Paste Mode */}
            {uploadMode === 'paste' && (
              <div>
                <label className="block text-sm font-body font-medium text-ink mb-1">
                  Resume Content *
                </label>
                <textarea
                  placeholder="Paste your resume text here..."
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-ink font-mono text-sm placeholder-slate focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none resize-y"
                  rows={12}
                  required={uploadMode === 'paste'}
                />
              </div>
            )}

            <div className="flex gap-3 pt-4">
              <button
                type="submit"
                disabled={saving}
                className="flex-1 px-4 py-2 bg-copper text-parchment rounded-none uppercase tracking-wide text-sm font-body font-semibold hover:bg-copper/90 active:translate-y-px disabled:opacity-50 transition-all"
              >
                {saving ? 'Saving...' : 'Save Resume'}
              </button>
              <button
                type="button"
                onClick={onClose}
                disabled={saving}
                className="px-4 py-2 bg-transparent border border-warm-gray text-slate rounded-none uppercase tracking-wide text-sm font-body hover:bg-warm-gray/50 disabled:opacity-50 transition-all"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

// Resume Edit Modal Component
function ResumeEditModal({ resume, onClose, onSave }) {
  const [formData, setFormData] = useState({
    name: resume?.name || '',
    focus_areas: resume?.focus_areas || '',
    target_roles: resume?.target_roles || '',
    content: resume?.content || ''
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!formData.name) {
      setError('Resume name is required');
      return;
    }
    if (!formData.content) {
      setError('Resume content is required');
      return;
    }

    setSaving(true);
    try {
      const response = await fetch(`${API_BASE}/resumes/${resume.resume_id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.name,
          focus_areas: formData.focus_areas,
          target_roles: formData.target_roles,
          content: formData.content
        })
      });

      const data = await response.json();

      if (response.ok) {
        onSave();
        onClose();
      } else {
        setError(data.error || 'Failed to update resume');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    }
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-2 sm:p-4">
      <div className="bg-parchment border border-warm-gray shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display text-2xl text-ink">Edit Resume</h2>
            <span className="text-xs text-slate bg-warm-gray/50 px-2 py-1 rounded-sm">
              {formData.content.length.toLocaleString()} characters
            </span>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-rust/10 border-l-[3px] border-l-rust flex items-start gap-2">
              <AlertCircle size={20} className="text-rust flex-shrink-0 mt-0.5" />
              <p className="text-sm text-rust font-body">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-body font-medium text-ink mb-1">
                  Resume Name *
                </label>
                <input
                  type="text"
                  placeholder="e.g., Backend Python AWS"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-ink font-body placeholder-slate focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-body font-medium text-ink mb-1">
                  Focus Areas
                </label>
                <input
                  type="text"
                  placeholder="e.g., Python, AWS, FastAPI"
                  value={formData.focus_areas}
                  onChange={(e) => setFormData({ ...formData, focus_areas: e.target.value })}
                  className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-ink font-body placeholder-slate focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-body font-medium text-ink mb-1">
                  Target Roles
                </label>
                <input
                  type="text"
                  placeholder="e.g., Senior Developer, Tech Lead"
                  value={formData.target_roles}
                  onChange={(e) => setFormData({ ...formData, target_roles: e.target.value })}
                  className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-ink font-body placeholder-slate focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-body font-medium text-ink mb-1">
                Resume Content *
              </label>
              <textarea
                placeholder="Paste or edit your resume content here..."
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                className="w-full px-3 py-2 border border-warm-gray bg-warm-gray/20 text-ink font-body text-sm placeholder-slate focus:border-copper focus:bg-parchment transition-colors outline-none resize-y leading-relaxed"
                rows={20}
                required
              />
            </div>

            <div className="flex gap-3 pt-4 border-t border-warm-gray">
              <button
                type="submit"
                disabled={saving}
                className="flex-1 px-4 py-2 bg-copper text-parchment rounded-none uppercase tracking-wide text-sm font-body font-semibold hover:bg-copper/90 active:translate-y-px disabled:opacity-50 transition-all"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
              <button
                type="button"
                onClick={onClose}
                disabled={saving}
                className="px-4 py-2 bg-transparent border border-warm-gray text-slate rounded-none uppercase tracking-wide text-sm font-body hover:bg-warm-gray/50 disabled:opacity-50 transition-all"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

function ExternalApplicationCard({ app, onStatusChange, expanded, onToggle, onDelete }) {
  const sourceLabels = {
    cold_email: 'Cold Email',
    referral: 'Referral',
    recruiter: 'Recruiter',
    company_website: 'Company Website',
    linkedin_message: 'LinkedIn',
    other: 'Other'
  };

  const EXTERNAL_STATUS_CONFIG = {
    applied: { label: 'Applied', borderColor: 'border-l-cream', textColor: 'text-ink', icon: CheckCircle },
    interviewing: { label: 'Interviewing', borderColor: 'border-l-patina', textColor: 'text-patina', icon: Briefcase },
    rejected: { label: 'Rejected', borderColor: 'border-l-rust', textColor: 'text-rust', icon: XCircle },
    offer: { label: 'Offer', borderColor: 'border-l-copper', textColor: 'text-copper', icon: Star },
    withdrawn: { label: 'Withdrawn', borderColor: 'border-l-slate', textColor: 'text-slate', icon: XCircle },
  };

  return (
    <div className="bg-parchment border border-warm-gray overflow-hidden hover:border-copper transition-all">
      <div
        className="p-4 cursor-pointer hover:bg-warm-gray/30 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 text-xs border-l-[3px] border-l-patina bg-patina/10 text-patina font-body uppercase tracking-wide flex-shrink-0">
                Manual
              </span>
              <h3 className="font-body font-semibold text-ink truncate">{app.title}</h3>
            </div>
            <p className="text-slate text-sm">{app.company}</p>
            <p className="text-slate text-xs">{app.location || 'Location not specified'}</p>
          </div>

          <div className="flex items-center gap-2">
            <StatusBadge
              status={app.status}
              onChange={(s) => onStatusChange(app.app_id, s)}
              statusConfig={EXTERNAL_STATUS_CONFIG}
            />
            <span className="text-xs text-slate">{sourceLabels[app.source] || app.source}</span>
          </div>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-warm-gray px-4 py-3 bg-warm-gray/30 space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-slate">Applied:</span>
              <span className="ml-2 font-medium text-ink">{new Date(app.applied_date).toLocaleDateString()}</span>
            </div>
            {app.application_method && (
              <div>
                <span className="text-slate">Method:</span>
                <span className="ml-2 font-medium text-ink capitalize">{app.application_method.replace('_', ' ')}</span>
              </div>
            )}
            {app.contact_name && (
              <div className="text-ink">
                <User size={14} className="inline mr-1 text-slate" />
                <span className="font-medium">{app.contact_name}</span>
              </div>
            )}
            {app.contact_email && (
              <div className="text-ink">
                <Mail size={14} className="inline mr-1 text-slate" />
                <span className="font-medium">{app.contact_email}</span>
              </div>
            )}
          </div>

          {app.notes && (
            <div>
              <h4 className="text-xs font-semibold text-ink uppercase tracking-wide mb-1">Notes</h4>
              <p className="text-sm text-ink bg-parchment p-3 border border-warm-gray">{app.notes}</p>
            </div>
          )}

          <div className="flex flex-wrap items-center gap-2 pt-2">
            {app.url && (
              <a
                href={app.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 px-3 py-1.5 bg-copper text-parchment rounded-none text-sm font-body uppercase tracking-wide hover:bg-copper/90 transition-all"
              >
                <ExternalLink size={14} /> View Job
              </a>
            )}
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(app.app_id); }}
              className="flex items-center gap-1 px-3 py-1.5 bg-rust text-parchment rounded-none text-sm font-body uppercase tracking-wide hover:bg-rust/90 transition-all"
            >
              Delete
            </button>
          </div>

          <div className="text-xs text-gray-400 dark:text-gray-500">
            Created: {new Date(app.created_at).toLocaleDateString()}
          </div>
        </div>
      )}
    </div>
  );
}

// Analytics View Component
function AnalyticsView() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [archiving, setArchiving] = useState(false);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const res = await fetch('/api/analytics');
      const data = await res.json();
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = () => {
    window.location.href = '/api/jobs/export-csv';
  };

  const handleBulkArchive = async (criteria) => {
    if (!confirm(`Archive all ${criteria.status} jobs${criteria.older_than_days ? ` older than ${criteria.older_than_days} days` : ''}?`)) {
      return;
    }
    setArchiving(true);
    try {
      const res = await fetch('/api/jobs/bulk-archive', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ criteria })
      });
      const data = await res.json();
      alert(`Archived ${data.archived_count} jobs`);
      fetchAnalytics();
    } catch (err) {
      console.error('Bulk archive failed:', err);
    } finally {
      setArchiving(false);
    }
  };

  const handleGmailArchive = async (type) => {
    if (!confirm(`Archive ${type} emails from Gmail?`)) return;
    setArchiving(true);
    try {
      const res = await fetch('/api/gmail/archive-emails', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ criteria: { type, older_than_days: 30 } })
      });
      const data = await res.json();
      if (data.success) {
        alert(`Archived ${data.archived_count} emails from Gmail`);
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (err) {
      console.error('Gmail archive failed:', err);
    } finally {
      setArchiving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw size={32} className="animate-spin text-copper" />
      </div>
    );
  }

  if (!analytics) {
    return <div className="text-center text-slate">Failed to load analytics</div>;
  }

  const { funnel, rates, by_source, by_resume, timeline } = analytics;

  return (
    <div className="space-y-6">
      {/* Quick Actions */}
      <div className="bg-parchment border border-warm-gray p-4">
        <h3 className="font-body font-semibold text-ink mb-3">Quick Actions</h3>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-2 px-3 py-2 bg-copper text-parchment text-sm uppercase tracking-wide font-semibold hover:bg-copper/90 transition-all"
          >
            <FileDown size={16} /> Export CSV
          </button>
          <button
            onClick={() => handleBulkArchive({ status: 'rejected' })}
            disabled={archiving}
            className="flex items-center gap-2 px-3 py-2 border border-warm-gray text-ink text-sm uppercase tracking-wide font-semibold hover:bg-warm-gray/50 disabled:opacity-50 transition-all"
          >
            <Archive size={16} /> Archive Rejections
          </button>
          <button
            onClick={() => handleBulkArchive({ status: 'passed' })}
            disabled={archiving}
            className="flex items-center gap-2 px-3 py-2 border border-warm-gray text-ink text-sm uppercase tracking-wide font-semibold hover:bg-warm-gray/50 disabled:opacity-50 transition-all"
          >
            <Archive size={16} /> Archive Passed
          </button>
          <button
            onClick={() => handleGmailArchive('rejections')}
            disabled={archiving}
            className="flex items-center gap-2 px-3 py-2 border border-rust text-rust text-sm uppercase tracking-wide font-semibold hover:bg-rust/10 disabled:opacity-50 transition-all"
          >
            <Mail size={16} /> Archive Gmail Rejections
          </button>
          <button
            onClick={() => handleGmailArchive('old_alerts')}
            disabled={archiving}
            className="flex items-center gap-2 px-3 py-2 border border-rust text-rust text-sm uppercase tracking-wide font-semibold hover:bg-rust/10 disabled:opacity-50 transition-all"
          >
            <Mail size={16} /> Archive Old Job Alerts
          </button>
        </div>
      </div>

      {/* Funnel Stats */}
      <div className="bg-parchment border border-warm-gray p-4">
        <h3 className="font-body font-semibold text-ink mb-3">Application Funnel</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          {[
            { label: 'Total', value: funnel.total, color: 'border-l-slate' },
            { label: 'New', value: funnel.new, color: 'border-l-slate' },
            { label: 'Interested', value: funnel.interested, color: 'border-l-copper' },
            { label: 'Applied', value: funnel.applied, color: 'border-l-cream' },
            { label: 'Interviewing', value: funnel.interviewing, color: 'border-l-patina' },
            { label: 'Offers', value: funnel.offers, color: 'border-l-copper' },
            { label: 'Rejected', value: funnel.rejected, color: 'border-l-rust' },
            { label: 'Passed', value: funnel.passed, color: 'border-l-slate' },
          ].map(({ label, value, color }) => (
            <div key={label} className={`border border-warm-gray border-l-[3px] ${color} p-3 text-center`}>
              <div className="text-2xl font-mono font-bold text-ink">{value}</div>
              <div className="text-xs text-slate uppercase tracking-wide">{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Key Rates */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-parchment border border-warm-gray border-l-[3px] border-l-patina p-4 text-center">
          <div className="text-3xl font-mono font-bold text-patina">{rates.response_rate}%</div>
          <div className="text-sm text-slate uppercase tracking-wide">Response Rate</div>
          <div className="text-xs text-slate mt-1">({rates.applications_sent} applications)</div>
        </div>
        <div className="bg-parchment border border-warm-gray border-l-[3px] border-l-copper p-4 text-center">
          <div className="text-3xl font-mono font-bold text-copper">{rates.interview_rate}%</div>
          <div className="text-sm text-slate uppercase tracking-wide">Interview Rate</div>
        </div>
        <div className="bg-parchment border border-warm-gray border-l-[3px] border-l-cream p-4 text-center">
          <div className="text-3xl font-mono font-bold text-ink">{rates.offer_rate}%</div>
          <div className="text-sm text-slate uppercase tracking-wide">Offer Rate</div>
        </div>
      </div>

      {/* By Source */}
      <div className="bg-parchment border border-warm-gray p-4">
        <h3 className="font-body font-semibold text-ink mb-3">By Source</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-warm-gray">
                <th className="text-left py-2 text-slate uppercase tracking-wide text-xs">Source</th>
                <th className="text-center py-2 text-slate uppercase tracking-wide text-xs">Total</th>
                <th className="text-center py-2 text-slate uppercase tracking-wide text-xs">Applied</th>
                <th className="text-center py-2 text-slate uppercase tracking-wide text-xs">Interviews</th>
                <th className="text-center py-2 text-slate uppercase tracking-wide text-xs">Offers</th>
                <th className="text-center py-2 text-slate uppercase tracking-wide text-xs">Rejected</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(by_source).map(([source, stats]) => (
                <tr key={source} className="border-b border-warm-gray/50">
                  <td className="py-2 text-ink">{source}</td>
                  <td className="text-center py-2 text-ink font-mono">{stats.total}</td>
                  <td className="text-center py-2 text-ink font-mono">{stats.applied}</td>
                  <td className="text-center py-2 text-patina font-mono">{stats.interviews}</td>
                  <td className="text-center py-2 text-copper font-mono">{stats.offers}</td>
                  <td className="text-center py-2 text-rust font-mono">{stats.rejected}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Resume Stats */}
      {Object.keys(by_resume).length > 0 && (
        <div className="bg-parchment border border-warm-gray p-4">
          <h3 className="font-body font-semibold text-ink mb-3">Resume Performance</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.entries(by_resume).map(([id, stats]) => (
              <div key={id} className="border border-warm-gray p-3">
                <div className="font-semibold text-ink mb-2">{stats.name}</div>
                <div className="grid grid-cols-3 gap-2 text-center text-sm">
                  <div>
                    <div className="font-mono text-ink">{stats.jobs_applied}</div>
                    <div className="text-xs text-slate">Applied</div>
                  </div>
                  <div>
                    <div className="font-mono text-patina">{stats.interviews}</div>
                    <div className="text-xs text-slate">Interviews</div>
                  </div>
                  <div>
                    <div className="font-mono text-copper">{stats.offers}</div>
                    <div className="text-xs text-slate">Offers</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Timeline */}
      {timeline.length > 0 && (
        <div className="bg-parchment border border-warm-gray p-4">
          <h3 className="font-body font-semibold text-ink mb-3">Applications Over Time</h3>
          <div className="flex items-end gap-1 h-32">
            {timeline.map(([week, count]) => {
              const maxCount = Math.max(...timeline.map(([, c]) => c));
              const height = maxCount > 0 ? (count / maxCount) * 100 : 0;
              return (
                <div key={week} className="flex-1 flex flex-col items-center">
                  <div
                    className="w-full bg-copper rounded-t"
                    style={{ height: `${height}%`, minHeight: count > 0 ? '4px' : '0' }}
                    title={`${week}: ${count} applications`}
                  />
                  <div className="text-[10px] text-slate mt-1 rotate-45 origin-left">{week.slice(5)}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// Email Templates View Component
function EmailTemplatesView() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [generatedEmail, setGeneratedEmail] = useState(null);
  const [variables, setVariables] = useState({});
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const res = await fetch('/api/email-templates');
      const data = await res.json();
      setTemplates(data.templates || []);
    } catch (err) {
      console.error('Failed to fetch templates:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateEmail = async () => {
    if (!selectedTemplate) return;
    try {
      const res = await fetch('/api/email-templates/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: selectedTemplate.id,
          variables
        })
      });
      const data = await res.json();
      setGeneratedEmail(data);
    } catch (err) {
      console.error('Failed to generate email:', err);
    }
  };

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Extract variable placeholders from template
  const extractVariables = (template) => {
    const regex = /\{([^}]+)\}/g;
    const vars = new Set();
    let match;
    while ((match = regex.exec(template.subject + template.body)) !== null) {
      vars.add(match[1]);
    }
    return Array.from(vars);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw size={32} className="animate-spin text-copper" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Template List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {templates.map((template) => (
          <div
            key={template.id}
            onClick={() => {
              setSelectedTemplate(template);
              setGeneratedEmail(null);
              setVariables({});
            }}
            className={`bg-parchment border border-warm-gray p-4 cursor-pointer transition-all hover:border-copper ${
              selectedTemplate?.id === template.id ? 'border-copper ring-1 ring-copper/20' : ''
            }`}
          >
            <h3 className="font-body font-semibold text-ink mb-1">{template.name}</h3>
            <p className="text-sm text-slate">{template.subject}</p>
          </div>
        ))}
      </div>

      {/* Template Editor */}
      {selectedTemplate && (
        <div className="bg-parchment border border-warm-gray p-6">
          <h3 className="font-body font-semibold text-ink mb-4">{selectedTemplate.name}</h3>

          {/* Variables */}
          <div className="mb-4">
            <h4 className="text-sm font-semibold text-slate uppercase tracking-wide mb-2">Fill in Variables</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {extractVariables(selectedTemplate).map((varName) => (
                <div key={varName}>
                  <label className="block text-xs text-slate mb-1">{varName.replace(/_/g, ' ')}</label>
                  <input
                    type="text"
                    value={variables[varName] || ''}
                    onChange={(e) => setVariables({ ...variables, [varName]: e.target.value })}
                    className="w-full px-3 py-2 border border-warm-gray bg-parchment text-ink text-sm focus:border-copper outline-none"
                    placeholder={`Enter ${varName.replace(/_/g, ' ')}`}
                  />
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={handleGenerateEmail}
            className="flex items-center gap-2 px-4 py-2 bg-copper text-parchment text-sm uppercase tracking-wide font-semibold hover:bg-copper/90 transition-all"
          >
            <Sparkles size={16} /> Generate Email
          </button>

          {/* Generated Email Preview */}
          {generatedEmail && (
            <div className="mt-6 space-y-4">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs text-slate uppercase tracking-wide">Subject</label>
                  <button
                    onClick={() => handleCopy(generatedEmail.subject)}
                    className="text-xs text-copper hover:text-copper/80"
                  >
                    <Copy size={14} className="inline mr-1" /> Copy
                  </button>
                </div>
                <div className="px-3 py-2 bg-warm-gray/30 border border-warm-gray text-ink">
                  {generatedEmail.subject}
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs text-slate uppercase tracking-wide">Body</label>
                  <button
                    onClick={() => handleCopy(generatedEmail.body)}
                    className="text-xs text-copper hover:text-copper/80"
                  >
                    <Copy size={14} className="inline mr-1" /> {copied ? 'Copied!' : 'Copy'}
                  </button>
                </div>
                <div className="px-3 py-2 bg-warm-gray/30 border border-warm-gray text-ink whitespace-pre-wrap text-sm">
                  {generatedEmail.body}
                </div>
              </div>

              <button
                onClick={() => handleCopy(`Subject: ${generatedEmail.subject}\n\n${generatedEmail.body}`)}
                className="flex items-center gap-2 px-4 py-2 border border-copper text-copper text-sm uppercase tracking-wide font-semibold hover:bg-copper/10 transition-all"
              >
                <Copy size={16} /> Copy Full Email
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Logs Viewer Component
function LogsViewer() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLog, setSelectedLog] = useState(null);
  const [logContent, setLogContent] = useState('');
  const [loadingContent, setLoadingContent] = useState(false);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      const res = await fetch('/api/logs');
      const data = await res.json();
      setLogs(data.logs || []);
    } catch (err) {
      console.error('Failed to fetch logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const viewLog = async (logName) => {
    setSelectedLog(logName);
    setLoadingContent(true);
    try {
      const res = await fetch(`/api/logs/${logName}`);
      const data = await res.json();
      setLogContent(data.content || '');
    } catch (err) {
      console.error('Failed to fetch log content:', err);
      setLogContent('Error loading log content');
    } finally {
      setLoadingContent(false);
    }
  };

  const deleteLog = async (logName, e) => {
    e.stopPropagation();
    if (!confirm(`Delete ${logName}?`)) return;
    try {
      await fetch(`/api/logs/${logName}`, { method: 'DELETE' });
      fetchLogs();
      if (selectedLog === logName) {
        setSelectedLog(null);
        setLogContent('');
      }
    } catch (err) {
      console.error('Failed to delete log:', err);
    }
  };

  const downloadLog = () => {
    if (!selectedLog || !logContent) return;
    const blob = new Blob([logContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = selectedLog;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-parchment border border-warm-gray overflow-hidden mb-6">
      <div className="bg-warm-gray/50 px-4 py-3 border-b border-warm-gray border-l-[3px] border-l-patina">
        <h3 className="font-body font-bold text-ink flex items-center gap-2">
          <FileText size={18} className="text-patina" />
          Operation Logs
        </h3>
        <p className="text-sm text-slate mt-1">
          View logs from scan and score operations
        </p>
      </div>

      <div className="p-4">
        {loading ? (
          <div className="flex items-center justify-center py-4">
            <RefreshCw size={20} className="animate-spin text-copper" />
          </div>
        ) : logs.length === 0 ? (
          <p className="text-sm text-slate">
            No logs yet. Run "Process Emails" to generate logs.
          </p>
        ) : (
          <div className="space-y-4">
            {/* Log list */}
            <div className="flex flex-wrap gap-2">
              {logs.slice(0, 10).map((log) => (
                <button
                  key={log.name}
                  onClick={() => viewLog(log.name)}
                  className={`group flex items-center gap-2 px-3 py-2 text-sm border transition-colors ${
                    selectedLog === log.name
                      ? 'border-copper bg-copper/10 text-copper'
                      : 'border-warm-gray text-ink hover:border-copper'
                  }`}
                >
                  <span className={`uppercase tracking-wide text-xs font-semibold ${
                    log.type === 'process' ? 'text-patina' :
                    log.type === 'scan' ? 'text-copper' :
                    log.type === 'score' ? 'text-rust' : 'text-slate'
                  }`}>
                    {log.type}
                  </span>
                  <span className="text-slate text-xs">
                    {new Date(log.created).toLocaleDateString()} {new Date(log.created).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </span>
                  <button
                    onClick={(e) => deleteLog(log.name, e)}
                    className="opacity-0 group-hover:opacity-100 text-rust hover:text-rust/80 transition-opacity"
                    title="Delete log"
                  >
                    <Trash2 size={14} />
                  </button>
                </button>
              ))}
            </div>

            {/* Log content */}
            {selectedLog && (
              <div className="border border-warm-gray">
                <div className="flex items-center justify-between px-3 py-2 bg-warm-gray/30 border-b border-warm-gray">
                  <span className="font-mono text-sm text-ink">{selectedLog}</span>
                  <button
                    onClick={downloadLog}
                    className="text-xs text-copper hover:text-copper/80 flex items-center gap-1"
                  >
                    <Download size={14} /> Download
                  </button>
                </div>
                {loadingContent ? (
                  <div className="flex items-center justify-center py-8">
                    <RefreshCw size={20} className="animate-spin text-copper" />
                  </div>
                ) : (
                  <pre className="px-3 py-2 text-xs font-mono text-ink whitespace-pre-wrap max-h-96 overflow-y-auto bg-parchment">
                    {logContent}
                  </pre>
                )}
              </div>
            )}

            <button
              onClick={fetchLogs}
              className="text-xs text-copper hover:text-copper/80 flex items-center gap-1"
            >
              <RefreshCw size={12} /> Refresh logs
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const [jobs, setJobs] = useState([]);
  const [stats, setStats] = useState({ total: 0, new: 0, interested: 0, applied: 0, avg_score: 0 });
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scoring, setScoring] = useState(false);
  const [researching, setResearching] = useState(false);
  const [expandedJob, setExpandedJob] = useState(null);
  const [filter, setFilter] = useState({ status: '', minScore: 0, search: '', sort: 'date', app_type: 'all' });
  const [activeView, setActiveView] = useState('all_applications'); // 'all_applications', 'resumes', 'companies', 'roadmap', or 'settings'
  const [externalApps, setExternalApps] = useState([]);
  const [showAddExternal, setShowAddExternal] = useState(false);
  const [resumes, setResumes] = useState([]);
  const [showResumeModal, setShowResumeModal] = useState(false);
  const [editingResume, setEditingResume] = useState(null);
  const [batchRecommending, setBatchRecommending] = useState(false);
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 });
  const [trackedCompanies, setTrackedCompanies] = useState([]);
  const [showAddCompany, setShowAddCompany] = useState(false);
  const [editingCompany, setEditingCompany] = useState(null);
  const [customEmailSources, setCustomEmailSources] = useState([]);
  const [showAddEmailSource, setShowAddEmailSource] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    // Check localStorage or system preference
    const saved = localStorage.getItem('darkMode');
    if (saved !== null) return saved === 'true';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  const [selectedJobIndex, setSelectedJobIndex] = useState(0);
  const [showShortcutsHelp, setShowShortcutsHelp] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [debugScanning, setDebugScanning] = useState(false);
  const [debugResults, setDebugResults] = useState(null);

  // Modal states
  const [showHelpModal, setShowHelpModal] = useState(false);
  const [showResumeRequired, setShowResumeRequired] = useState(false);
  const [processingPhase, setProcessingPhase] = useState(0);
  const [processingStats, setProcessingStats] = useState(null);
  const [followups, setFollowups] = useState([]);
  const [followupStats, setFollowupStats] = useState({ total: 0, interviews: 0, rejections: 0, offers: 0, assessments: 0 });
  const [followupsLoading, setFollowupsLoading] = useState(false);
  const [scanningFollowups, setScanningFollowups] = useState(false);

  // Update HTML element and localStorage when dark mode changes
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('darkMode', darkMode);
  }, [darkMode]);

  // Toast notification system
  const showToast = useCallback((message, type = 'info') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3000);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e) => {
      // Ignore if typing in input/textarea
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

      // Only apply shortcuts on all applications view
      if (activeView !== 'all_applications') {
        if (e.key === '?') setShowShortcutsHelp(true);
        return;
      }

      const filteredJobsList = jobs.filter(job => {
        const matchesSearch = !filter.search ||
          job.title?.toLowerCase().includes(filter.search.toLowerCase()) ||
          job.company?.toLowerCase().includes(filter.search.toLowerCase());
        const matchesStatus = !filter.status || job.status === filter.status;
        const matchesScore = job.score >= filter.minScore;
        return matchesSearch && matchesStatus && matchesScore;
      });

      switch(e.key) {
        case 'j':
          e.preventDefault();
          setSelectedJobIndex(prev => Math.min(prev + 1, filteredJobsList.length - 1));
          break;
        case 'k':
          e.preventDefault();
          setSelectedJobIndex(prev => Math.max(prev - 1, 0));
          break;
        case '/':
          e.preventDefault();
          document.querySelector('input[placeholder*="Search"]')?.focus();
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredJobsList[selectedJobIndex]) {
            navigate(`/jobs/${filteredJobsList[selectedJobIndex].job_id}`);
          }
          break;
        case 'd':
          e.preventDefault();
          if (filteredJobsList[selectedJobIndex] && confirm('Delete this job?')) {
            handleDeleteJob(filteredJobsList[selectedJobIndex].job_id);
            setSelectedJobIndex(prev => Math.max(0, Math.min(prev, filteredJobsList.length - 2)));
          }
          break;
        case '?':
          e.preventDefault();
          setShowShortcutsHelp(true);
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [activeView, filter, jobs, selectedJobIndex, navigate]);
  
  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filter.status) params.set('status', filter.status);
      if (filter.minScore) params.set('min_score', filter.minScore);
      params.set('sort', 'score');
      
      const res = await fetch(`${API_BASE}/jobs?${params}`);
      const data = await res.json();
      
      setJobs(data.jobs || []);
      setStats(data.stats || {});
    } catch (err) {
      console.error('Failed to fetch jobs:', err);
    }
    setLoading(false);
  }, [filter.status, filter.minScore]);
  
  const fetchExternalApps = useCallback(async () => {
    console.log('[Frontend] Fetching external applications...');
    try {
      const res = await fetch(`${API_BASE}/external-applications`);
      const data = await res.json();
      console.log(`[Frontend] Received ${data.applications?.length || 0} external applications`);
      setExternalApps(data.applications || []);
    } catch (err) {
      console.error('[Frontend] Failed to fetch external applications:', err);
    }
  }, []);

  const fetchResumes = useCallback(async () => {
    console.log('[Frontend] Fetching resumes...');
    try {
      const res = await fetch(`${API_BASE}/resumes`);
      const data = await res.json();
      console.log(`[Frontend] Received ${data.resumes?.length || 0} resumes`);
      setResumes(data.resumes || []);
    } catch (err) {
      console.error('[Frontend] Failed to fetch resumes:', err);
    }
  }, []);

  const fetchTrackedCompanies = useCallback(async () => {
    console.log('[Frontend] Fetching tracked companies...');
    try {
      const res = await fetch(`${API_BASE}/tracked-companies`);
      const data = await res.json();
      console.log(`[Frontend] Received ${data.companies?.length || 0} tracked companies`);
      setTrackedCompanies(data.companies || []);
    } catch (err) {
      console.error('[Frontend] Failed to fetch tracked companies:', err);
    }
  }, []);

  const fetchCustomEmailSources = useCallback(async () => {
    console.log('[Frontend] Fetching custom email sources...');
    try {
      const res = await fetch(`${API_BASE}/custom-email-sources`);
      const data = await res.json();
      console.log(`[Frontend] Received ${data.sources?.length || 0} custom email sources`);
      setCustomEmailSources(data.sources || []);
    } catch (err) {
      console.error('[Frontend] Failed to fetch custom email sources:', err);
    }
  }, []);

  const fetchFollowups = useCallback(async () => {
    console.log('[Frontend] Fetching followups...');
    setFollowupsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/followups`);
      const data = await res.json();
      console.log(`[Frontend] Received ${data.followups?.length || 0} followups`);
      setFollowups(data.followups || []);
      setFollowupStats(data.stats || { total: 0, interviews: 0, rejections: 0, offers: 0, assessments: 0 });
    } catch (err) {
      console.error('[Frontend] Failed to fetch followups:', err);
    } finally {
      setFollowupsLoading(false);
    }
  }, []);

  const handleScanFollowups = async () => {
    setScanningFollowups(true);
    try {
      const res = await fetch(`${API_BASE}/scan-followups`, { method: 'POST' });
      const data = await res.json();
      console.log('[Frontend] Scan followups result:', data);
      // Refresh followups after scan
      await fetchFollowups();
    } catch (err) {
      console.error('[Frontend] Scan followups failed:', err);
    } finally {
      setScanningFollowups(false);
    }
  };

  useEffect(() => {
    console.log('[Frontend] Component mounted, fetching initial data...');
    fetchJobs();
    fetchExternalApps();
    fetchResumes();
    fetchTrackedCompanies();
    fetchCustomEmailSources();
    fetchFollowups();
  }, [fetchJobs, fetchExternalApps, fetchResumes, fetchTrackedCompanies, fetchCustomEmailSources, fetchFollowups]);

  // Separate effect for polling to avoid recreating interval
  useEffect(() => {
    // Poll for external applications every 5 seconds to catch updates from extension
    console.log('[Frontend] Setting up polling for external applications (5s interval)');
    const pollInterval = setInterval(() => {
      console.log('[Frontend] Polling for external applications updates...');
      fetchExternalApps();
    }, 5000);

    return () => {
      console.log('[Frontend] Cleaning up polling interval');
      clearInterval(pollInterval);
    };
  }, [fetchExternalApps]);

  // UNIFIED: Scan + Enrich + Score all in one
  const handleProcessEmails = async () => {
    // Check if user has at least one resume
    if (resumes.length === 0) {
      setShowResumeRequired(true);
      return;
    }

    setScanning(true);
    setProcessingPhase(1); // Start at phase 1
    setProcessingStats(null);

    try {
      // Simulate phase progression for better UX
      // In reality, we don't get real-time updates from the API
      const phaseInterval = setInterval(() => {
        setProcessingPhase((prev) => {
          if (prev < 5) return prev + 1;
          return prev;
        });
      }, 8000); // Progress every 8 seconds

      const response = await fetch(`${API_BASE}/scan-and-process`, { method: 'POST' });
      const data = await response.json();

      clearInterval(phaseInterval);
      setProcessingPhase(5); // Complete

      if (data.error) {
        showToast(`Processing failed: ${data.error}`, 'error');
      } else {
        // Update stats for the modal
        setProcessingStats({
          jobs: data.jobs_new || 0,
          enriched: data.jobs_enriched || 0,
          scored: data.jobs_scored || 0,
        });

        const summary = [
          data.jobs_new > 0 ? `${data.jobs_new} new jobs` : null,
          data.jobs_enriched > 0 ? `${data.jobs_enriched} enriched` : null,
          data.jobs_scored > 0 ? `${data.jobs_scored} scored` : null,
          data.followups_new > 0 ? `${data.followups_new} follow-ups` : null,
        ].filter(Boolean).join(', ');
        showToast(`✓ ${summary || 'No new jobs found'}`, 'success');
        if (data.log_file) {
          console.log(`Log file: logs/${data.log_file}`);
        }
      }
      // Refresh jobs
      setTimeout(fetchJobs, 2000);
    } catch (err) {
      console.error('Processing failed:', err);
      showToast('Processing failed. Check console for details.', 'error');
    }
    setScanning(false);
    setProcessingPhase(0);
  };

  // Legacy scan (for backwards compatibility)
  const handleScan = handleProcessEmails;

  const handleScoreJobs = async () => {
    setScoring(true);
    try {
      const response = await fetch(`${API_BASE}/score-jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enrich_first: true }),
      });
      const data = await response.json();
      if (data.error) {
        showToast(`Scoring failed: ${data.error}`, 'error');
      } else {
        showToast(`✓ Enriched ${data.enriched || 0}, Scored ${data.scored}/${data.total}`, 'success');
      }
      setTimeout(fetchJobs, 2000);
    } catch (err) {
      console.error('Scoring failed:', err);
      showToast('Scoring failed. Check console for details.', 'error');
    }
    setScoring(false);
  };

  const handleDebugScan = async () => {
    setDebugScanning(true);
    setDebugResults(null);
    showToast('Running debug scan on recent emails...', 'info');
    try {
      const response = await fetch(`${API_BASE}/debug-scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count: 40, days_back: 7 }),
      });
      const data = await response.json();
      if (data.error) {
        showToast(`Debug scan failed: ${data.error}`, 'error');
      } else {
        setDebugResults(data);
        showToast(`Debug scan complete: ${data.emails_processed} emails processed`, 'success');
      }
    } catch (err) {
      console.error('Debug scan failed:', err);
      showToast('Debug scan failed. Check console for details.', 'error');
    }
    setDebugScanning(false);
  };

  const downloadDebugLog = () => {
    if (!debugResults?.log_content) return;
    const blob = new Blob([debugResults.log_content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `debug_scan_${new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')}.log`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleStatusChange = async (jobId, newStatus) => {
    try {
      await fetch(`${API_BASE}/jobs/${jobId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      fetchJobs();
    } catch (err) {
      console.error('Status update failed:', err);
    }
  };

  const handleUpdateNotes = async (jobId, notes) => {
    try {
      const response = await fetch(`${API_BASE}/jobs/${jobId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes }),
      });

      if (response.ok) {
        // Refresh the job list to get updated data (including new scores from description updates)
        await fetchJobs();
      } else {
        // Fallback: just update notes locally
        setJobs((prevJobs) =>
          prevJobs.map((job) =>
            job.job_id === jobId ? { ...job, notes } : job
          )
        );
      }
    } catch (err) {
      console.error('Notes update failed:', err);
      showToast('Failed to save notes', 'error');
    }
  };
  
  const handleGenerateCoverLetter = async (jobId) => {
    try {
      await fetch(`${API_BASE}/jobs/${jobId}/cover-letter`, { method: 'POST' });
      // Poll for completion
      setTimeout(fetchJobs, 5000);
      setTimeout(fetchJobs, 15000);
    } catch (err) {
      console.error('Cover letter generation failed:', err);
    }
  };

  const handleExternalStatusChange = async (appId, newStatus) => {
    console.log(`[Frontend] Updating external application ${appId} status to: ${newStatus}`);
    try {
      await fetch(`${API_BASE}/external-applications/${appId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      console.log('[Frontend] Status update successful, refreshing list...');
      fetchExternalApps();
    } catch (err) {
      console.error('[Frontend] External app status update failed:', err);
    }
  };

  const handleDeleteExternal = async (appId) => {
    console.log(`[Frontend] Deleting external application: ${appId}`);
    try {
      await fetch(`${API_BASE}/external-applications/${appId}`, { method: 'DELETE' });
      console.log('[Frontend] Delete successful, refreshing list...');
      fetchExternalApps();
    } catch (err) {
      console.error('[Frontend] Delete failed:', err);
    }
  };

  // Tracked Companies handlers (from tracked-companies branch)
  const handleAddTrackedCompany = async (companyData) => {
    console.log('[Frontend] Adding tracked company:', companyData);
    try {
      await fetch(`${API_BASE}/tracked-companies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(companyData),
      });
      console.log('[Frontend] Company added successfully, refreshing list...');
      fetchTrackedCompanies();
      setShowAddCompany(false);
    } catch (err) {
      console.error('[Frontend] Failed to add company:', err);
    }
  };

  // Custom Email Sources handlers
  const handleAddEmailSource = async (sourceData) => {
    console.log('[Frontend] Adding custom email source:', sourceData);
    try {
      await fetch(`${API_BASE}/custom-email-sources`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sourceData),
      });
      console.log('[Frontend] Email source added successfully, refreshing list...');
      showToast(`✓ Added ${sourceData.name}`, 'success');
      fetchCustomEmailSources();
      setShowAddEmailSource(false);
    } catch (err) {
      console.error('[Frontend] Failed to add email source:', err);
      showToast('Failed to add email source', 'error');
    }
  };

  const handleToggleEmailSource = async (source) => {
    try {
      await fetch(`${API_BASE}/custom-email-sources/${source.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: source.name,
          sender_email: source.sender_email || '',
          sender_pattern: source.sender_pattern || '',
          subject_keywords: source.subject_keywords || '',
          enabled: source.enabled ? 0 : 1,
        }),
      });
      fetchCustomEmailSources();
    } catch (err) {
      console.error('[Frontend] Failed to toggle email source:', err);
    }
  };

  const handleDeleteEmailSource = async (sourceId) => {
    try {
      await fetch(`${API_BASE}/custom-email-sources/${sourceId}`, { method: 'DELETE' });
      console.log('[Frontend] Email source deleted successfully, refreshing list...');
      fetchCustomEmailSources();
    } catch (err) {
      console.error('[Frontend] Failed to delete email source:', err);
    }
  };

  const handleUpdateTrackedCompany = async (companyId, companyData) => {
    console.log(`[Frontend] Updating tracked company ${companyId}:`, companyData);
    try {
      await fetch(`${API_BASE}/tracked-companies/${companyId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(companyData),
      });
      console.log('[Frontend] Company updated successfully, refreshing list...');
      fetchTrackedCompanies();
      setEditingCompany(null);
    } catch (err) {
      console.error('[Frontend] Failed to update company:', err);
    }
  };

  const handleDeleteTrackedCompany = async (companyId) => {
    console.log(`[Frontend] Deleting tracked company: ${companyId}`);
    try {
      await fetch(`${API_BASE}/tracked-companies/${companyId}`, { method: 'DELETE' });
      console.log('[Frontend] Company deleted successfully, refreshing list...');
      fetchTrackedCompanies();
    } catch (err) {
      console.error('[Frontend] Failed to delete company:', err);
    }
  };

  // Job management handlers (from job-management-features branch)
  const handleDeleteJob = async (jobId) => {
    try {
      await fetch(`${API_BASE}/jobs/${jobId}`, { method: 'DELETE' });
      // Update jobs state directly instead of refetching
      setJobs(prevJobs => prevJobs.filter(job => job.job_id !== jobId));
    } catch (err) {
      console.error('Delete job failed:', err);
    }
  };

  const handleResearchJobs = async () => {
    setResearching(true);
    try {
      const response = await fetch(`${API_BASE}/research-jobs`, { method: 'POST' });
      const data = await response.json();

      if (data.success) {
        alert(`✨ Claude found ${data.jobs_saved} new job recommendations!`);
        // Refresh jobs list to show new researched jobs
        setTimeout(fetchJobs, 2000);
      } else {
        alert(`Research failed: ${data.error || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('Job research failed:', err);
      alert('Job research failed. Check console for details.');
    }
    setResearching(false);
  };

  const handleRecommendResume = async (jobId) => {
    console.log(`[Frontend] Getting resume recommendation for job: ${jobId}`);
    try {
      const res = await fetch(`${API_BASE}/jobs/${jobId}/recommend-resume`, {
        method: 'POST'
      });
      const data = await res.json();
      console.log('[Frontend] Recommendation received:', data);
      fetchJobs(); // Refresh to show recommendation
    } catch (err) {
      console.error('[Frontend] Resume recommendation failed:', err);
    }
  };

  const handleBatchRecommend = async () => {
    const jobIds = jobs.filter(j => !j.resume_recommendation).map(j => j.job_id);

    if (jobIds.length === 0) {
      alert('All jobs already have recommendations!');
      return;
    }

    if (!confirm(`Generate resume recommendations for ${jobIds.length} jobs? This may take a few minutes.`)) {
      return;
    }

    setBatchRecommending(true);
    setBatchProgress({ current: 0, total: jobIds.length });

    try {
      const res = await fetch(`${API_BASE}/jobs/recommend-resumes-batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_ids: jobIds })
      });
      const data = await res.json();

      console.log('[Frontend] Batch recommendation complete:', data);
      alert(`Batch complete! ${data.summary.successful} successful, ${data.summary.failed} failed`);
      fetchJobs(); // Refresh to show all recommendations
    } catch (err) {
      console.error('[Frontend] Batch recommendation failed:', err);
      alert('Batch recommendation failed: ' + err.message);
    }

    setBatchRecommending(false);
    setBatchProgress({ current: 0, total: 0 });
  };

  const handleDeleteResume = async (resumeId) => {
    if (!confirm('Are you sure you want to delete this resume?')) {
      return;
    }

    try {
      await fetch(`${API_BASE}/resumes/${resumeId}`, { method: 'DELETE' });
      fetchResumes();
    } catch (err) {
      console.error('[Frontend] Resume deletion failed:', err);
    }
  };

  const handleResearchForResume = async (resumeId, resumeName) => {
    console.log(`[Frontend] Researching jobs for resume: ${resumeName}`);
    try {
      const response = await fetch(`${API_BASE}/research-jobs/${resumeId}`, { method: 'POST' });
      const data = await response.json();

      if (data.success) {
        alert(`✨ Claude found ${data.jobs_saved} jobs tailored for "${resumeName}"!`);
        // Refresh jobs list to show new researched jobs
        setTimeout(fetchJobs, 2000);
      } else {
        alert(`Research failed: ${data.error || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('[Frontend] Job research failed:', err);
      alert('Job research failed. Check console for details.');
    }
  };

  const filteredJobs = jobs
    .filter(job => {
      if (filter.search) {
        const search = filter.search.toLowerCase();
        const matches =
          job.title?.toLowerCase().includes(search) ||
          job.company?.toLowerCase().includes(search);
        if (!matches) return false;
      }
      return true;
    })
    .sort((a, b) => {
      switch (filter.sort) {
        case 'date':
          return new Date(b.created_at) - new Date(a.created_at);
        case 'date-oldest':
          return new Date(a.created_at) - new Date(b.created_at);
        case 'title':
          return (a.title || '').localeCompare(b.title || '');
        case 'title-desc':
          return (b.title || '').localeCompare(a.title || '');
        case 'score':
          return (b.score || 0) - (a.score || 0);
        case 'score-low':
          return (a.score || 0) - (b.score || 0);
        default:
          return new Date(b.created_at) - new Date(a.created_at);
      }
    });

  // Combine jobs and external applications for unified view
  const allApplications = useMemo(() => {
    const combinedList = [];

    // Add discovered jobs with type marker
    jobs.forEach(job => {
      combinedList.push({
        ...job,
        app_type: 'discovered',
        sort_date: job.email_date || job.created_at,
        display_status: job.status
      });
    });

    // Add external applications with type marker
    externalApps.forEach(app => {
      combinedList.push({
        ...app,
        app_type: 'external',
        sort_date: app.applied_date || app.created_at,
        display_status: app.status
      });
    });

    // Sort based on filter.sort
    return combinedList.sort((a, b) => {
      switch (filter.sort) {
        case 'score':
          return (b.score || 0) - (a.score || 0);
        case 'score-low':
          return (a.score || 0) - (b.score || 0);
        case 'title':
          return (a.title || '').localeCompare(b.title || '');
        case 'title-desc':
          return (b.title || '').localeCompare(a.title || '');
        case 'status':
          return (a.display_status || '').localeCompare(b.display_status || '');
        case 'status-desc':
          return (b.display_status || '').localeCompare(a.display_status || '');
        case 'date-oldest':
          return new Date(a.sort_date || 0) - new Date(b.sort_date || 0);
        case 'date':
        default:
          return new Date(b.sort_date || 0) - new Date(a.sort_date || 0);
      }
    });
  }, [jobs, externalApps, filter.sort]);

  // Counts for sidebar
  const sidebarCounts = {
    jobs: allApplications.length,
    resumes: resumes.length,
    companies: trackedCompanies.length,
    followups: followupStats.total || followups.length,
  };

  // Navigate to home (closes job detail page)
  const navigateHome = useCallback(() => {
    navigate('/');
  }, [navigate]);

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <Sidebar
        activeView={activeView}
        setActiveView={setActiveView}
        counts={sidebarCounts}
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        onNavigateHome={navigateHome}
      />

      {/* Main content area */}
      <div className="flex-1 min-w-0 lg:ml-0">
        {/* Top header with mobile menu button and actions */}
        <header className="bg-parchment border-b border-warm-gray px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between gap-4">
            {/* Mobile menu button */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 text-ink hover:text-copper transition-colors"
            >
              <Menu size={24} />
            </button>

            {/* Page title */}
            <h2 className="font-display text-xl text-ink hidden sm:block">
              {activeView === 'all_applications' && 'Jobs'}
              {activeView === 'achievements' && 'Progress & Achievements'}
              {activeView === 'analytics' && 'Analytics'}
              {activeView === 'followups' && 'Follow-ups'}
              {activeView === 'resumes' && 'Resume Library'}
              {activeView === 'templates' && 'Email Templates'}
              {activeView === 'companies' && 'Tracked Companies'}
              {activeView === 'settings' && 'Settings'}
            </h2>

            {/* Actions with help button */}
            <div className="flex items-center gap-2 ml-auto">
              {/* Help button */}
              <button
                onClick={() => setShowHelpModal(true)}
                className="p-2 text-slate hover:text-copper transition-colors"
                title="How to use Hammy"
              >
                <HelpCircle size={20} />
              </button>

              {/* Process button */}
              <button
                onClick={handleProcessEmails}
                disabled={scanning}
                className="flex items-center gap-2 px-4 py-2 bg-copper text-parchment rounded-none uppercase tracking-wide text-sm font-body font-semibold hover:bg-copper/90 active:translate-y-px disabled:opacity-50 transition-all"
              >
                <RefreshCw size={16} className={scanning ? 'animate-spin' : ''} />
                <span>{scanning ? 'Processing...' : 'Process Emails'}</span>
              </button>
            </div>
          </div>
        </header>

        <main className="px-4 sm:px-6 py-6">
        <Routes>
          <Route path="/jobs/:jobId" element={<JobDetailPage />} />
          <Route path="*" element={
        activeView === 'all_applications' ? (
          <>
            <StatsBar stats={stats} />

            {/* Filters */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 mb-6">
              {/* App Type Filter */}
              <select
                value={filter.app_type}
                onChange={(e) => setFilter({ ...filter, app_type: e.target.value })}
                className="px-3 py-2 border-b border-warm-gray bg-parchment text-ink font-body text-sm focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none"
              >
                <option value="all">All Types</option>
                <option value="discovered">Discovered Jobs</option>
                <option value="external">External Apps</option>
              </select>

              <div className="relative sm:col-span-2 lg:col-span-1">
                <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate" />
                <input
                  type="text"
                  placeholder="Search applications..."
                  value={filter.search}
                  onChange={(e) => setFilter({ ...filter, search: e.target.value })}
                  className="w-full pl-10 pr-4 py-2 border-b border-warm-gray bg-parchment text-ink font-body text-sm placeholder-slate focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none"
                />
              </div>

              <select
                value={filter.status}
                onChange={(e) => setFilter({ ...filter, status: e.target.value })}
                className="px-3 py-2 border-b border-warm-gray bg-parchment text-ink font-body text-sm focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none"
              >
                <option value="">All Statuses</option>
                {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
                  <option key={key} value={key}>{cfg.label}</option>
                ))}
              </select>

              <select
                value={filter.minScore}
                onChange={(e) => setFilter({ ...filter, minScore: Number(e.target.value) })}
                className="px-3 py-2 border-b border-warm-gray bg-parchment text-ink font-body text-sm focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none"
              >
                <option value="0">All Scores</option>
                <option value="80">80+ (Highly Qualified)</option>
                <option value="60">60+ (Good Match)</option>
                <option value="40">40+ (Partial Match)</option>
              </select>

              <select
                value={filter.sort}
                onChange={(e) => setFilter({ ...filter, sort: e.target.value })}
                className="px-3 py-2 border-b border-warm-gray bg-parchment text-ink font-body text-sm focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none"
              >
                <option value="date">Date (Newest)</option>
                <option value="date-oldest">Date (Oldest)</option>
                <option value="title">Title (A-Z)</option>
                <option value="title-desc">Title (Z-A)</option>
                <option value="score">Score (High-Low)</option>
                <option value="score-low">Score (Low-High)</option>
                <option value="status">Status (A-Z)</option>
                <option value="status-desc">Status (Z-A)</option>
              </select>
            </div>

            {/* Unified Applications List */}
            {loading ? (
              <div className="bg-parchment border border-warm-gray overflow-hidden">
                {[1, 2, 3, 4, 5].map(i => (
                  <div key={i} className="flex items-center gap-3 px-4 py-3 border-b border-warm-gray animate-pulse">
                    <div className="w-2 flex-shrink-0"></div>
                    <div className="w-10 h-10 bg-warm-gray flex-shrink-0"></div>
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-warm-gray w-3/4"></div>
                      <div className="h-3 bg-warm-gray w-1/2"></div>
                    </div>
                    <div className="w-10 h-6 bg-warm-gray flex-shrink-0"></div>
                    <div className="w-20 h-6 bg-warm-gray flex-shrink-0"></div>
                    <div className="w-12 h-4 bg-warm-gray flex-shrink-0"></div>
                    <div className="w-4 flex-shrink-0"></div>
                  </div>
                ))}
              </div>
            ) : allApplications.length === 0 ? (
              <div className="bg-parchment border border-warm-gray p-12 text-center">
                <Briefcase size={48} className="mx-auto mb-4 text-slate" />
                <p className="text-slate font-body">No applications found. Click "Scan" to fetch job alerts or use the browser extension to add applications.</p>
              </div>
            ) : (
              <div className="bg-parchment border border-warm-gray overflow-hidden">
                {/* List Header */}
                <div className="flex items-center gap-3 px-4 py-2 bg-warm-gray/50 border-b border-warm-gray text-xs font-body uppercase tracking-wide text-slate">
                  <div className="w-2 flex-shrink-0"></div>
                  <div className="w-10 flex-shrink-0"></div>
                  <div className="flex-1 min-w-0">Job</div>
                  <button
                    onClick={() => setFilter({ ...filter, sort: filter.sort === 'score' ? 'score-low' : 'score' })}
                    className="w-10 flex-shrink-0 flex items-center justify-center gap-0.5 hover:text-copper transition-colors cursor-pointer"
                  >
                    Score
                    {filter.sort === 'score' && <ChevronDown size={12} />}
                    {filter.sort === 'score-low' && <ChevronUp size={12} />}
                    {!filter.sort.startsWith('score') && <ArrowUpDown size={10} className="opacity-50" />}
                  </button>
                  <button
                    onClick={() => setFilter({ ...filter, sort: filter.sort === 'status' ? 'status-desc' : 'status' })}
                    className="w-24 flex-shrink-0 flex items-center gap-0.5 hover:text-copper transition-colors cursor-pointer"
                  >
                    Status
                    {filter.sort === 'status' && <ChevronUp size={12} />}
                    {filter.sort === 'status-desc' && <ChevronDown size={12} />}
                    {!filter.sort.startsWith('status') && <ArrowUpDown size={10} className="opacity-50" />}
                  </button>
                  <button
                    onClick={() => setFilter({ ...filter, sort: filter.sort === 'date' ? 'date-oldest' : 'date' })}
                    className="w-12 flex-shrink-0 flex items-center justify-end gap-0.5 hover:text-copper transition-colors cursor-pointer"
                  >
                    Date
                    {filter.sort === 'date' && <ChevronDown size={12} />}
                    {filter.sort === 'date-oldest' && <ChevronUp size={12} />}
                    {!filter.sort.startsWith('date') && <ArrowUpDown size={10} className="opacity-50" />}
                  </button>
                  <div className="w-4 flex-shrink-0"></div>
                </div>

                {/* Job Rows */}
                {allApplications
                  .filter(app => {
                    // Apply app_type filter
                    if (filter.app_type && filter.app_type !== 'all' && app.app_type !== filter.app_type) return false;

                    // Apply status filter
                    if (filter.status && app.display_status !== filter.status) return false;

                    // Apply score filter (only for discovered jobs)
                    if (app.app_type === 'discovered' && app.score < filter.minScore) return false;

                    // Apply search filter
                    if (filter.search) {
                      const search = filter.search.toLowerCase();
                      const matches =
                        app.title?.toLowerCase().includes(search) ||
                        app.company?.toLowerCase().includes(search);
                      if (!matches) return false;
                    }

                    return true;
                  })
                  .map((app, index) => {
                    // Render JobRow for discovered jobs
                    if (app.app_type === 'discovered') {
                      return (
                        <JobRow
                          key={app.job_id}
                          job={app}
                          isSelected={index === selectedJobIndex}
                        />
                      );
                    } else {
                      // External applications still use the card view for now
                      return (
                        <ExternalApplicationCard
                          key={app.app_id}
                          app={app}
                          expanded={expandedJob === app.app_id}
                          onToggle={() => setExpandedJob(expandedJob === app.app_id ? null : app.app_id)}
                          onStatusChange={handleExternalStatusChange}
                          onDelete={handleDeleteExternal}
                        />
                      );
                    }
                  })}
              </div>
            )}
          </>
        ) : activeView === 'resumes' ? (
          <>
            {/* Resumes View */}
            <div className="flex justify-between items-center mb-6">
              <h2 className="font-display text-xl text-ink">Resume Library</h2>
              <button
                onClick={() => setShowResumeModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-copper text-parchment rounded-none uppercase tracking-wide text-sm font-body font-semibold hover:bg-copper/90 active:translate-y-px transition-all"
              >
                <Plus size={18} />
                Add Resume
              </button>
            </div>

            {resumes.length === 0 ? (
              <div className="text-center py-12">
                <FileText size={48} className="mx-auto mb-4 text-slate" />
                <p className="text-slate mb-4">No resumes in your library yet.</p>
                <p className="text-sm text-slate mb-6">Add your first resume to get AI-powered job-resume matching!</p>
                <button
                  onClick={() => setShowResumeModal(true)}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-copper text-parchment rounded-none uppercase tracking-wide text-sm font-body font-semibold hover:bg-copper/90 active:translate-y-px transition-all"
                >
                  <Upload size={20} />
                  Upload Your First Resume
                </button>
              </div>
            ) : (
              <>
                <div className="mb-4 p-4 bg-warm-gray/50 border border-warm-gray border-l-[3px] border-l-copper">
                  <h3 className="font-body font-semibold text-ink mb-2">Library Stats</h3>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-2xl font-mono font-bold text-ink">{resumes.length}</div>
                      <div className="text-slate text-xs uppercase tracking-wide">Total Resumes</div>
                    </div>
                    <div>
                      <div className="text-2xl font-mono font-bold text-ink">
                        {resumes.reduce((sum, r) => sum + (r.usage_count || 0), 0)}
                      </div>
                      <div className="text-slate text-xs uppercase tracking-wide">Total Recommendations</div>
                    </div>
                    <div>
                      <div className="text-2xl font-mono font-bold text-ink">
                        {resumes.filter(r => r.usage_count > 0).length}
                      </div>
                      <div className="text-slate text-xs uppercase tracking-wide">Used Resumes</div>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  {resumes.map(resume => (
                    <ResumeCard
                      key={resume.resume_id}
                      resume={resume}
                      expanded={expandedJob === resume.resume_id}
                      onToggle={() => setExpandedJob(expandedJob === resume.resume_id ? null : resume.resume_id)}
                      onEdit={(resume) => setEditingResume(resume)}
                      onDelete={handleDeleteResume}
                      onResearch={handleResearchForResume}
                    />
                  ))}
                </div>
              </>
            )}
          </>
        ) : activeView === 'followups' ? (
          <>
            {/* Follow-ups View */}
            <div className="space-y-6">
              {/* Header with scan button */}
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                  <h2 className="font-display text-xl text-ink">Follow-ups</h2>
                  <p className="font-body text-sm text-slate mt-1">
                    Track interview responses, rejections, and application confirmations
                  </p>
                </div>
                <button
                  onClick={handleScanFollowups}
                  disabled={scanningFollowups}
                  className="flex items-center gap-2 px-4 py-2 bg-copper text-parchment rounded-none uppercase tracking-wide text-sm font-body font-semibold hover:bg-copper/90 active:translate-y-px transition-all disabled:opacity-50"
                >
                  {scanningFollowups ? (
                    <>
                      <RefreshCw size={16} className="animate-spin" />
                      Scanning...
                    </>
                  ) : (
                    <>
                      <Mail size={16} />
                      Scan Follow-ups
                    </>
                  )}
                </button>
              </div>

              {/* Stats Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
                <div className="bg-parchment border border-warm-gray p-4 rounded-sm">
                  <div className="flex items-center gap-2 text-slate text-xs uppercase tracking-wide mb-1">
                    <Mail size={14} />
                    Total
                  </div>
                  <div className="font-mono text-2xl text-ink">{followupStats.total}</div>
                </div>
                <div className="bg-patina/10 border border-patina/30 p-4 rounded-sm">
                  <div className="flex items-center gap-2 text-patina text-xs uppercase tracking-wide mb-1">
                    <Briefcase size={14} />
                    Interviews
                  </div>
                  <div className="font-mono text-2xl text-patina">{followupStats.interviews}</div>
                </div>
                <div className="bg-copper/10 border border-copper/30 p-4 rounded-sm">
                  <div className="flex items-center gap-2 text-copper text-xs uppercase tracking-wide mb-1">
                    <Star size={14} />
                    Offers
                  </div>
                  <div className="font-mono text-2xl text-copper">{followupStats.offers}</div>
                </div>
                <div className="bg-rust/10 border border-rust/30 p-4 rounded-sm">
                  <div className="flex items-center gap-2 text-rust text-xs uppercase tracking-wide mb-1">
                    <XCircle size={14} />
                    Rejections
                  </div>
                  <div className="font-mono text-2xl text-rust">{followupStats.rejections}</div>
                </div>
                <div className="bg-cream/10 border border-cream/30 p-4 rounded-sm">
                  <div className="flex items-center gap-2 text-ink text-xs uppercase tracking-wide mb-1">
                    <FileText size={14} />
                    Assessments
                  </div>
                  <div className="font-mono text-2xl text-ink">{followupStats.assessments}</div>
                </div>
              </div>

              {/* Follow-ups List */}
              {followupsLoading ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw size={24} className="animate-spin text-copper" />
                </div>
              ) : followups.length === 0 ? (
                <div className="bg-parchment border border-warm-gray rounded-sm p-12 text-center">
                  <Mail size={48} className="mx-auto mb-4 text-slate opacity-50" />
                  <h3 className="font-display text-xl text-ink mb-2">No Follow-ups Yet</h3>
                  <p className="font-body text-slate mb-6">
                    Click "Scan Follow-ups" to check your Gmail for application responses,
                    interview invitations, and other follow-up emails.
                  </p>
                  <button
                    onClick={handleScanFollowups}
                    disabled={scanningFollowups}
                    className="inline-flex items-center gap-2 px-6 py-3 bg-copper text-parchment rounded-none uppercase tracking-wide text-sm font-body font-semibold hover:bg-copper/90 active:translate-y-px transition-all disabled:opacity-50"
                  >
                    <Mail size={18} />
                    Scan Follow-ups
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {/* Group followups by company */}
                  {Object.entries(
                    followups.reduce((acc, f) => {
                      const company = f.company || 'Unknown Company';
                      if (!acc[company]) acc[company] = [];
                      acc[company].push(f);
                      return acc;
                    }, {})
                  )
                    .sort(([, a], [, b]) => {
                      // Sort by most recent email date
                      const dateA = new Date(a[0]?.email_date || 0);
                      const dateB = new Date(b[0]?.email_date || 0);
                      return dateB - dateA;
                    })
                    .map(([company, companyFollowups]) => (
                      <div key={company} className="bg-parchment border border-warm-gray rounded-sm overflow-hidden">
                        {/* Company Header */}
                        <div className="px-5 py-4 bg-warm-gray/20 border-b border-warm-gray flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <Building2 size={18} className="text-copper" />
                            <h3 className="font-body font-semibold text-ink">{company}</h3>
                            <span className="text-xs text-slate bg-warm-gray/50 px-2 py-0.5 rounded-sm">
                              {companyFollowups.length} email{companyFollowups.length !== 1 ? 's' : ''}
                            </span>
                          </div>
                          {companyFollowups[0]?.job_title && (
                            <span className="text-sm text-slate">{companyFollowups[0].job_title}</span>
                          )}
                        </div>

                        {/* Company's Follow-up Emails */}
                        <div className="divide-y divide-warm-gray">
                          {companyFollowups
                            .sort((a, b) => new Date(b.email_date) - new Date(a.email_date))
                            .map((followup) => (
                              <div
                                key={followup.id}
                                className={`p-5 hover:bg-warm-gray/10 transition-colors border-l-4 ${
                                  followup.type === 'interview' ? 'border-l-patina' :
                                  followup.type === 'offer' ? 'border-l-copper' :
                                  followup.type === 'rejection' ? 'border-l-rust' :
                                  followup.type === 'assessment' ? 'border-l-cream' :
                                  'border-l-slate'
                                }`}
                              >
                                <div className="flex items-start justify-between gap-4">
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-2">
                                      <span className={`text-xs px-2 py-1 rounded-sm font-medium uppercase tracking-wide ${
                                        followup.type === 'interview' ? 'bg-patina/15 text-patina' :
                                        followup.type === 'offer' ? 'bg-copper/15 text-copper' :
                                        followup.type === 'rejection' ? 'bg-rust/15 text-rust' :
                                        followup.type === 'assessment' ? 'bg-cream/15 text-ink' :
                                        'bg-slate/15 text-slate'
                                      }`}>
                                        {followup.type || 'update'}
                                      </span>
                                      <span className="text-xs text-slate">
                                        {followup.email_date ? new Date(followup.email_date).toLocaleDateString('en-US', {
                                          month: 'short',
                                          day: 'numeric',
                                          year: 'numeric'
                                        }) : ''}
                                      </span>
                                    </div>
                                    <p className="text-sm text-ink font-body font-medium mb-1">
                                      {followup.subject}
                                    </p>
                                    {followup.snippet && (
                                      <p className="text-sm text-slate font-body leading-relaxed">
                                        {followup.snippet}
                                      </p>
                                    )}
                                    {followup.sender_email && (
                                      <p className="text-xs text-slate mt-2">
                                        From: {followup.sender_email}
                                      </p>
                                    )}
                                  </div>
                                  {followup.job_id && (
                                    <button
                                      onClick={() => navigate(`/jobs/${followup.job_id}`)}
                                      className="flex-shrink-0 text-xs text-copper hover:text-copper/80 flex items-center gap-1 px-2 py-1 bg-copper/10 rounded-sm transition-colors"
                                    >
                                      <ExternalLink size={12} />
                                      View Job
                                    </button>
                                  )}
                                </div>
                              </div>
                            ))}
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </div>
          </>
        ) : activeView === 'achievements' ? (
          <AchievementsView />
        ) : activeView === 'analytics' ? (
          <AnalyticsView />
        ) : activeView === 'templates' ? (
          <EmailTemplatesView />
        ) : activeView === 'companies' ? (
          <>
            {/* Tracked Companies View */}
            <div className="flex justify-between items-center mb-6">
              <h2 className="font-display text-xl text-ink">Tracked Companies</h2>
              <button
                onClick={() => setShowAddCompany(!showAddCompany)}
                className="flex items-center gap-2 px-4 py-2 bg-copper text-parchment rounded-none uppercase tracking-wide text-sm font-body font-semibold hover:bg-copper/90 active:translate-y-px transition-all"
              >
                <Plus size={18} />
                {showAddCompany ? 'Cancel' : 'Add Company'}
              </button>
            </div>

            {showAddCompany && (
              <div className="bg-parchment border border-warm-gray p-6 mb-6">
                <h3 className="font-body font-semibold text-ink mb-4">Add Tracked Company</h3>
                <form onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.target);
                  handleAddTrackedCompany({
                    company_name: formData.get('company_name'),
                    career_page_url: formData.get('career_page_url'),
                    job_alert_email: formData.get('job_alert_email'),
                    notes: formData.get('notes'),
                  });
                  e.target.reset();
                }}>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-body font-medium text-ink mb-1">
                        Company Name <span className="text-rust">*</span>
                      </label>
                      <input
                        type="text"
                        name="company_name"
                        required
                        className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-ink font-body placeholder-slate focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none"
                        placeholder="e.g., Google, Microsoft, Startup Inc."
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-body font-medium text-ink mb-1">
                        Career Page URL
                      </label>
                      <input
                        type="url"
                        name="career_page_url"
                        className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-ink font-body placeholder-slate focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none"
                        placeholder="https://company.com/careers"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-body font-medium text-ink mb-1">
                        Job Alert Email
                      </label>
                      <input
                        type="email"
                        name="job_alert_email"
                        className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-ink font-body placeholder-slate focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none"
                        placeholder="jobs@company.com"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-body font-medium text-ink mb-1">
                        Notes
                      </label>
                      <textarea
                        name="notes"
                        rows="3"
                        className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-ink font-body placeholder-slate focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none resize-y"
                        placeholder="Add any notes about this company..."
                      />
                    </div>
                    <div className="flex gap-2">
                      <button
                        type="submit"
                        className="px-4 py-2 bg-copper text-parchment rounded-none uppercase tracking-wide text-sm font-body font-semibold hover:bg-copper/90 active:translate-y-px transition-all"
                      >
                        Add Company
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowAddCompany(false)}
                        className="px-4 py-2 bg-transparent border border-warm-gray text-slate rounded-none uppercase tracking-wide text-sm font-body hover:bg-warm-gray/50 transition-all"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </form>
              </div>
            )}

            {trackedCompanies.length === 0 ? (
              <div className="text-center py-12">
                <Briefcase size={48} className="mx-auto mb-4 text-slate" />
                <p className="text-slate mb-4">No tracked companies yet.</p>
                <p className="text-sm text-slate mb-6">
                  Track companies you're interested in with their career pages and job alert emails.
                </p>
                <button
                  onClick={() => setShowAddCompany(true)}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-copper text-parchment rounded-none uppercase tracking-wide text-sm font-body font-semibold hover:bg-copper/90 active:translate-y-px transition-all"
                >
                  <Plus size={20} />
                  Add Your First Company
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {trackedCompanies.map(company => (
                  <div key={company.id} className="bg-parchment border border-warm-gray p-4 hover:border-copper transition-colors">
                    {editingCompany === company.id ? (
                      <form onSubmit={(e) => {
                        e.preventDefault();
                        const formData = new FormData(e.target);
                        handleUpdateTrackedCompany(company.id, {
                          company_name: formData.get('company_name'),
                          career_page_url: formData.get('career_page_url'),
                          job_alert_email: formData.get('job_alert_email'),
                          notes: formData.get('notes'),
                        });
                      }}>
                        <div className="space-y-3">
                          <input
                            type="text"
                            name="company_name"
                            defaultValue={company.company_name}
                            required
                            className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-ink font-body font-semibold placeholder-slate focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none"
                            placeholder="Company Name"
                          />
                          <input
                            type="url"
                            name="career_page_url"
                            defaultValue={company.career_page_url || ''}
                            className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-ink font-body text-sm placeholder-slate focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none"
                            placeholder="Career Page URL"
                          />
                          <input
                            type="email"
                            name="job_alert_email"
                            defaultValue={company.job_alert_email || ''}
                            className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-ink font-body text-sm placeholder-slate focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none"
                            placeholder="Job Alert Email"
                          />
                          <textarea
                            name="notes"
                            defaultValue={company.notes || ''}
                            rows="2"
                            className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-ink font-body text-sm placeholder-slate focus:border-b-copper focus:bg-warm-gray/50 transition-colors outline-none resize-y"
                            placeholder="Notes"
                          />
                          <div className="flex gap-2">
                            <button
                              type="submit"
                              className="px-3 py-1.5 bg-copper text-parchment text-sm rounded-none uppercase tracking-wide font-body hover:bg-copper/90 transition-all"
                            >
                              Save
                            </button>
                            <button
                              type="button"
                              onClick={() => setEditingCompany(null)}
                              className="px-3 py-1.5 bg-transparent border border-warm-gray text-slate text-sm rounded-none uppercase tracking-wide font-body hover:bg-warm-gray/50 transition-all"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      </form>
                    ) : (
                      <>
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <h3 className="font-body font-semibold text-ink text-lg mb-2">{company.company_name}</h3>
                            <div className="space-y-1 text-sm text-slate">
                              {company.career_page_url && (
                                <div className="flex items-center gap-2">
                                  <ExternalLink size={14} />
                                  <a
                                    href={company.career_page_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-copper hover:underline"
                                  >
                                    {company.career_page_url}
                                  </a>
                                </div>
                              )}
                              {company.job_alert_email && (
                                <div className="flex items-center gap-2">
                                  <Mail size={14} />
                                  <a
                                    href={`mailto:${company.job_alert_email}`}
                                    className="text-blue-600 dark:text-blue-400 hover:underline"
                                  >
                                    {company.job_alert_email}
                                  </a>
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => setEditingCompany(company.id)}
                              className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                              title="Edit"
                            >
                              <Edit2 size={16} />
                            </button>
                            <button
                              onClick={() => {
                                if (confirm(`Delete ${company.company_name}?`)) {
                                  handleDeleteTrackedCompany(company.id);
                                }
                              }}
                              className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
                              title="Delete"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </div>
                        {company.notes && (
                          <div className="mt-2 p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
                            <p className="text-sm text-gray-700 dark:text-gray-300">{company.notes}</p>
                          </div>
                        )}
                        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
                          Added: {new Date(company.created_at).toLocaleDateString()}
                        </div>
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        ) : activeView === 'roadmap' ? (
          <>
            {/* Roadmap View */}
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">🗺️ Product Roadmap</h2>
              <p className="text-gray-600 dark:text-gray-400">Track feature progress and planned improvements for Hammy the Hire Tracker</p>
            </div>

            {/* Progress Overview */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-gradient-to-br from-teal-50 to-teal-100 rounded-lg p-4 border border-teal-200">
                <div className="text-3xl font-bold text-teal-700">3%</div>
                <div className="text-sm text-teal-800 font-medium">Overall Complete</div>
              </div>
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
                <div className="text-3xl font-bold text-blue-700">31</div>
                <div className="text-sm text-blue-800 font-medium">Total Features</div>
              </div>
              <div className="bg-gradient-to-br from-pink-50 to-pink-100 rounded-lg p-4 border border-pink-200">
                <div className="text-3xl font-bold text-pink-700">7</div>
                <div className="text-sm text-pink-800 font-medium">Quick Wins</div>
              </div>
            </div>

            {/* Roadmap Sections */}
            <div className="space-y-6">
              {/* Critical - Must Have */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-red-200 dark:border-red-800 overflow-hidden">
                <div className="bg-gradient-to-r from-red-50 to-red-100 dark:from-red-900/30 dark:to-red-800/30 px-4 py-3 border-b border-red-200 dark:border-red-800">
                  <h3 className="font-bold text-red-900 dark:text-red-300 flex items-center gap-2">
                    🚨 CRITICAL - Must Have Before Test Users
                    <span className="text-xs bg-red-200 dark:bg-red-900/50 text-red-800 dark:text-red-200 px-2 py-1 rounded-full">P0</span>
                  </h3>
                </div>
                <div className="p-4 space-y-2 text-sm">
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900 dark:text-gray-100">Authentication & Multi-User Support</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">User registration, login, session management, user isolation</div>
                      <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">Effort: 2-3 weeks</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900 dark:text-gray-100">Database & Hosting</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">Migrate to PostgreSQL, deploy backend/frontend, environment management</div>
                      <div className="text-xs text-gray-500 mt-1">Effort: 1 week</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900 dark:text-gray-100">API Key Management</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">Secure storage, rate limiting, cost tracking, BYOK decision</div>
                      <div className="text-xs text-gray-500 mt-1">Effort: 3-5 days</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900 dark:text-gray-100">Gmail OAuth Per User</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">OAuth flow, token storage, refresh handling per user</div>
                      <div className="text-xs text-gray-500 mt-1">Effort: 2-3 days</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900 dark:text-gray-100">Domain & SSL</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">Purchase domain, SSL certificate, configure DNS, update OAuth redirects</div>
                      <div className="text-xs text-gray-500 mt-1">Effort: 4 hours</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Wins - In Progress */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-blue-200 dark:border-blue-800 overflow-hidden">
                <div className="bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 px-4 py-3 border-b border-blue-200 dark:border-blue-800">
                  <h3 className="font-bold text-blue-900 dark:text-blue-300 flex items-center gap-2">
                    🎯 Quick Wins - Easy but Impactful
                    <span className="text-xs bg-blue-200 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200 px-2 py-1 rounded-full">In Progress</span>
                  </h3>
                </div>
                <div className="p-4 space-y-2 text-sm">
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" defaultChecked />
                    <div className="opacity-60">
                      <div className="font-medium text-gray-900 dark:text-gray-100 line-through">Create Roadmap Page</div>
                      <div className="text-xs text-teal-600 dark:text-teal-400">✓ Completed</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900 dark:text-gray-100">Custom Email Sources (User-Defined) ⚡</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">UI to add custom job board email patterns with AI assistance</div>
                      <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">🔄 Starting Now - Effort: 2-3 days</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900 dark:text-gray-100">Dark Mode</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">Toggle in settings, respect system preference</div>
                      <div className="text-xs text-gray-500 mt-1">Effort: 1 day</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900 dark:text-gray-100">Keyboard Shortcuts</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">J/K navigation, / search, Enter open, D delete, ? help</div>
                      <div className="text-xs text-gray-500 mt-1">Effort: 4 hours</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900 dark:text-gray-100">Job Notes</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">Quick notes field, interview date, key takeaways</div>
                      <div className="text-xs text-gray-500 mt-1">Effort: 2 hours</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900 dark:text-gray-100">Better Empty States & Loading</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">Skeleton loaders, progress bars, toast notifications</div>
                      <div className="text-xs text-gray-500 mt-1">Effort: 1 day</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900 dark:text-gray-100">Enhanced Deduplication</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">Fuzzy matching, show similar jobs, manual merge</div>
                      <div className="text-xs text-gray-500 mt-1">Effort: 2 days</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* UX/Onboarding */}
              <div className="bg-white rounded-lg shadow-sm border border-purple-200 overflow-hidden">
                <div className="bg-gradient-to-r from-purple-50 to-purple-100 px-4 py-3 border-b border-purple-200">
                  <h3 className="font-bold text-purple-900 flex items-center gap-2">
                    🎨 UX/Onboarding - High Priority
                    <span className="text-xs bg-purple-200 text-purple-800 px-2 py-1 rounded-full">P1</span>
                  </h3>
                </div>
                <div className="p-4 space-y-2 text-sm">
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900">Welcome/Onboarding Flow</div>
                      <div className="text-xs text-gray-600">Landing page, sign up flow, welcome wizard, interactive tutorial</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900">How-To Guide / Documentation</div>
                      <div className="text-xs text-gray-600">/help page with getting started, FAQs, troubleshooting</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Legal & Trust */}
              <div className="bg-white rounded-lg shadow-sm border border-amber-200 overflow-hidden">
                <div className="bg-gradient-to-r from-amber-50 to-amber-100 px-4 py-3 border-b border-amber-200">
                  <h3 className="font-bold text-amber-900 flex items-center gap-2">
                    📄 Legal & Trust - Required for Test Users
                    <span className="text-xs bg-amber-200 text-amber-800 px-2 py-1 rounded-full">P0</span>
                  </h3>
                </div>
                <div className="p-4 space-y-2 text-sm">
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900">Privacy Policy</div>
                      <div className="text-xs text-gray-600">Data collection, usage, third-party services, retention</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900">Terms of Service</div>
                      <div className="text-xs text-gray-600">Acceptable use, service availability, liability limitations</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900">Data Export/Delete (GDPR)</div>
                      <div className="text-xs text-gray-600">Export button, delete account flow, automated deletion</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Feature Improvements */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-4 py-3 border-b border-gray-200">
                  <h3 className="font-bold text-gray-900 flex items-center gap-2">
                    ✨ Feature Improvements - Nice to Have
                    <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded-full">P3</span>
                  </h3>
                </div>
                <div className="p-4 space-y-1 text-sm text-gray-700">
                  <div>• Advanced Search & Filters (salary, date, company size, keywords)</div>
                  <div>• Job Application Timeline (visual timeline, Kanban board, funnel analytics)</div>
                  <div>• Interview Management (scheduler, prep notes, calendar integration)</div>
                  <div>• Company Intelligence (auto-fetch info, ratings, news, employee connections)</div>
                  <div>• Networking Tracker (contact management, interaction history, reminders)</div>
                  <div>• Analytics Dashboard (success rate, response times, application velocity)</div>
                  <div>• Status Automation (auto-move based on email patterns)</div>
                  <div>• Email Templates (thank you, follow-up, withdrawal, acceptance)</div>
                  <div>• Mobile Responsiveness (responsive design, touch-friendly UI)</div>
                </div>
              </div>

              {/* View Full Roadmap */}
              <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-6 border border-blue-200 text-center">
                <h3 className="font-bold text-blue-900 mb-2">📋 Full Roadmap Document</h3>
                <p className="text-sm text-blue-800 mb-4">
                  See the complete roadmap with detailed descriptions, technical approaches, and timelines in the ROADMAP.md file.
                </p>
                <a
                  href="https://github.com/creavill/Henry-the-Hire-Tracker/blob/main/ROADMAP.md"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-copper text-parchment rounded-none uppercase tracking-wide text-sm font-body font-semibold hover:bg-copper/90 transition-all"
                >
                  <ExternalLink size={16} />
                  View ROADMAP.md on GitHub
                </a>
              </div>

              {/* Current Sprint */}
              <div className="bg-warm-gray/50 border border-warm-gray border-l-[3px] border-l-copper p-6">
                <h3 className="font-body font-bold text-ink mb-3">Current Sprint (This Week)</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2 text-ink">
                    <CheckCircle size={16} className="text-patina" />
                    <span className="font-medium">Create Roadmap Page - DONE</span>
                  </div>
                  <div className="flex items-center gap-2 text-ink">
                    <Clock size={16} className="text-copper" />
                    <span className="font-medium">Implement Custom Email Sources UI</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate">
                    <Clock size={16} className="text-slate" />
                    <span>Add Dark Mode Toggle</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate">
                    <Clock size={16} className="text-slate" />
                    <span>Add Keyboard Shortcuts</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate">
                    <Clock size={16} className="text-slate" />
                    <span>Add Job Notes Field</span>
                  </div>
                </div>
              </div>
            </div>
          </>
        ) : (
          <>
            {/* Settings View */}
            <div className="mb-6">
              <h2 className="font-display text-2xl text-ink mb-2">Settings</h2>
              <p className="text-slate">Configure custom email sources and application preferences</p>
            </div>

            {/* Dark Mode Section */}
            <div className="bg-parchment border border-warm-gray overflow-hidden mb-6">
              <div className="bg-warm-gray/50 px-4 py-3 border-b border-warm-gray border-l-[3px] border-l-slate">
                <h3 className="font-body font-bold text-ink">Appearance</h3>
                <p className="text-sm text-slate mt-1">
                  Customize how Hammy looks
                </p>
              </div>

              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-body font-semibold text-ink">Dark Mode</h4>
                    <p className="text-sm text-slate mt-1">
                      {darkMode ? 'Currently using dark theme' : 'Currently using light theme'}
                    </p>
                  </div>
                  <button
                    onClick={() => setDarkMode(!darkMode)}
                    className={`relative inline-flex h-8 w-14 items-center transition-colors duration-200 focus:outline-none ${
                      darkMode ? 'bg-copper' : 'bg-warm-gray'
                    }`}
                  >
                    <span
                      className={`inline-block h-6 w-6 transform bg-parchment transition-transform duration-200 ${
                        darkMode ? 'translate-x-7' : 'translate-x-1'
                      }`}
                    >
                      <span className="flex items-center justify-center h-full text-xs">
                        {darkMode ? 'D' : 'L'}
                      </span>
                    </span>
                  </button>
                </div>
              </div>
            </div>

            {/* Email Sources Section */}
            <EmailSourcesSettings showToast={showToast} />

            {/* AI Provider Settings Section */}
            <AIProviderSettings showToast={showToast} />

            {/* Debug Tools Section */}
            <div className="bg-parchment border border-warm-gray overflow-hidden mb-6">
              <div className="bg-warm-gray/50 px-4 py-3 border-b border-warm-gray border-l-[3px] border-l-rust">
                <h3 className="font-body font-bold text-ink flex items-center gap-2">
                  <AlertCircle size={18} className="text-rust" />
                  Debug Tools
                </h3>
                <p className="text-sm text-slate mt-1">
                  Test email processing pipeline with verbose logging
                </p>
              </div>

              <div className="p-4">
                <div className="flex items-center gap-3 mb-4">
                  <button
                    onClick={handleDebugScan}
                    disabled={debugScanning}
                    className="flex items-center gap-2 px-4 py-2 bg-rust text-parchment text-sm uppercase tracking-wide font-semibold hover:bg-rust/90 disabled:opacity-50 transition-colors"
                  >
                    <RefreshCw size={16} className={debugScanning ? 'animate-spin' : ''} />
                    {debugScanning ? 'Scanning...' : 'Debug Scan (Last 40 Emails)'}
                  </button>
                  {debugResults && (
                    <button
                      onClick={downloadDebugLog}
                      className="flex items-center gap-2 px-4 py-2 border border-warm-gray text-ink text-sm uppercase tracking-wide font-semibold hover:bg-warm-gray/50 transition-colors"
                    >
                      <FileText size={16} />
                      Download Log
                    </button>
                  )}
                </div>

                {debugResults && (
                  <div className="space-y-3">
                    <div className="text-sm text-slate">
                      Processed <strong className="text-ink">{debugResults.emails_processed}</strong> emails
                      {debugResults.log_file && (
                        <span className="ml-2">| Log saved to: <code className="text-xs bg-warm-gray/50 px-1 py-0.5">{debugResults.log_file}</code></span>
                      )}
                    </div>

                    {/* Per-email results */}
                    <div className="space-y-2 max-h-[600px] overflow-y-auto">
                      {debugResults.results?.map((email, i) => (
                        <details key={email.msg_id || i} className="border border-warm-gray">
                          <summary className="px-3 py-2 bg-warm-gray/20 cursor-pointer hover:bg-warm-gray/40 transition-colors">
                            <span className="font-body font-semibold text-sm text-ink">
                              #{email.index} {email.subject || '(no subject)'}
                            </span>
                            <span className="ml-2 text-xs">
                              {email.classification && (
                                <span className={`inline-block px-1.5 py-0.5 uppercase tracking-wide font-semibold ${
                                  email.classification === 'rejection' ? 'bg-rust/20 text-rust' :
                                  email.classification === 'interview' ? 'bg-patina/20 text-patina' :
                                  email.classification === 'offer' ? 'bg-patina/30 text-patina' :
                                  email.classification === 'received' ? 'bg-copper/20 text-copper' :
                                  'bg-warm-gray/30 text-slate'
                                }`}>
                                  {email.classification}
                                </span>
                              )}
                              {email.matches_known_source && (
                                <span className="inline-block ml-1 px-1.5 py-0.5 bg-patina/20 text-patina uppercase tracking-wide font-semibold">
                                  source match
                                </span>
                              )}
                              {email.already_processed && (
                                <span className="inline-block ml-1 px-1.5 py-0.5 bg-warm-gray/40 text-slate uppercase tracking-wide font-semibold">
                                  already processed
                                </span>
                              )}
                            </span>
                          </summary>
                          <div className="px-3 py-2 text-xs font-mono space-y-1 bg-parchment">
                            <div><span className="text-slate">From:</span> <span className="text-ink">{email.from}</span></div>
                            <div><span className="text-slate">Sender:</span> <span className="text-ink">{email.sender}</span></div>
                            <div><span className="text-slate">Display Name:</span> <span className="text-ink">{email.display_name}</span></div>
                            <div><span className="text-slate">Date:</span> <span className="text-ink">{email.date}</span></div>
                            <div><span className="text-slate">Classification:</span> <span className="text-ink font-bold">{email.classification}</span></div>
                            <div><span className="text-slate">Company:</span> <span className="text-ink">{email.company}</span></div>
                            <div><span className="text-slate">Role:</span> <span className="text-ink">{email.role || '(none extracted)'}</span></div>
                            <div><span className="text-slate">Matches Source:</span> <span className="text-ink">{email.matches_known_source ? `Yes (${email.matched_source})` : 'No'}</span></div>
                            <div><span className="text-slate">Body Length:</span> <span className="text-ink">{email.body_length} chars</span></div>
                            {email.ai_score !== undefined && (
                              <>
                                <div className="mt-1 pt-1 border-t border-warm-gray/50">
                                  <span className="text-slate">AI Keep:</span> <span className="text-ink">{email.ai_keep ? 'Yes' : 'No'}</span>
                                </div>
                                <div><span className="text-slate">AI Score:</span> <span className="text-ink">{email.ai_score}</span></div>
                                <div><span className="text-slate">AI Reason:</span> <span className="text-ink">{email.ai_reason}</span></div>
                              </>
                            )}
                            {email.ai_error && (
                              <div className="text-rust"><span className="text-slate">AI Error:</span> {email.ai_error}</div>
                            )}
                            {email.snippet && (
                              <div className="mt-1 pt-1 border-t border-warm-gray/50">
                                <span className="text-slate">Snippet:</span>
                                <div className="text-ink mt-0.5 whitespace-pre-wrap">{email.snippet}</div>
                              </div>
                            )}
                            {email.body_preview && (
                              <div className="mt-1 pt-1 border-t border-warm-gray/50">
                                <span className="text-slate">Body Preview:</span>
                                <div className="text-ink mt-0.5 whitespace-pre-wrap max-h-40 overflow-y-auto">{email.body_preview}</div>
                              </div>
                            )}
                            {email.error && (
                              <div className="text-rust mt-1"><span className="text-slate">Error:</span> {email.error}</div>
                            )}
                          </div>
                        </details>
                      ))}
                    </div>

                    {/* Raw log content */}
                    {debugResults.log_content && (
                      <details className="border border-warm-gray">
                        <summary className="px-3 py-2 bg-warm-gray/20 cursor-pointer hover:bg-warm-gray/40 transition-colors font-body font-semibold text-sm text-ink">
                          Full Log Output
                        </summary>
                        <pre className="px-3 py-2 text-xs font-mono text-ink whitespace-pre-wrap max-h-96 overflow-y-auto bg-parchment">
                          {debugResults.log_content}
                        </pre>
                      </details>
                    )}
                  </div>
                )}

                {!debugResults && !debugScanning && (
                  <p className="text-sm text-slate">
                    Click "Debug Scan" to fetch your 40 most recent emails and process them through
                    the full pipeline with verbose logging. This helps diagnose classification,
                    company extraction, and scoring issues. A log file will be saved for review.
                  </p>
                )}
              </div>
            </div>

            {/* Operation Logs Section */}
            <LogsViewer />
          </>
        )
          } />
        </Routes>
      </main>
      </div>

      {/* Resume Upload Modal */}
      {showResumeModal && (
        <ResumeUploadModal
          onClose={() => setShowResumeModal(false)}
          onSave={fetchResumes}
        />
      )}

      {/* Resume Edit Modal */}
      {editingResume && (
        <ResumeEditModal
          resume={editingResume}
          onClose={() => setEditingResume(null)}
          onSave={fetchResumes}
        />
      )}

      {/* Toast Notifications */}
      <div className="fixed bottom-4 right-4 z-50 space-y-2">
        {toasts.map(toast => (
          <div
            key={toast.id}
            className={`px-4 py-3 shadow-lg text-parchment font-body transform transition-all duration-300 animate-slide-in border-l-[3px] ${
              toast.type === 'success' ? 'bg-patina border-l-patina' :
              toast.type === 'error' ? 'bg-rust border-l-rust' :
              toast.type === 'warning' ? 'bg-cream text-ink border-l-cream' :
              'bg-copper border-l-copper'
            }`}
          >
            <div className="flex items-center gap-2">
              {toast.type === 'success' && <CheckCircle size={20} />}
              {toast.type === 'error' && <AlertCircle size={20} />}
              <span>{toast.message}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Keyboard Shortcuts Help Modal */}
      {showShortcutsHelp && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-parchment border border-warm-gray shadow-xl max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-display text-xl text-ink">Keyboard Shortcuts</h3>
                <button
                  onClick={() => setShowShortcutsHelp(false)}
                  className="text-slate hover:text-ink"
                >
                  <XCircle size={24} />
                </button>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-2 bg-warm-gray/30">
                  <span className="text-ink font-body">Navigate down</span>
                  <kbd className="px-2 py-1 bg-parchment border border-warm-gray font-mono text-sm text-ink">j</kbd>
                </div>
                <div className="flex items-center justify-between p-2 bg-warm-gray/30">
                  <span className="text-ink font-body">Navigate up</span>
                  <kbd className="px-2 py-1 bg-parchment border border-warm-gray font-mono text-sm text-ink">k</kbd>
                </div>
                <div className="flex items-center justify-between p-2 bg-warm-gray/30">
                  <span className="text-ink font-body">Focus search</span>
                  <kbd className="px-2 py-1 bg-parchment border border-warm-gray font-mono text-sm text-ink">/</kbd>
                </div>
                <div className="flex items-center justify-between p-2 bg-warm-gray/30">
                  <span className="text-ink font-body">View job details</span>
                  <kbd className="px-2 py-1 bg-parchment border border-warm-gray font-mono text-sm text-ink">Enter</kbd>
                </div>
                <div className="flex items-center justify-between p-2 bg-warm-gray/30">
                  <span className="text-ink font-body">Delete selected job</span>
                  <kbd className="px-2 py-1 bg-parchment border border-warm-gray font-mono text-sm text-ink">d</kbd>
                </div>
                <div className="flex items-center justify-between p-2 bg-warm-gray/30">
                  <span className="text-ink font-body">Show this help</span>
                  <kbd className="px-2 py-1 bg-parchment border border-warm-gray font-mono text-sm text-ink">?</kbd>
                </div>
              </div>

              <p className="mt-4 text-sm text-slate font-body">
                Shortcuts work on the All Applications view
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Help Modal */}
      <HelpModal isOpen={showHelpModal} onClose={() => setShowHelpModal(false)} />

      {/* Resume Required Modal */}
      <ResumeRequiredModal
        isOpen={showResumeRequired}
        onClose={() => setShowResumeRequired(false)}
        onGoToResumes={() => {
          setShowResumeRequired(false);
          setActiveView('resumes');
          navigate('/');
        }}
      />

      {/* Processing Progress Modal */}
      <ProcessingModal
        isOpen={scanning}
        phase={processingPhase}
        stats={processingStats}
      />
    </div>
  );
}
