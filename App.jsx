import React, { useState, useEffect, useCallback } from 'react';
import { Search, RefreshCw, FileText, ExternalLink, ChevronDown, Filter, Briefcase, CheckCircle, XCircle, Clock, Star, Plus, Mail, Phone, User, Upload, Edit2, Trash2, Sparkles, AlertCircle } from 'lucide-react';

const API_BASE = '/api';

const STATUS_CONFIG = {
  new: { label: 'New', color: 'bg-gray-100 text-gray-700', icon: Clock },
  interested: { label: 'Interested', color: 'bg-blue-100 text-blue-700', icon: Star },
  applied: { label: 'Applied', color: 'bg-cyan-100 text-cyan-700', icon: CheckCircle },
  interviewing: { label: 'Interviewing', color: 'bg-purple-100 text-purple-700', icon: Briefcase },
  rejected: { label: 'Rejected', color: 'bg-red-100 text-red-700', icon: XCircle },
  offer: { label: 'Offer', color: 'bg-yellow-100 text-yellow-700', icon: Star },
  passed: { label: 'Passed', color: 'bg-gray-100 text-gray-500', icon: XCircle },
};

function ScoreBadge({ score }) {
  let color = 'bg-gray-200 text-gray-700';
  if (score >= 80) color = 'bg-gradient-to-r from-pink-500 to-pink-600 text-white shadow-md';
  else if (score >= 60) color = 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-sm';
  else if (score >= 40) color = 'bg-gradient-to-r from-yellow-500 to-yellow-600 text-white shadow-sm';
  else if (score > 0) color = 'bg-gradient-to-r from-red-400 to-red-500 text-white shadow-sm';

  return (
    <span className={`px-2 py-1 rounded-full text-sm font-bold ${color}`}>
      {score || '—'}
    </span>
  );
}

function StatusBadge({ status, onChange, statusConfig }) {
  const config_to_use = statusConfig || STATUS_CONFIG;
  const config = config_to_use[status] || config_to_use.new || config_to_use.applied;
  const Icon = config.icon;
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-1 px-2 py-1 rounded-full text-sm ${config.color} hover:opacity-80`}
      >
        <Icon size={14} />
        {config.label}
        <ChevronDown size={14} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 bg-white border rounded-lg shadow-lg z-10 min-w-32">
          {Object.entries(config_to_use).map(([key, cfg]) => (
            <button
              key={key}
              onClick={() => { onChange(key); setIsOpen(false); }}
              className={`w-full text-left px-3 py-2 hover:bg-gray-50 flex items-center gap-2 ${key === status ? 'bg-gray-50' : ''}`}
            >
              <cfg.icon size={14} />
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

  return (
    <div className={`bg-white rounded-lg shadow-sm border overflow-hidden ${
      isSelected ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-200'
    }`}>
      <div className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <ScoreBadge score={job.score} />
              <h3 className="font-semibold text-gray-900 truncate">{job.title}</h3>
            </div>
            <p className="text-gray-600 text-sm">{job.company || 'Unknown Company'}</p>
            <p className="text-gray-500 text-xs">{job.location || 'Location not specified'}</p>
          </div>

          <div className="flex items-center gap-2">
            <StatusBadge status={job.status} onChange={(s) => onStatusChange(job.job_id, s)} />
            <span className="text-xs text-gray-400 capitalize">{job.source}</span>
          </div>
        </div>

        {analysis.recommendation && (
          <p className="mt-2 text-sm text-gray-600 line-clamp-2">{analysis.recommendation}</p>
        )}
      </div>
      
      {expanded && (
        <div className="border-t px-4 py-3 bg-gray-50 space-y-3">
          {analysis.strengths?.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-cyan-700 uppercase mb-1">Strengths</h4>
              <ul className="text-sm text-gray-700 space-y-1">
                {analysis.strengths.map((s, i) => <li key={i}>• {s}</li>)}
              </ul>
            </div>
          )}

          {analysis.gaps?.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-red-700 uppercase mb-1">Gaps</h4>
              <ul className="text-sm text-gray-700 space-y-1">
                {analysis.gaps.map((g, i) => <li key={i}>• {g}</li>)}
              </ul>
            </div>
          )}
          
          {job.cover_letter && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase mb-1">Cover Letter</h4>
              <pre className="text-sm text-gray-700 whitespace-pre-wrap bg-white p-3 rounded border max-h-48 overflow-y-auto">
                {job.cover_letter}
              </pre>
            </div>
          )}

          {/* Notes Section */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <h4 className="text-xs font-semibold text-gray-700 uppercase">Notes</h4>
              {saveStatus && (
                <span className={`text-xs ${saveStatus === 'saving' ? 'text-blue-600' : 'text-cyan-600'}`}>
                  {saveStatus === 'saving' ? 'Saving...' : '✓ Saved'}
                </span>
              )}
            </div>
            <textarea
              value={notes}
              onChange={handleNotesChange}
              onBlur={handleNotesSave}
              placeholder="Add notes, interview dates, key takeaways..."
              className="w-full px-3 py-2 text-sm border rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows="3"
            />
          </div>

          <div className="flex items-center gap-2 pt-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                window.open(job.url, '_blank', 'width=1200,height=800,left=100,top=100');
              }}
              className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
            >
              <ExternalLink size={14} /> View Job
            </button>

            {!job.cover_letter && (
              <button
                onClick={(e) => { e.stopPropagation(); onGenerateCoverLetter(job.job_id); }}
                className="flex items-center gap-1 px-3 py-1.5 bg-purple-600 text-white rounded text-sm hover:bg-purple-700"
              >
                <FileText size={14} /> Generate Cover Letter
              </button>
            )}

            <button
              onClick={(e) => { e.stopPropagation(); onDelete(job.job_id); }}
              className="flex items-center gap-1 px-3 py-1.5 bg-red-600 text-white rounded text-sm hover:bg-red-700 ml-auto"
            >
              <Trash2 size={14} /> Delete
            </button>
          </div>
          
          <div className="text-xs text-gray-400">
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
    <div className="grid grid-cols-5 gap-4 mb-6">
      {[
        { label: 'Total', value: stats.total, color: 'bg-white border border-gray-200', textColor: 'text-gray-900' },
        { label: 'New', value: stats.new, color: 'bg-gradient-to-br from-gray-50 to-gray-100 border border-gray-200', textColor: 'text-gray-900' },
        { label: 'Interested', value: stats.interested, color: 'bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200', textColor: 'text-blue-900' },
        { label: 'Applied', value: stats.applied, color: 'bg-gradient-to-br from-cyan-50 to-cyan-100 border border-cyan-200', textColor: 'text-cyan-900' },
        { label: 'Avg Score', value: Math.round(stats.avg_score), color: 'bg-gradient-to-br from-pink-100 to-pink-200 border border-pink-300', textColor: 'text-pink-900' },
      ].map(({ label, value, color, textColor }) => (
        <div key={label} className={`${color} rounded-lg p-4 text-center shadow-sm hover:shadow-md transition-shadow`}>
          <div className={`text-3xl font-bold ${textColor}`}>{value}</div>
          <div className="text-xs text-gray-600 font-medium mt-1">{label}</div>
        </div>
      ))}
    </div>
  );
}

function ResumeCard({ resume, onEdit, onDelete, onResearch, expanded, onToggle }) {
  const [researching, setResearching] = useState(false);

  const handleResearch = async (e) => {
    e.stopPropagation();
    setResearching(true);
    await onResearch(resume.resume_id, resume.name);
    setResearching(false);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div
        className="p-4 cursor-pointer hover:bg-gray-50"
        onClick={onToggle}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 mb-1">{resume.name}</h3>
            {resume.focus_areas && (
              <p className="text-sm text-gray-600 mb-1">
                <span className="font-medium">Focus:</span> {resume.focus_areas}
              </p>
            )}
            {resume.target_roles && (
              <p className="text-sm text-gray-600">
                <span className="font-medium">Target Roles:</span> {resume.target_roles}
              </p>
            )}
          </div>
          <div className="flex flex-col items-end gap-2">
            <span className="px-2 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-700">
              Used {resume.usage_count || 0}x
            </span>
            <div className="flex gap-1">
              <button
                onClick={handleResearch}
                disabled={researching}
                className="p-1.5 text-purple-600 hover:bg-purple-50 rounded disabled:opacity-50"
                title="Find jobs for this resume"
              >
                {researching ? <RefreshCw size={16} className="animate-spin" /> : <Sparkles size={16} />}
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); onEdit(resume); }}
                className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
              >
                <Edit2 size={16} />
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(resume.resume_id); }}
                className="p-1.5 text-red-600 hover:bg-red-50 rounded"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {expanded && (
        <div className="border-t px-4 py-3 bg-gray-50 space-y-2">
          <div className="text-xs text-gray-500">
            Created: {new Date(resume.created_at).toLocaleDateString()}
          </div>
          <div className="max-h-40 overflow-y-auto">
            <p className="text-sm text-gray-700 whitespace-pre-wrap font-mono bg-white p-2 rounded border">
              {resume.content?.substring(0, 500)}...
            </p>
          </div>
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-4">Add New Resume</h2>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
              <AlertCircle size={20} className="text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Upload Mode Toggle */}
            <div className="flex gap-2 p-1 bg-gray-100 rounded-lg">
              <button
                type="button"
                onClick={() => setUploadMode('file')}
                className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition ${
                  uploadMode === 'file'
                    ? 'bg-white text-gray-900 shadow'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                📎 Upload File
              </button>
              <button
                type="button"
                onClick={() => setUploadMode('paste')}
                className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition ${
                  uploadMode === 'paste'
                    ? 'bg-white text-gray-900 shadow'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                📝 Paste Text
              </button>
            </div>

            {/* File Upload Mode */}
            {uploadMode === 'file' && (
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <Upload size={40} className="mx-auto mb-3 text-gray-400" />
                <label className="cursor-pointer">
                  <span className="text-sm text-gray-600">
                    {selectedFile ? (
                      <span className="text-teal-600 font-medium">
                        ✓ {selectedFile.name}
                      </span>
                    ) : (
                      <>
                        Click to upload or drag and drop
                        <br />
                        <span className="text-xs text-gray-500">PDF, TXT, or MD files</span>
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
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Resume Name *
              </label>
              <input
                type="text"
                placeholder="e.g., Backend Python AWS"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Focus Areas
              </label>
              <input
                type="text"
                placeholder="e.g., Python, AWS, FastAPI, PostgreSQL"
                value={formData.focus_areas}
                onChange={(e) => setFormData({ ...formData, focus_areas: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Target Roles
              </label>
              <input
                type="text"
                placeholder="e.g., Backend Engineer, API Developer"
                value={formData.target_roles}
                onChange={(e) => setFormData({ ...formData, target_roles: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>

            {/* Paste Mode */}
            {uploadMode === 'paste' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Resume Content *
                </label>
                <textarea
                  placeholder="Paste your resume text here..."
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg font-mono text-sm"
                  rows={12}
                  required={uploadMode === 'paste'}
                />
              </div>
            )}

            <div className="flex gap-3 pt-4">
              <button
                type="submit"
                disabled={saving}
                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save Resume'}
              </button>
              <button
                type="button"
                onClick={onClose}
                disabled={saving}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
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
    applied: { label: 'Applied', color: 'bg-cyan-100 text-cyan-700', icon: CheckCircle },
    interviewing: { label: 'Interviewing', color: 'bg-purple-100 text-purple-700', icon: Briefcase },
    rejected: { label: 'Rejected', color: 'bg-red-100 text-red-700', icon: XCircle },
    offer: { label: 'Offer', color: 'bg-yellow-100 text-yellow-700', icon: Star },
    withdrawn: { label: 'Withdrawn', color: 'bg-gray-100 text-gray-500', icon: XCircle },
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div
        className="p-4 cursor-pointer hover:bg-gray-50"
        onClick={onToggle}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-1 rounded-full text-xs font-semibold bg-orange-100 text-orange-700">
                EXTERNAL
              </span>
              <h3 className="font-semibold text-gray-900 truncate">{app.title}</h3>
            </div>
            <p className="text-gray-600 text-sm">{app.company}</p>
            <p className="text-gray-500 text-xs">{app.location || 'Location not specified'}</p>
          </div>

          <div className="flex items-center gap-2">
            <StatusBadge
              status={app.status}
              onChange={(s) => onStatusChange(app.app_id, s)}
              statusConfig={EXTERNAL_STATUS_CONFIG}
            />
            <span className="text-xs text-gray-400">{sourceLabels[app.source] || app.source}</span>
          </div>
        </div>
      </div>

      {expanded && (
        <div className="border-t px-4 py-3 bg-gray-50 space-y-3">
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-500">Applied:</span>
              <span className="ml-2 font-medium">{new Date(app.applied_date).toLocaleDateString()}</span>
            </div>
            {app.application_method && (
              <div>
                <span className="text-gray-500">Method:</span>
                <span className="ml-2 font-medium capitalize">{app.application_method.replace('_', ' ')}</span>
              </div>
            )}
            {app.contact_name && (
              <div>
                <User size={14} className="inline mr-1" />
                <span className="font-medium">{app.contact_name}</span>
              </div>
            )}
            {app.contact_email && (
              <div>
                <Mail size={14} className="inline mr-1" />
                <span className="font-medium">{app.contact_email}</span>
              </div>
            )}
          </div>

          {app.notes && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase mb-1">Notes</h4>
              <p className="text-sm text-gray-700 bg-white p-3 rounded border">{app.notes}</p>
            </div>
          )}

          <div className="flex items-center gap-2 pt-2">
            {app.url && (
              <a
                href={app.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
              >
                <ExternalLink size={14} /> View Job
              </a>
            )}
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(app.app_id); }}
              className="flex items-center gap-1 px-3 py-1.5 bg-red-600 text-white rounded text-sm hover:bg-red-700"
            >
              Delete
            </button>
          </div>

          <div className="text-xs text-gray-400">
            Created: {new Date(app.created_at).toLocaleDateString()}
          </div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [jobs, setJobs] = useState([]);
  const [stats, setStats] = useState({ total: 0, new: 0, interested: 0, applied: 0, avg_score: 0 });
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scoring, setScoring] = useState(false);
  const [researching, setResearching] = useState(false);
  const [expandedJob, setExpandedJob] = useState(null);
  const [filter, setFilter] = useState({ status: '', minScore: 0, search: '', sort: 'date' });
  const [activeView, setActiveView] = useState('discovered'); // 'discovered', 'external', 'resumes', 'companies', 'roadmap', or 'settings'
  const [externalApps, setExternalApps] = useState([]);
  const [showAddExternal, setShowAddExternal] = useState(false);
  const [resumes, setResumes] = useState([]);
  const [showResumeModal, setShowResumeModal] = useState(false);
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

      // Only apply shortcuts on discovered jobs view
      if (activeView !== 'discovered') {
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
            window.open(filteredJobsList[selectedJobIndex].url, '_blank');
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
  }, [activeView, filter, jobs, selectedJobIndex]);
  
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

  useEffect(() => {
    console.log('[Frontend] Component mounted, fetching initial data...');
    fetchJobs();
    fetchExternalApps();
    fetchResumes();
    fetchTrackedCompanies();
    fetchCustomEmailSources();
  }, [fetchJobs, fetchExternalApps, fetchResumes, fetchTrackedCompanies, fetchCustomEmailSources]);

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

  const handleScan = async () => {
    setScanning(true);
    showToast('Scanning emails...', 'info');
    try {
      await fetch(`${API_BASE}/scan`, { method: 'POST' });
      showToast('Email scan complete! Refreshing jobs...', 'success');
      // Poll for updates after a delay
      setTimeout(fetchJobs, 5000);
      setTimeout(fetchJobs, 15000);
      setTimeout(fetchJobs, 30000);
    } catch (err) {
      console.error('Scan failed:', err);
      showToast('Scan failed. Please try again.', 'error');
    }
    setScanning(false);
  };

  const handleScoreJobs = async () => {
    setScoring(true);
    try {
      const response = await fetch(`${API_BASE}/score-jobs`, { method: 'POST' });
      const data = await response.json();
      if (data.error) {
        showToast(`Scoring failed: ${data.error}`, 'error');
      } else {
        showToast(`✓ Scored ${data.scored} jobs out of ${data.total}`, 'success');
      }
      // Refresh jobs to show new scores
      setTimeout(fetchJobs, 2000);
    } catch (err) {
      console.error('Scoring failed:', err);
      showToast('Scoring failed. Check console for details.', 'error');
    }
    setScoring(false);
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
      await fetch(`${API_BASE}/jobs/${jobId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes }),
      });
      // Update local state optimistically
      setJobs(prevJobs =>
        prevJobs.map(job =>
          job.job_id === jobId ? { ...job, notes } : job
        )
      );
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
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-pink-50 dark:from-gray-900 dark:to-gray-800 transition-colors duration-200">
      <header className="bg-white dark:bg-gray-800 shadow-md border-b border-pink-100 dark:border-gray-700 transition-colors duration-200">
        <div className="max-w-6xl mx-auto px-4 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Logo placeholder - add your logo here */}
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-pink-400 to-pink-500 flex items-center justify-center shadow-lg">
                <span className="text-2xl">🐷</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-800 to-pink-600 dark:from-pink-400 dark:to-purple-400 bg-clip-text text-transparent">
                  Henry the Hire Tracker
                </h1>
                <p className="text-sm text-gray-600 dark:text-gray-400">AI-powered job matching</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleResearchJobs}
                disabled={researching}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
              >
                <Sparkles size={18} className={researching ? 'animate-pulse' : ''} />
                {researching ? 'Researching...' : 'Research Jobs with Claude'}
              </button>

              <button
                onClick={handleScan}
                disabled={scanning}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                <RefreshCw size={18} className={scanning ? 'animate-spin' : ''} />
                {scanning ? 'Scanning...' : 'Scan Emails'}
              </button>

              <button
                onClick={handleScoreJobs}
                disabled={scoring}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-pink-300 to-pink-400 text-pink-900 rounded-lg hover:from-pink-400 hover:to-pink-500 shadow-md hover:shadow-lg transition-all disabled:opacity-50 border-2 border-pink-400"
              >
                <Star size={18} className={scoring ? 'animate-spin' : ''} />
                {scoring ? 'Scoring...' : 'Score Jobs'}
              </button>
            </div>
          </div>
        </div>
      </header>
      
      <main className="max-w-6xl mx-auto px-4 py-6">
        {/* View Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveView('discovered')}
            className={`px-4 py-2 rounded-lg font-medium transition shadow-sm ${
              activeView === 'discovered'
                ? 'bg-gradient-to-r from-pink-300 to-pink-400 text-pink-900 shadow-md border-2 border-pink-400'
                : 'bg-white text-gray-700 hover:bg-pink-50 border-2 border-pink-100'
            }`}
          >
            Discovered Jobs ({jobs.length})
          </button>
          <button
            onClick={() => setActiveView('external')}
            className={`px-4 py-2 rounded-lg font-medium transition shadow-sm ${
              activeView === 'external'
                ? 'bg-gradient-to-r from-emerald-200 to-emerald-300 text-emerald-900 shadow-md border-2 border-emerald-400'
                : 'bg-white text-gray-700 hover:bg-emerald-50 border-2 border-emerald-100'
            }`}
          >
            External Applications ({externalApps.length})
          </button>
          <button
            onClick={() => setActiveView('resumes')}
            className={`px-4 py-2 rounded-lg font-medium transition shadow-sm ${
              activeView === 'resumes'
                ? 'bg-gradient-to-r from-purple-200 to-purple-300 text-purple-900 shadow-md border-2 border-purple-400'
                : 'bg-white text-gray-700 hover:bg-purple-50 border-2 border-purple-100'
            }`}
          >
            📄 Resume Library ({resumes.length})
          </button>
          <button
            onClick={() => setActiveView('companies')}
            className={`px-4 py-2 rounded-lg font-medium transition shadow-sm ${
              activeView === 'companies'
                ? 'bg-gradient-to-r from-amber-200 to-amber-300 text-amber-900 shadow-md border-2 border-amber-400'
                : 'bg-white text-gray-700 hover:bg-amber-50 border-2 border-amber-100'
            }`}
          >
            🏢 Tracked Companies ({trackedCompanies.length})
          </button>
          <button
            onClick={() => setActiveView('roadmap')}
            className={`px-4 py-2 rounded-lg font-medium transition shadow-sm ${
              activeView === 'roadmap'
                ? 'bg-gradient-to-r from-blue-200 to-blue-300 text-blue-900 shadow-md border-2 border-blue-400'
                : 'bg-white text-gray-700 hover:bg-blue-50 border-2 border-blue-100'
            }`}
          >
            🗺️ Roadmap
          </button>
          <button
            onClick={() => setActiveView('settings')}
            className={`px-4 py-2 rounded-lg font-medium transition shadow-sm ${
              activeView === 'settings'
                ? 'bg-gradient-to-r from-gray-200 to-gray-300 text-gray-900 shadow-md border-2 border-gray-400'
                : 'bg-white text-gray-700 hover:bg-gray-50 border-2 border-gray-100'
            }`}
          >
            ⚙️ Settings
          </button>
        </div>

        {activeView === 'discovered' ? (
          <>
            <StatsBar stats={stats} />

            {/* Filters */}
            <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search jobs..."
              value={filter.search}
              onChange={(e) => setFilter({ ...filter, search: e.target.value })}
              className="w-full pl-10 pr-4 py-2 border rounded-lg"
            />
          </div>
          
          <select
            value={filter.status}
            onChange={(e) => setFilter({ ...filter, status: e.target.value })}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="">All Statuses</option>
            {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
              <option key={key} value={key}>{cfg.label}</option>
            ))}
          </select>
          
          <select
            value={filter.minScore}
            onChange={(e) => setFilter({ ...filter, minScore: Number(e.target.value) })}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="0">All Scores</option>
            <option value="80">80+ (Highly Qualified)</option>
            <option value="60">60+ (Good Match)</option>
            <option value="40">40+ (Partial Match)</option>
          </select>

          <select
            value={filter.sort}
            onChange={(e) => setFilter({ ...filter, sort: e.target.value })}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="date">Sort by Date (Newest)</option>
            <option value="date-oldest">Sort by Date (Oldest)</option>
            <option value="title">Sort by Title (A-Z)</option>
            <option value="title-desc">Sort by Title (Z-A)</option>
            <option value="score">Sort by Score (High-Low)</option>
            <option value="score-low">Sort by Score (Low-High)</option>
          </select>
        </div>
        
            {/* Jobs List */}
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 animate-pulse">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 bg-gray-200 rounded-full"></div>
                      <div className="flex-1 space-y-2">
                        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                        <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                        <div className="h-3 bg-gray-200 rounded w-1/3"></div>
                      </div>
                      <div className="w-20 h-8 bg-gray-200 rounded"></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : filteredJobs.length === 0 ? (
              <div className="text-center py-12">
                <Briefcase size={48} className="mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500">No jobs found. Click "Scan Emails" to fetch job alerts.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredJobs.map((job, index) => (
                  <JobCard
                    key={job.job_id}
                    job={job}
                    expanded={true}
                    onToggle={() => {}}
                    onStatusChange={handleStatusChange}
                    onGenerateCoverLetter={handleGenerateCoverLetter}
                    onRecommendResume={handleRecommendResume}
                    onDelete={handleDeleteJob}
                    onUpdateNotes={handleUpdateNotes}
                    isSelected={index === selectedJobIndex}
                  />
                ))}
              </div>
            )}
          </>
        ) : activeView === 'external' ? (
          <>
            {/* External Applications View */}
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900">External Applications</h2>
              <button
                onClick={() => setShowAddExternal(!showAddExternal)}
                className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700"
              >
                <Plus size={18} />
                {showAddExternal ? 'Cancel' : 'Add External Application'}
              </button>
            </div>

            {showAddExternal && (
              <div className="bg-white rounded-lg shadow-sm border p-4 mb-6">
                <h3 className="font-semibold mb-4">Add External Application</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Use the browser extension for quick capture, or visit the extension for more options.
                </p>
                <button
                  onClick={() => setShowAddExternal(false)}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                >
                  Close
                </button>
              </div>
            )}

            {externalApps.length === 0 ? (
              <div className="text-center py-12">
                <Briefcase size={48} className="mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500 mb-4">No external applications tracked yet.</p>
                <p className="text-sm text-gray-400">Use the browser extension to add applications you made outside the system.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {externalApps.map(app => (
                  <ExternalApplicationCard
                    key={app.app_id}
                    app={app}
                    expanded={expandedJob === app.app_id}
                    onToggle={() => setExpandedJob(expandedJob === app.app_id ? null : app.app_id)}
                    onStatusChange={handleExternalStatusChange}
                    onDelete={handleDeleteExternal}
                  />
                ))}
              </div>
            )}
          </>
        ) : activeView === 'resumes' ? (
          <>
            {/* Resumes View */}
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Resume Library</h2>
              <button
                onClick={() => setShowResumeModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                <Plus size={18} />
                Add Resume
              </button>
            </div>

            {resumes.length === 0 ? (
              <div className="text-center py-12">
                <FileText size={48} className="mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500 mb-4">No resumes in your library yet.</p>
                <p className="text-sm text-gray-400 mb-6">Add your first resume to get AI-powered job-resume matching!</p>
                <button
                  onClick={() => setShowResumeModal(true)}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                >
                  <Upload size={20} />
                  Upload Your First Resume
                </button>
              </div>
            ) : (
              <>
                <div className="mb-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
                  <h3 className="font-semibold text-purple-900 mb-2">📊 Library Stats</h3>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-2xl font-bold text-purple-600">{resumes.length}</div>
                      <div className="text-purple-700">Total Resumes</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-purple-600">
                        {resumes.reduce((sum, r) => sum + (r.usage_count || 0), 0)}
                      </div>
                      <div className="text-purple-700">Total Recommendations</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-purple-600">
                        {resumes.filter(r => r.usage_count > 0).length}
                      </div>
                      <div className="text-purple-700">Used Resumes</div>
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
                      onEdit={() => alert('Edit functionality coming soon!')}
                      onDelete={handleDeleteResume}
                      onResearch={handleResearchForResume}
                    />
                  ))}
                </div>
              </>
            )}
          </>
        ) : activeView === 'companies' ? (
          <>
            {/* Tracked Companies View */}
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Tracked Companies</h2>
              <button
                onClick={() => setShowAddCompany(!showAddCompany)}
                className="flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700"
              >
                <Plus size={18} />
                {showAddCompany ? 'Cancel' : 'Add Company'}
              </button>
            </div>

            {showAddCompany && (
              <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
                <h3 className="font-semibold mb-4">Add Tracked Company</h3>
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
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Company Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        name="company_name"
                        required
                        className="w-full px-3 py-2 border rounded-lg"
                        placeholder="e.g., Google, Microsoft, Startup Inc."
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Career Page URL
                      </label>
                      <input
                        type="url"
                        name="career_page_url"
                        className="w-full px-3 py-2 border rounded-lg"
                        placeholder="https://company.com/careers"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Job Alert Email
                      </label>
                      <input
                        type="email"
                        name="job_alert_email"
                        className="w-full px-3 py-2 border rounded-lg"
                        placeholder="jobs@company.com"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Notes
                      </label>
                      <textarea
                        name="notes"
                        rows="3"
                        className="w-full px-3 py-2 border rounded-lg"
                        placeholder="Add any notes about this company..."
                      />
                    </div>
                    <div className="flex gap-2">
                      <button
                        type="submit"
                        className="px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700"
                      >
                        Add Company
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowAddCompany(false)}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
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
                <Briefcase size={48} className="mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500 mb-4">No tracked companies yet.</p>
                <p className="text-sm text-gray-400 mb-6">
                  Track companies you're interested in with their career pages and job alert emails.
                </p>
                <button
                  onClick={() => setShowAddCompany(true)}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-teal-600 text-white rounded-lg hover:bg-teal-700"
                >
                  <Plus size={20} />
                  Add Your First Company
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {trackedCompanies.map(company => (
                  <div key={company.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
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
                            className="w-full px-3 py-2 border rounded-lg font-semibold"
                            placeholder="Company Name"
                          />
                          <input
                            type="url"
                            name="career_page_url"
                            defaultValue={company.career_page_url || ''}
                            className="w-full px-3 py-2 border rounded-lg text-sm"
                            placeholder="Career Page URL"
                          />
                          <input
                            type="email"
                            name="job_alert_email"
                            defaultValue={company.job_alert_email || ''}
                            className="w-full px-3 py-2 border rounded-lg text-sm"
                            placeholder="Job Alert Email"
                          />
                          <textarea
                            name="notes"
                            defaultValue={company.notes || ''}
                            rows="2"
                            className="w-full px-3 py-2 border rounded-lg text-sm"
                            placeholder="Notes"
                          />
                          <div className="flex gap-2">
                            <button
                              type="submit"
                              className="px-3 py-1.5 bg-teal-600 text-white text-sm rounded-lg hover:bg-teal-700"
                            >
                              Save
                            </button>
                            <button
                              type="button"
                              onClick={() => setEditingCompany(null)}
                              className="px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200"
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
                            <h3 className="font-semibold text-gray-900 text-lg mb-2">{company.company_name}</h3>
                            <div className="space-y-1 text-sm text-gray-600">
                              {company.career_page_url && (
                                <div className="flex items-center gap-2">
                                  <ExternalLink size={14} />
                                  <a
                                    href={company.career_page_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:underline"
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
                                    className="text-blue-600 hover:underline"
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
                              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
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
                              className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                              title="Delete"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </div>
                        {company.notes && (
                          <div className="mt-2 p-3 bg-gray-50 rounded-lg">
                            <p className="text-sm text-gray-700">{company.notes}</p>
                          </div>
                        )}
                        <div className="mt-3 pt-3 border-t text-xs text-gray-500">
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
              <p className="text-gray-600 dark:text-gray-400">Track feature progress and planned improvements for Henry the Hire Tracker</p>
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
              <div className="bg-white rounded-lg shadow-sm border border-red-200 overflow-hidden">
                <div className="bg-gradient-to-r from-red-50 to-red-100 px-4 py-3 border-b border-red-200">
                  <h3 className="font-bold text-red-900 flex items-center gap-2">
                    🚨 CRITICAL - Must Have Before Test Users
                    <span className="text-xs bg-red-200 text-red-800 px-2 py-1 rounded-full">P0</span>
                  </h3>
                </div>
                <div className="p-4 space-y-2 text-sm">
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900">Authentication & Multi-User Support</div>
                      <div className="text-xs text-gray-600">User registration, login, session management, user isolation</div>
                      <div className="text-xs text-gray-500 mt-1">Effort: 2-3 weeks</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900">Database & Hosting</div>
                      <div className="text-xs text-gray-600">Migrate to PostgreSQL, deploy backend/frontend, environment management</div>
                      <div className="text-xs text-gray-500 mt-1">Effort: 1 week</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900">API Key Management</div>
                      <div className="text-xs text-gray-600">Secure storage, rate limiting, cost tracking, BYOK decision</div>
                      <div className="text-xs text-gray-500 mt-1">Effort: 3-5 days</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900">Gmail OAuth Per User</div>
                      <div className="text-xs text-gray-600">OAuth flow, token storage, refresh handling per user</div>
                      <div className="text-xs text-gray-500 mt-1">Effort: 2-3 days</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900">Domain & SSL</div>
                      <div className="text-xs text-gray-600">Purchase domain, SSL certificate, configure DNS, update OAuth redirects</div>
                      <div className="text-xs text-gray-500 mt-1">Effort: 4 hours</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Wins - In Progress */}
              <div className="bg-white rounded-lg shadow-sm border border-blue-200 overflow-hidden">
                <div className="bg-gradient-to-r from-blue-50 to-blue-100 px-4 py-3 border-b border-blue-200">
                  <h3 className="font-bold text-blue-900 flex items-center gap-2">
                    🎯 Quick Wins - Easy but Impactful
                    <span className="text-xs bg-blue-200 text-blue-800 px-2 py-1 rounded-full">In Progress</span>
                  </h3>
                </div>
                <div className="p-4 space-y-2 text-sm">
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" defaultChecked />
                    <div className="opacity-60">
                      <div className="font-medium text-gray-900 line-through">Create Roadmap Page</div>
                      <div className="text-xs text-teal-600">✓ Completed</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900">Custom Email Sources (User-Defined) ⚡</div>
                      <div className="text-xs text-gray-600">UI to add custom job board email patterns with AI assistance</div>
                      <div className="text-xs text-blue-600 mt-1">🔄 Starting Now - Effort: 2-3 days</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900">Dark Mode</div>
                      <div className="text-xs text-gray-600">Toggle in settings, respect system preference</div>
                      <div className="text-xs text-gray-500 mt-1">Effort: 1 day</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900">Keyboard Shortcuts</div>
                      <div className="text-xs text-gray-600">J/K navigation, / search, Enter open, D delete, ? help</div>
                      <div className="text-xs text-gray-500 mt-1">Effort: 4 hours</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900">Job Notes</div>
                      <div className="text-xs text-gray-600">Quick notes field, interview date, key takeaways</div>
                      <div className="text-xs text-gray-500 mt-1">Effort: 2 hours</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900">Better Empty States & Loading</div>
                      <div className="text-xs text-gray-600">Skeleton loaders, progress bars, toast notifications</div>
                      <div className="text-xs text-gray-500 mt-1">Effort: 1 day</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <div>
                      <div className="font-medium text-gray-900">Enhanced Deduplication</div>
                      <div className="text-xs text-gray-600">Fuzzy matching, show similar jobs, manual merge</div>
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
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <ExternalLink size={16} />
                  View ROADMAP.md on GitHub
                </a>
              </div>

              {/* Current Sprint */}
              <div className="bg-gradient-to-r from-pink-50 to-pink-100 rounded-lg p-6 border border-pink-200">
                <h3 className="font-bold text-pink-900 mb-3">🚀 Current Sprint (This Week)</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2 text-pink-800">
                    <CheckCircle size={16} className="text-teal-600" />
                    <span className="font-medium">Create Roadmap Page - DONE</span>
                  </div>
                  <div className="flex items-center gap-2 text-pink-800">
                    <Clock size={16} className="text-blue-600" />
                    <span className="font-medium">Implement Custom Email Sources UI</span>
                  </div>
                  <div className="flex items-center gap-2 text-pink-800">
                    <Clock size={16} className="text-gray-400" />
                    <span>Add Dark Mode Toggle</span>
                  </div>
                  <div className="flex items-center gap-2 text-pink-800">
                    <Clock size={16} className="text-gray-400" />
                    <span>Add Keyboard Shortcuts</span>
                  </div>
                  <div className="flex items-center gap-2 text-pink-800">
                    <Clock size={16} className="text-gray-400" />
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
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">⚙️ Settings</h2>
              <p className="text-gray-600 dark:text-gray-400">Configure custom email sources and application preferences</p>
            </div>

            {/* Dark Mode Section */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden mb-6 transition-colors duration-200">
              <div className="bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-gray-700 dark:to-gray-600 px-4 py-3 border-b border-purple-200 dark:border-gray-600">
                <h3 className="font-bold text-purple-900 dark:text-purple-200">🌙 Appearance</h3>
                <p className="text-sm text-purple-700 dark:text-purple-300 mt-1">
                  Customize how Hammy looks
                </p>
              </div>

              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white">Dark Mode</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {darkMode ? 'Currently using dark theme' : 'Currently using light theme'}
                    </p>
                  </div>
                  <button
                    onClick={() => setDarkMode(!darkMode)}
                    className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 ${
                      darkMode ? 'bg-purple-600' : 'bg-gray-300'
                    }`}
                  >
                    <span
                      className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform duration-200 ${
                        darkMode ? 'translate-x-7' : 'translate-x-1'
                      }`}
                    >
                      <span className="flex items-center justify-center h-full">
                        {darkMode ? '🌙' : '☀️'}
                      </span>
                    </span>
                  </button>
                </div>
              </div>
            </div>

            {/* Custom Email Sources Section */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden mb-6">
              <div className="bg-gradient-to-r from-blue-50 to-blue-100 px-4 py-3 border-b border-blue-200">
                <h3 className="font-bold text-blue-900">📧 Custom Email Sources</h3>
                <p className="text-sm text-blue-700 mt-1">
                  Add job boards and companies that send you job alerts via email
                </p>
              </div>

              <div className="p-4">
                <div className="flex justify-between items-center mb-4">
                  <p className="text-sm text-gray-600">
                    {customEmailSources.length} custom source{customEmailSources.length !== 1 ? 's' : ''} configured
                  </p>
                  <button
                    onClick={() => setShowAddEmailSource(!showAddEmailSource)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    <Plus size={18} />
                    {showAddEmailSource ? 'Cancel' : 'Add Email Source'}
                  </button>
                </div>

                {/* Add Email Source Form */}
                {showAddEmailSource && (
                  <div className="bg-blue-50 rounded-lg border border-blue-200 p-4 mb-4">
                    <h4 className="font-semibold text-blue-900 mb-3">Add New Email Source</h4>
                    <form onSubmit={(e) => {
                      e.preventDefault();
                      const formData = new FormData(e.target);
                      handleAddEmailSource({
                        name: formData.get('name'),
                        sender_email: formData.get('sender_email'),
                        sender_pattern: formData.get('sender_pattern'),
                        subject_keywords: formData.get('subject_keywords'),
                      });
                      e.target.reset();
                    }}>
                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Source Name <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="text"
                            name="name"
                            required
                            className="w-full px-3 py-2 border rounded-lg"
                            placeholder="e.g., Stripe Careers, Remote.com Jobs"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Sender Email
                          </label>
                          <input
                            type="email"
                            name="sender_email"
                            className="w-full px-3 py-2 border rounded-lg"
                            placeholder="e.g., careers@stripe.com, jobs@remote.com"
                          />
                          <p className="text-xs text-gray-500 mt-1">
                            The exact email address that sends job alerts
                          </p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Sender Pattern (Alternative)
                          </label>
                          <input
                            type="text"
                            name="sender_pattern"
                            className="w-full px-3 py-2 border rounded-lg"
                            placeholder="e.g., noreply@company.com"
                          />
                          <p className="text-xs text-gray-500 mt-1">
                            Use if emails come from varying senders (one or the other required)
                          </p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Subject Keywords (Optional)
                          </label>
                          <input
                            type="text"
                            name="subject_keywords"
                            className="w-full px-3 py-2 border rounded-lg"
                            placeholder="e.g., job alert, new opportunities, careers"
                          />
                          <p className="text-xs text-gray-500 mt-1">
                            Comma-separated keywords to match in subject line
                          </p>
                        </div>

                        <div className="flex gap-2 pt-2">
                          <button
                            type="submit"
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                          >
                            Add Source
                          </button>
                          <button
                            type="button"
                            onClick={() => setShowAddEmailSource(false)}
                            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    </form>
                  </div>
                )}

                {/* Email Sources List */}
                {customEmailSources.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Mail size={48} className="mx-auto mb-3 text-gray-300" />
                    <p className="mb-2">No custom email sources yet</p>
                    <p className="text-sm text-gray-400">
                      Add email sources to scan job alerts from any company or job board
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {customEmailSources.map(source => (
                      <div key={source.id} className="border rounded-lg p-3 flex items-start justify-between hover:bg-gray-50">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h4 className="font-semibold text-gray-900">{source.name}</h4>
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              source.enabled
                                ? 'bg-teal-100 text-teal-700'
                                : 'bg-gray-100 text-gray-600'
                            }`}>
                              {source.enabled ? 'Active' : 'Disabled'}
                            </span>
                          </div>
                          {source.sender_email && (
                            <p className="text-sm text-gray-600 mt-1">
                              <Mail size={14} className="inline mr-1" />
                              From: {source.sender_email}
                            </p>
                          )}
                          {source.sender_pattern && !source.sender_email && (
                            <p className="text-sm text-gray-600 mt-1">
                              <Mail size={14} className="inline mr-1" />
                              Pattern: {source.sender_pattern}
                            </p>
                          )}
                          {source.subject_keywords && (
                            <p className="text-sm text-gray-600 mt-1">
                              <Filter size={14} className="inline mr-1" />
                              Keywords: {source.subject_keywords}
                            </p>
                          )}
                          <p className="text-xs text-gray-400 mt-1">
                            Added: {new Date(source.created_at).toLocaleDateString()}
                          </p>
                        </div>

                        <div className="flex items-center gap-2 ml-4">
                          <button
                            onClick={() => handleToggleEmailSource(source)}
                            className={`px-3 py-1 text-sm rounded ${
                              source.enabled
                                ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                : 'bg-teal-100 text-teal-700 hover:bg-teal-200'
                            }`}
                            title={source.enabled ? 'Disable' : 'Enable'}
                          >
                            {source.enabled ? 'Disable' : 'Enable'}
                          </button>
                          <button
                            onClick={() => {
                              if (confirm(`Delete "${source.name}"?`)) {
                                handleDeleteEmailSource(source.id);
                              }
                            }}
                            className="p-2 text-red-600 hover:bg-red-50 rounded"
                            title="Delete"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Help Text */}
                <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <h4 className="font-semibold text-blue-900 mb-2">💡 How to Use Custom Email Sources</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>1. Find a job alert email in your inbox from the source you want to add</li>
                    <li>2. Copy the sender's email address (e.g., jobs@company.com)</li>
                    <li>3. Add it here with a memorable name</li>
                    <li>4. Run "Scan Emails" to start finding jobs from this source</li>
                  </ul>
                  <p className="text-sm text-blue-700 mt-3">
                    <strong>Tip:</strong> Subject keywords are optional but help filter out non-job emails from the same sender.
                  </p>
                </div>
              </div>
            </div>

            {/* Future Settings Sections */}
            <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg p-6 border border-gray-200 text-center">
              <p className="text-gray-600">
                More settings coming soon: notifications, preferences, API keys, and more!
              </p>
            </div>
          </>
        )}
      </main>

      {/* Resume Upload Modal */}
      {showResumeModal && (
        <ResumeUploadModal
          onClose={() => setShowResumeModal(false)}
          onSave={fetchResumes}
        />
      )}

      {/* Toast Notifications */}
      <div className="fixed bottom-4 right-4 z-50 space-y-2">
        {toasts.map(toast => (
          <div
            key={toast.id}
            className={`px-4 py-3 rounded-lg shadow-lg text-white transform transition-all duration-300 animate-slide-in ${
              toast.type === 'success' ? 'bg-teal-600' :
              toast.type === 'error' ? 'bg-red-600' :
              toast.type === 'warning' ? 'bg-yellow-600' :
              'bg-blue-600'
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
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">⌨️ Keyboard Shortcuts</h3>
                <button
                  onClick={() => setShowShortcutsHelp(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <XCircle size={24} />
                </button>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
                  <span className="text-gray-700 dark:text-gray-300">Navigate down</span>
                  <kbd className="px-2 py-1 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded font-mono text-sm">j</kbd>
                </div>
                <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
                  <span className="text-gray-700 dark:text-gray-300">Navigate up</span>
                  <kbd className="px-2 py-1 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded font-mono text-sm">k</kbd>
                </div>
                <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
                  <span className="text-gray-700 dark:text-gray-300">Focus search</span>
                  <kbd className="px-2 py-1 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded font-mono text-sm">/</kbd>
                </div>
                <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
                  <span className="text-gray-700 dark:text-gray-300">Open selected job</span>
                  <kbd className="px-2 py-1 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded font-mono text-sm">Enter</kbd>
                </div>
                <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
                  <span className="text-gray-700 dark:text-gray-300">Delete selected job</span>
                  <kbd className="px-2 py-1 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded font-mono text-sm">d</kbd>
                </div>
                <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
                  <span className="text-gray-700 dark:text-gray-300">Show this help</span>
                  <kbd className="px-2 py-1 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded font-mono text-sm">?</kbd>
                </div>
              </div>

              <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">
                Shortcuts work on the Discovered Jobs view
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
