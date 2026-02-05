"""
Flask API Routes for Hammy the Hire Tracker

This module contains all HTTP endpoints for the web application.
"""

import os
import json
import hashlib
import uuid
import logging
from datetime import datetime, timedelta
from flask import jsonify, request
from werkzeug.utils import secure_filename

# Anthropic Claude AI
import anthropic

# Import business logic from other modules
from ai_analyzer import (
    ai_filter_and_score,
    analyze_job,
    generate_cover_letter,
    calculate_weighted_score,
    generate_interview_answer,
)
from gmail_scanner import scan_emails, scan_followup_emails, get_gmail_service, get_email_body
from resume_manager import (
    load_resumes,
    load_resumes_from_db,
    get_combined_resume_text,
    migrate_file_resumes_to_db,
    recommend_resume_for_job,
)
from database import get_db
from parsers import fetch_wwr_jobs, generate_job_id, clean_job_url
from config_loader import get_config
from constants import APP_DIR
from backup_manager import BackupManager
from app.ai import get_provider_info, get_available_providers

logger = logging.getLogger(__name__)

# Load config
CONFIG = get_config()

# Dashboard HTML template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Hammy the Hire Tracker</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="max-w-6xl mx-auto p-6">
        <div class="flex justify-between items-center mb-6">
            <div>
                <h1 class="text-3xl font-bold">🐷 Hammy the Hire Tracker</h1>
                <p class="text-gray-600">Go HAM on your job search!</p>
            </div>
            <div class="space-x-2">
                <button onclick="scanEmails()" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                    📧 Scan Gmail
                </button>
                <button onclick="scanWWR()" class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">
                    🌐 Scan WWR
                </button>
                <button onclick="analyzeAll()" class="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700">
                    🤖 Analyze All
                </button>
                <button onclick="scanFollowups()" class="bg-orange-600 text-white px-4 py-2 rounded hover:bg-orange-700">
                    📬 Scan Follow-Ups
                </button>
            </div>
        </div>
        
        <div class="mb-6 border-b">
            <button onclick="showTab('jobs')" id="tab-jobs" class="px-4 py-2 font-semibold border-b-2 border-blue-600">
                Jobs
            </button>
            <button onclick="showTab('followups')" id="tab-followups" class="px-4 py-2 font-semibold text-gray-600">
                📧 Follow-Ups
            </button>
            <button onclick="showTab('watchlist')" id="tab-watchlist" class="px-4 py-2 font-semibold text-gray-600">
                Watchlist
            </button>
        </div>
        
        <div id="jobs-tab">
            <div id="stats" class="grid grid-cols-5 gap-4 mb-6"></div>
            
            <div class="mb-4 flex gap-4">
                <input type="text" id="search" placeholder="Search..." 
                       class="flex-1 px-4 py-2 border rounded" onkeyup="filterJobs()">
                <select id="statusFilter" class="px-4 py-2 border rounded" onchange="loadJobs()">
                    <option value="">All Statuses</option>
                    <option value="new">New</option>
                    <option value="interested">Interested</option>
                    <option value="applied">Applied</option>
                    <option value="passed">Passed</option>
                </select>
                <select id="minScore" class="px-4 py-2 border rounded" onchange="loadJobs()">
                    <option value="0">All Scores</option>
                    <option value="80">80+</option>
                    <option value="60">60+</option>
                    <option value="40">40+</option>
                </select>
            </div>
            
            <div id="jobs" class="space-y-3"></div>
        </div>

        <div id="followups-tab" class="hidden">
            <div id="followup-stats" class="grid grid-cols-5 gap-4 mb-6"></div>
            <div id="followups" class="space-y-3"></div>
        </div>

        <div id="watchlist-tab" class="hidden">
            <div class="bg-white rounded-lg shadow p-6 mb-4">
                <h2 class="text-xl font-bold mb-4">Add Company to Watchlist</h2>
                <div class="space-y-3">
                    <input type="text" id="watch-company" placeholder="Company name" 
                           class="w-full px-4 py-2 border rounded">
                    <input type="url" id="watch-url" placeholder="Careers page URL" 
                           class="w-full px-4 py-2 border rounded">
                    <textarea id="watch-notes" placeholder="Notes (e.g., 'Not hiring now, check Q2')" 
                              class="w-full px-4 py-2 border rounded" rows="3"></textarea>
                    <button onclick="addToWatchlist()" class="bg-blue-600 text-white px-4 py-2 rounded">
                        Add to Watchlist
                    </button>
                </div>
            </div>
            
            <div id="watchlist-items" class="space-y-3"></div>
        </div>
    </div>
    
    <script>
        let allJobs = [];
        let currentTab = 'jobs';
        
        function showTab(tab) {
            currentTab = tab;
            document.getElementById('jobs-tab').classList.toggle('hidden', tab !== 'jobs');
            document.getElementById('followups-tab').classList.toggle('hidden', tab !== 'followups');
            document.getElementById('watchlist-tab').classList.toggle('hidden', tab !== 'watchlist');

            document.getElementById('tab-jobs').className = tab === 'jobs'
                ? 'px-4 py-2 font-semibold border-b-2 border-blue-600'
                : 'px-4 py-2 font-semibold text-gray-600';
            document.getElementById('tab-followups').className = tab === 'followups'
                ? 'px-4 py-2 font-semibold border-b-2 border-blue-600'
                : 'px-4 py-2 font-semibold text-gray-600';
            document.getElementById('tab-watchlist').className = tab === 'watchlist'
                ? 'px-4 py-2 font-semibold border-b-2 border-blue-600'
                : 'px-4 py-2 font-semibold text-gray-600';

            if (tab === 'followups') loadFollowups();
            if (tab === 'watchlist') loadWatchlist();
        }
        
        function formatDate(dateStr) {
            if (!dateStr) return '';
            try {
                const d = new Date(dateStr);
                return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            } catch {
                return '';
            }
        }
        
        async function loadJobs() {
            const status = document.getElementById('statusFilter').value;
            const minScore = document.getElementById('minScore').value;
            const params = new URLSearchParams({status, min_score: minScore});
            
            const res = await fetch('/api/jobs?' + params);
            const data = await res.json();
            allJobs = data.jobs;
            renderJobs(allJobs);
            renderStats(data.stats);
        }
        
        function renderStats(stats) {
            document.getElementById('stats').innerHTML = `
                <div class="bg-white p-4 rounded shadow text-center">
                    <div class="text-2xl font-bold">${stats.total}</div>
                    <div class="text-gray-500 text-sm">Total</div>
                </div>
                <div class="bg-blue-50 p-4 rounded shadow text-center">
                    <div class="text-2xl font-bold">${stats.new}</div>
                    <div class="text-gray-500 text-sm">New</div>
                </div>
                <div class="bg-yellow-50 p-4 rounded shadow text-center">
                    <div class="text-2xl font-bold">${stats.interested}</div>
                    <div class="text-gray-500 text-sm">Interested</div>
                </div>
                <div class="bg-green-50 p-4 rounded shadow text-center">
                    <div class="text-2xl font-bold">${stats.applied}</div>
                    <div class="text-gray-500 text-sm">Applied</div>
                </div>
                <div class="bg-purple-50 p-4 rounded shadow text-center">
                    <div class="text-2xl font-bold">${Math.round(stats.avg_score)}</div>
                    <div class="text-gray-500 text-sm">Avg Score</div>
                </div>
            `;
        }
        
        function filterJobs() {
            const search = document.getElementById('search').value.toLowerCase();
            const filtered = allJobs.filter(j => 
                j.title.toLowerCase().includes(search) || 
                (j.company || '').toLowerCase().includes(search)
            );
            renderJobs(filtered);
        }
        
        function renderJobs(jobs) {
            const container = document.getElementById('jobs');
            container.innerHTML = jobs.map(job => {
                const analysis = job.analysis ? JSON.parse(job.analysis) : {};
                const scoreColor = job.baseline_score >= 80 ? 'bg-green-500' : 
                                   job.baseline_score >= 60 ? 'bg-blue-500' : 
                                   job.baseline_score >= 40 ? 'bg-yellow-500' : 'bg-gray-300';
                
                // Status colors
                const statusColors = {
                    'new': 'bg-gray-100 border-gray-300',
                    'interested': 'bg-blue-50 border-blue-300',
                    'applied': 'bg-green-50 border-green-400',
                    'interviewing': 'bg-purple-50 border-purple-300',
                    'passed': 'bg-gray-50 border-gray-200',
                    'rejected': 'bg-red-50 border-red-200'
                };
                
                const statusColor = statusColors[job.status] || statusColors['new'];
                const viewedStyle = job.viewed ? 'opacity-90 bg-gray-100' : '';
                
                return `
                <div class="bg-white ${viewedStyle} rounded-lg shadow p-4 border-l-4 ${statusColor}">
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <div class="flex items-center gap-2 mb-1">
                                <span class="${scoreColor} text-white px-2 py-1 rounded-full text-sm font-bold">
                                    ${job.baseline_score || '—'}
                                </span>
                                <h3 class="font-semibold">${job.title}</h3>
                            </div>
                            <p class="text-gray-600 text-sm">${job.company || 'Unknown'} • ${job.location || ''}</p>
                            <p class="text-gray-400 text-xs">${job.source} • ${formatDate(job.email_date)}</p>
                            
                            ${analysis.recommendation ? `
                            <div class="mt-2 p-2 bg-blue-50 border-l-2 border-blue-400 rounded text-sm">
                                <strong class="text-blue-900">AI Insight:</strong>
                                <p class="text-gray-700 mt-1">${analysis.recommendation}</p>
                            </div>
                            ` : ''}
                        </div>
                        <div class="flex items-center gap-2">
                            <select onchange="updateStatus('${job.job_id}', this.value)" 
                                    class="text-sm border rounded px-2 py-1">
                                ${['new','interested','applied','interviewing','passed','rejected'].map(s => 
                                    `<option value="${s}" ${job.status === s ? 'selected' : ''}>${s}</option>`
                                ).join('')}
                            </select>
                            <button onclick="addToWatchlistFromJob('${job.company}', '${job.url}')" 
                                    class="text-yellow-600 hover:text-yellow-700 p-1" title="Add to Watchlist">
                                ⭐
                            </button>
                            <button onclick="hideJob('${job.job_id}')" 
                                    class="text-gray-400 hover:text-red-600 p-1" title="Hide">
                                ✕
                            </button>
                            <a href="${job.url}" target="_blank" class="text-blue-600 hover:underline text-sm"
                               onclick="markViewed('${job.job_id}')">View</a>
                        </div>
                    </div>
                    
                    ${analysis.strengths ? `
                    <details class="mt-3">
                        <summary class="cursor-pointer text-sm text-gray-500">Full Analysis</summary>
                        
                        <div class="mt-2 grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <h4 class="font-semibold text-green-700">Strengths</h4>
                                <ul class="list-disc list-inside">${analysis.strengths.map(s => `<li>${s}</li>`).join('')}</ul>
                            </div>
                            <div>
                                <h4 class="font-semibold text-red-700">Gaps</h4>
                                <ul class="list-disc list-inside">${(analysis.gaps || []).map(g => `<li>${g}</li>`).join('')}</ul>
                            </div>
                        </div>
                        
                        ${job.cover_letter ? `
                        <div class="mt-3">
                            <h4 class="font-semibold">Cover Letter</h4>
                            <pre class="bg-gray-50 p-3 rounded text-sm whitespace-pre-wrap mt-1">${job.cover_letter}</pre>
                        </div>
                        ` : `
                        <button onclick="generateCoverLetter('${job.job_id}')" 
                                class="mt-2 bg-purple-600 text-white px-3 py-1 rounded text-sm">
                            Generate Cover Letter
                        </button>
                        `}
                    </details>
                    ` : ''}
                </div>
                `;
            }).join('');
        }
        
        async function loadWatchlist() {
            const res = await fetch('/api/watchlist');
            const data = await res.json();
            
            const container = document.getElementById('watchlist-items');
            if (data.items.length === 0) {
                container.innerHTML = '<p class="text-gray-500 text-center py-8">No companies on watchlist yet</p>';
                return;
            }
            
            container.innerHTML = data.items.map(item => `
                <div class="bg-white rounded-lg shadow p-4">
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <h3 class="font-semibold text-lg">${item.company}</h3>
                            <a href="${item.url}" target="_blank" class="text-blue-600 hover:underline text-sm">
                                ${item.url}
                            </a>
                            ${item.notes ? `<p class="text-gray-600 text-sm mt-2">${item.notes}</p>` : ''}
                            <p class="text-gray-400 text-xs mt-1">Added ${formatDate(item.created_at)}</p>
                        </div>
                        <button onclick="removeFromWatchlist(${item.id})" 
                                class="text-red-600 hover:text-red-700">
                            Remove
                        </button>
                    </div>
                </div>
            `).join('');
        }
        
        async function addToWatchlist() {
            const company = document.getElementById('watch-company').value.trim();
            const url = document.getElementById('watch-url').value.trim();
            const notes = document.getElementById('watch-notes').value.trim();
            
            if (!company) {
                alert('Company name required');
                return;
            }
            
            await fetch('/api/watchlist', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({company, url, notes})
            });
            
            document.getElementById('watch-company').value = '';
            document.getElementById('watch-url').value = '';
            document.getElementById('watch-notes').value = '';
            
            loadWatchlist();
        }
        
        function addToWatchlistFromJob(company, url) {
            document.getElementById('watch-company').value = company;
            document.getElementById('watch-url').value = url;
            showTab('watchlist');
        }
        
        async function removeFromWatchlist(id) {
            console.log('[Dashboard] Removing from watchlist:', id);
            await fetch(`/api/watchlist/${id}`, {method: 'DELETE'});
            loadWatchlist();
        }
        
        async function scanWWR() {
            const btn = event.target;
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Scanning WWR...';
            
            try {
                await fetch('/api/wwr', {method: 'POST'});
                // Poll for updates
                setTimeout(loadJobs, 3000);
                setTimeout(loadJobs, 10000);
                setTimeout(loadJobs, 20000);
            } catch (err) {
                console.error('WWR scan failed:', err);
            }
            
            btn.disabled = false;
            btn.textContent = originalText;
        }
        
        async function scanEmails() {
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = 'Scanning...';
            await fetch('/api/scan', {method: 'POST'});
            await loadJobs();
            btn.disabled = false;
            btn.textContent = '📧 Scan Gmail';
        }
        
        async function analyzeAll() {
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = 'Analyzing...';
            await fetch('/api/analyze', {method: 'POST'});
            await loadJobs();
            btn.disabled = false;
            btn.textContent = '🤖 Analyze All';
        }
        
        async function updateStatus(jobId, status) {
            await fetch(`/api/jobs/${jobId}`, {
                method: 'PATCH',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({status})
            });
            loadJobs();
        }
        
        async function markViewed(jobId) {
            await fetch(`/api/jobs/${jobId}`, {
                method: 'PATCH',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({viewed: 1})
            });
            setTimeout(() => loadJobs(), 500);
        }
        
        async function hideJob(jobId) {
            console.log('[Dashboard] Hiding job:', jobId);
            await fetch(`/api/jobs/${jobId}`, {
                method: 'PATCH',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({status: 'hidden'})
            });
            loadJobs();
        }
        
        async function generateCoverLetter(jobId) {
            event.target.disabled = true;
            event.target.textContent = 'Generating...';
            await fetch(`/api/jobs/${jobId}/cover-letter`, {method: 'POST'});
            loadJobs();
        }

        async function scanFollowups() {
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = 'Scanning Follow-Ups...';
            try {
                const res = await fetch('/api/scan-followups', {method: 'POST'});
                const data = await res.json();
                alert(`Found ${data.found} follow-ups!\\n${data.new} new\\n${data.updated_jobs} jobs updated`);
                await loadFollowups();
                await loadJobs();
            } finally {
                btn.disabled = false;
                btn.textContent = '📬 Scan Follow-Ups';
            }
        }

        async function loadFollowups() {
            const res = await fetch('/api/followups');
            const data = await res.json();

            // Display statistics
            const stats = data.stats;
            document.getElementById('followup-stats').innerHTML = `
                <div class="bg-white rounded-lg shadow p-4 text-center">
                    <div class="text-2xl font-bold">${stats.total}</div>
                    <div class="text-sm text-gray-600">Total Responses</div>
                </div>
                <div class="bg-green-100 rounded-lg shadow p-4 text-center">
                    <div class="text-2xl font-bold text-green-700">🎉 ${stats.interviews}</div>
                    <div class="text-sm text-gray-600">Interviews</div>
                </div>
                <div class="bg-blue-100 rounded-lg shadow p-4 text-center">
                    <div class="text-2xl font-bold text-blue-700">🎁 ${stats.offers}</div>
                    <div class="text-sm text-gray-600">Offers</div>
                </div>
                <div class="bg-red-100 rounded-lg shadow p-4 text-center">
                    <div class="text-2xl font-bold text-red-700">😞 ${stats.rejections}</div>
                    <div class="text-sm text-gray-600">Rejections</div>
                </div>
                <div class="bg-purple-100 rounded-lg shadow p-4 text-center">
                    <div class="text-2xl font-bold text-purple-700">${stats.response_rate}%</div>
                    <div class="text-sm text-gray-600">Response Rate</div>
                </div>
            `;

            // Display follow-ups
            const followupsHTML = data.followups.map(f => {
                const typeIcons = {
                    'interview': '🎉',
                    'rejection': '😞',
                    'offer': '🎁',
                    'assessment': '📋',
                    'received': '✅',
                    'update': '📧'
                };
                const typeColors = {
                    'interview': 'bg-green-100 border-green-300',
                    'rejection': 'bg-red-100 border-red-300',
                    'offer': 'bg-blue-100 border-blue-300',
                    'assessment': 'bg-purple-100 border-purple-300',
                    'received': 'bg-gray-100 border-gray-300',
                    'update': 'bg-yellow-100 border-yellow-300'
                };

                const icon = typeIcons[f.type] || '📧';
                const color = typeColors[f.type] || 'bg-gray-100 border-gray-300';
                const matchBadge = f.job_id ? '<span class="text-xs bg-blue-500 text-white px-2 py-1 rounded">Matched</span>' : '';
                const spamBadge = f.in_spam ? '<span class="text-xs bg-red-500 text-white px-2 py-1 rounded">Was in Spam!</span>' : '';

                return `
                    <div class="bg-white rounded-lg shadow border-l-4 ${color} p-4">
                        <div class="flex justify-between items-start mb-2">
                            <div>
                                <div class="flex items-center gap-2">
                                    <span class="text-2xl">${icon}</span>
                                    <h3 class="font-bold text-lg">${f.type.toUpperCase()}: ${f.company}</h3>
                                    ${matchBadge}
                                    ${spamBadge}
                                </div>
                                <p class="text-sm text-gray-600">${f.subject}</p>
                            </div>
                            <div class="text-right">
                                <div class="text-sm text-gray-500">${formatDate(f.email_date)}</div>
                                ${f.title ? `<div class="text-xs text-blue-600 mt-1">${f.title}</div>` : ''}
                            </div>
                        </div>
                        <p class="text-sm text-gray-700 mt-2">${f.snippet}</p>
                        ${f.url ? `<a href="${f.url}" target="_blank" class="text-blue-600 text-sm hover:underline mt-2 inline-block">View Job →</a>` : ''}
                    </div>
                `;
            }).join('');

            document.getElementById('followups').innerHTML = followupsHTML ||
                '<div class="bg-white rounded-lg shadow p-8 text-center text-gray-500">No follow-ups yet. Click "📬 Scan Follow-Ups" to check your email!</div>';
        }

        loadJobs();
    </script>
</body>
</html>
"""


def register_routes(app):
    """
    Register all Flask routes with the app instance.

    Args:
        app: Flask application instance

    Returns:
        app: Flask application instance with routes registered
    """

    @app.route("/")
    def dashboard():
        """
        Serve the React frontend dashboard.

        Route: GET /

        Serves the built React application from the dist/ folder. The React app
        provides the user interface for job tracking, resume management, and
        application tracking.

        Returns:
            HTML content of the built React app, or error if not built

        Raises:
            500: If frontend hasn't been built yet
        """
        # Serve the built React app from dist folder
        dist_index = APP_DIR / "dist" / "index.html"
        if dist_index.exists():
            return dist_index.read_text()
        else:
            return "Frontend not built! Run 'npm run build' first.", 500

    @app.route("/api/jobs")
    def get_jobs():
        """
        Retrieve jobs with filtering and weighted scoring.

        Route: GET /api/jobs

        Query Parameters:
            status (str, optional): Filter by job status (new, interested, applied, etc.)
            min_score (int, optional): Minimum baseline score (0-100)
            show_hidden (bool, optional): Include hidden jobs (default: false)

        Returns:
            JSON response with:
            - jobs: List of job dictionaries with weighted_score calculated
            - stats: Statistics (total, new, interested, applied, avg_score)

        Jobs are sorted by weighted score (70% qualification, 30% recency).

        Examples:
            GET /api/jobs?status=new&min_score=70
            GET /api/jobs?show_hidden=true
        """
        try:
            status = request.args.get("status", "")
            min_score = int(request.args.get("min_score", 0))
            show_hidden = request.args.get("show_hidden", "false") == "true"

            conn = get_db()

            # Build query with followup count via LEFT JOIN subquery
            base_query = """
                SELECT j.*,
                       COALESCE(f.followup_count, 0) as followup_count
                FROM jobs j
                LEFT JOIN (
                    SELECT job_id, COUNT(*) as followup_count
                    FROM followups
                    GROUP BY job_id
                ) f ON j.job_id = f.job_id
                WHERE j.is_filtered = 0
            """
            params = []

            if not show_hidden:
                base_query += " AND j.status != 'hidden'"

            if status:
                base_query += " AND j.status = ?"
                params.append(status)
            if min_score:
                base_query += " AND j.baseline_score >= ?"
                params.append(min_score)

            # Fetch all matching jobs
            jobs = [dict(row) for row in conn.execute(base_query, params).fetchall()]

            # Calculate weighted scores and sort
            for job in jobs:
                job["weighted_score"] = calculate_weighted_score(
                    job.get("baseline_score", 0), job.get("email_date", job.get("created_at", ""))
                )

            jobs.sort(key=lambda x: x["weighted_score"], reverse=True)

            # Stats
            all_jobs = [
                dict(row)
                for row in conn.execute(
                    "SELECT status, baseline_score FROM jobs WHERE is_filtered = 0 AND status != 'hidden'"
                ).fetchall()
            ]
            stats = {
                "total": len(all_jobs),
                "new": len([j for j in all_jobs if j["status"] == "new"]),
                "interested": len([j for j in all_jobs if j["status"] == "interested"]),
                "applied": len([j for j in all_jobs if j["status"] == "applied"]),
                "avg_score": (
                    sum(j["baseline_score"] or 0 for j in all_jobs) / len(all_jobs)
                    if all_jobs
                    else 0
                ),
            }

            conn.close()
            return jsonify({"jobs": jobs, "stats": stats})
        except ValueError as e:
            logger.error(f"❌ Invalid parameter in /api/jobs: {e}")
            return jsonify({"error": "Invalid parameters"}), 400
        except Exception as e:
            logger.error(f"❌ Error in /api/jobs: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/jobs/<job_id>", methods=["GET"])
    def get_job(job_id):
        """
        Get a single job by ID with all details.

        Route: GET /api/jobs/{job_id}

        Returns:
            JSON: {job: {job_id, title, company, location, score, status, ...}}
        """
        conn = get_db()
        try:
            job = conn.execute(
                """
                SELECT
                    j.*,
                    j.score as score,
                    j.baseline_score as baseline_score
                FROM jobs j
                WHERE j.job_id = ?
                """,
                (job_id,),
            ).fetchone()

            if job:
                job_dict = dict(job)
                # Parse analysis JSON if present
                if job_dict.get("analysis"):
                    try:
                        import json

                        job_dict["analysis"] = json.loads(job_dict["analysis"])
                    except:
                        pass
                return jsonify({"job": job_dict})
            else:
                return jsonify({"error": "Job not found"}), 404
        finally:
            conn.close()

    @app.route("/api/jobs/<job_id>", methods=["PATCH"])
    def update_job(job_id):
        """
        Update job fields (status, notes, viewed flag, etc.).

        Route: PATCH /api/jobs/{job_id}

        Request Body (JSON):
            Any of: status, notes, viewed, applied_date, interview_date

        Behavior:
            - Updates specified fields in jobs table
            - Sets updated_at timestamp
            - Syncs status to linked external_applications if exists

        Returns:
            JSON: {success: true}

        Examples:
            PATCH /api/jobs/abc123
            {"status": "applied", "notes": "Applied via referral"}
        """
        data = request.json
        conn = get_db()

        # Build update query dynamically
        allowed_fields = ["status", "notes", "viewed", "applied_date", "interview_date"]
        updates = []
        params = []

        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = ?")
                params.append(data[field])

        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(job_id)

            query = f"UPDATE jobs SET {', '.join(updates)} WHERE job_id = ?"
            conn.execute(query, params)

            # If status is being updated and this job is linked to an external application, sync it
            if "status" in data:
                conn.execute(
                    "UPDATE external_applications SET status = ?, updated_at = ? WHERE job_id = ?",
                    (data["status"], datetime.now().isoformat(), job_id),
                )
                logger.debug(
                    f"[Backend] Synced status '{data['status']}' to linked external application"
                )

            conn.commit()

        conn.close()
        return jsonify({"success": True})

    @app.route("/api/jobs/<job_id>/description", methods=["PATCH"])
    def update_job_description(job_id):
        """
        Update job description and automatically rescore the job.

        Route: PATCH /api/jobs/{job_id}/description

        Request body:
            {
                "job_description": "Full job description text..."
            }

        Returns:
            {
                "success": true,
                "new_score": 85,
                "analysis": {...}
            }
        """
        data = request.json
        job_description = data.get("job_description", "").strip()

        if not job_description:
            return jsonify({"error": "Job description cannot be empty"}), 400

        conn = get_db()

        # Update the job description
        conn.execute(
            """
            UPDATE jobs
            SET job_description = ?, updated_at = ?
            WHERE job_id = ?
        """,
            (job_description, datetime.now().isoformat(), job_id),
        )

        # Get the updated job
        job = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()

        if not job:
            conn.close()
            return jsonify({"error": "Job not found"}), 404

        # Auto-rescore with the new description
        try:
            resume_text = get_combined_resume_text()

            # Analyze with the full description
            analysis_result = analyze_job(dict(job), resume_text)

            if analysis_result:
                # Update with new analysis
                conn.execute(
                    """
                    UPDATE jobs
                    SET analysis = ?,
                        updated_at = ?
                    WHERE job_id = ?
                """,
                    (json.dumps(analysis_result), datetime.now().isoformat(), job_id),
                )

                conn.commit()
                conn.close()

                return jsonify(
                    {
                        "success": True,
                        "new_score": analysis_result.get("qualification_score", 0),
                        "analysis": analysis_result,
                    }
                )
            else:
                conn.close()
                return jsonify({"error": "Failed to analyze job"}), 500

        except Exception as e:
            logger.error(f"Error rescoring job: {e}")
            conn.close()
            return jsonify({"error": str(e)}), 500

    @app.route("/api/jobs/<job_id>", methods=["DELETE"])
    def delete_job(job_id):
        """
        Delete a job and all associated data.

        Tracks deleted jobs by URL to prevent re-scanning the same job.
        """
        conn = get_db()

        # Get the job details before deleting
        job = conn.execute(
            "SELECT title, company, url FROM jobs WHERE job_id = ?", (job_id,)
        ).fetchone()

        if job and job["url"]:
            # Track this deletion to prevent re-scanning
            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO deleted_jobs (job_url, title, company, deleted_at, deleted_reason)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        job["url"],
                        job["title"],
                        job["company"],
                        datetime.now().isoformat(),
                        "user_deleted",
                    ),
                )
            except Exception as e:
                logger.warning(f"Failed to track deleted job: {e}")

        # Delete the job
        conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))

        # Also delete any linked external applications
        conn.execute("DELETE FROM external_applications WHERE job_id = ?", (job_id,))

        # Delete any resume usage logs for this job
        conn.execute("DELETE FROM resume_usage_log WHERE job_id = ?", (job_id,))

        conn.commit()
        conn.close()

        return jsonify({"success": True})

    @app.route("/api/scan", methods=["POST"])
    def api_scan():
        """
        Unified three-phase scan pipeline with store-then-enrich flow.

        Route: POST /api/scan

        Process:
            Phase 1: Fetch job alert emails from known sources
            Phase 2: Detect follow-up emails (confirmations, interviews, rejections)
            Phase 3: Discover potential new job alert sources

            For Phase 1 jobs:
            1. Quick rule-based filter (location, seniority)
            2. Store jobs with enrichment_status='pending' (no AI scoring yet)
            3. Follow-ups from Phase 2 are stored in followups table
            4. Return quickly — enrichment + scoring happens via /api/enrich-pending

        Returns:
            JSON with:
            - found: Total jobs extracted from emails
            - stored: Jobs stored pending enrichment
            - filtered: Jobs filtered out by rules
            - duplicates: Jobs already in database
            - followups_found: Follow-up emails detected
            - followups_new: New follow-ups stored
            - followups_jobs_created: Jobs created from cold applications
            - sources_discovered: New job alert sources discovered

        Raises:
            400: If no resumes found

        Examples:
            POST /api/scan
            Response: {"found": 45, "stored": 12, "filtered": 28, ...}
        """
        scan_result = scan_emails()
        jobs = scan_result["jobs"]
        followups = scan_result["followups"]

        resume_text = load_resumes()
        if not resume_text:
            return (
                jsonify({"error": "No resumes found. Add .txt/.md files to resumes/ folder"}),
                400,
            )

        # --- Store Phase 1 jobs (filter first, then store without AI scoring) ---
        conn = get_db()
        stored_count = 0
        filtered_count = 0
        duplicate_count = 0

        try:
            for job in jobs:
                # Check duplicates
                existing = conn.execute(
                    """
                    SELECT 1 FROM jobs
                    WHERE job_id = ?
                    OR url = ?
                    OR (company = ? AND title = ?)
                """,
                    (job["job_id"], job["url"], job["company"], job["title"]),
                ).fetchone()
                if existing:
                    duplicate_count += 1
                    continue

                # Check previously deleted
                deleted_check = conn.execute(
                    "SELECT id FROM deleted_jobs WHERE job_url = ?", (job["url"],)
                ).fetchone()
                if deleted_check:
                    continue

                # Quick rule-based AI filter (location + seniority)
                keep, baseline_score, reason = ai_filter_and_score(job, resume_text)

                if keep:
                    conn.execute(
                        """
                        INSERT INTO jobs (job_id, title, company, location, url, source, raw_text,
                                         baseline_score, created_at, updated_at, email_date,
                                         is_filtered, enrichment_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'pending')
                    """,
                        (
                            job["job_id"],
                            job["title"],
                            job["company"],
                            job["location"],
                            job["url"],
                            job["source"],
                            job["raw_text"],
                            baseline_score,
                            job["created_at"],
                            datetime.now().isoformat(),
                            job.get("email_date", job["created_at"]),
                        ),
                    )
                    conn.commit()
                    stored_count += 1
                    logger.info(
                        f"Stored (pending enrichment): {job['title'][:50]} - Score {baseline_score}"
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO jobs (job_id, title, company, location, url, source, raw_text,
                                         baseline_score, created_at, updated_at, email_date,
                                         is_filtered, notes, enrichment_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, 'skipped')
                    """,
                        (
                            job["job_id"],
                            job["title"],
                            job["company"],
                            job["location"],
                            job["url"],
                            job["source"],
                            job["raw_text"],
                            baseline_score,
                            job["created_at"],
                            datetime.now().isoformat(),
                            job.get("email_date", job["created_at"]),
                            reason,
                        ),
                    )
                    conn.commit()
                    filtered_count += 1
        finally:
            conn.close()

        # --- Store Phase 2 follow-ups ---
        conn = get_db()
        followups_new = 0
        updated_jobs = 0
        try:
            for followup in followups:
                gmail_msg_id = followup.get("gmail_message_id")
                if gmail_msg_id:
                    existing = conn.execute(
                        "SELECT id FROM followups WHERE gmail_message_id = ?", (gmail_msg_id,)
                    ).fetchone()
                else:
                    existing = conn.execute(
                        "SELECT id FROM followups WHERE company = ? AND subject = ? AND email_date = ?",
                        (followup["company"], followup["subject"], followup["email_date"]),
                    ).fetchone()

                if existing:
                    continue

                conn.execute(
                    """INSERT INTO followups (
                        company, subject, type, snippet, email_date, job_id, created_at,
                        gmail_message_id, sender_email, ai_summary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        followup["company"],
                        followup["subject"],
                        followup["type"],
                        followup["snippet"],
                        followup["email_date"],
                        followup["job_id"],
                        datetime.now().isoformat(),
                        followup.get("gmail_message_id"),
                        followup.get("sender_email"),
                        f"{followup['type'].title()} from {followup['company']}"
                        + (f" for {followup.get('role')}" if followup.get("role") else ""),
                    ),
                )
                conn.commit()
                followups_new += 1

                # Auto-update job status if matched
                if followup["job_id"]:
                    job = conn.execute(
                        "SELECT status FROM jobs WHERE job_id = ?", (followup["job_id"],)
                    ).fetchone()
                    if job:
                        current_status = job[0]
                        new_status = current_status
                        if followup["type"] == "rejection" and current_status != "rejected":
                            new_status = "rejected"
                        elif followup["type"] == "interview" and current_status not in [
                            "interviewing",
                            "offered",
                            "accepted",
                        ]:
                            new_status = "interviewing"
                        elif followup["type"] == "offer" and current_status not in [
                            "offered",
                            "accepted",
                        ]:
                            new_status = "offered"

                        if new_status != current_status:
                            conn.execute(
                                "UPDATE jobs SET status = ?, updated_at = ? WHERE job_id = ?",
                                (new_status, datetime.now().isoformat(), followup["job_id"]),
                            )
                            conn.commit()
                            updated_jobs += 1
        finally:
            conn.close()

        logger.info(
            f"Scan Summary: {len(jobs)} found, {stored_count} stored, "
            f"{filtered_count} filtered, {duplicate_count} dupes, "
            f"{len(followups)} follow-ups, {scan_result['phase3_discoveries']} discoveries"
        )

        return jsonify(
            {
                "found": len(jobs),
                "stored": stored_count,
                "filtered": filtered_count,
                "duplicates": duplicate_count,
                "pending_enrichment": stored_count,
                "followups_found": len(followups),
                "followups_new": followups_new,
                "followups_jobs_created": scan_result["phase2_jobs_created"],
                "followups_updated_jobs": updated_jobs,
                "sources_discovered": scan_result["phase3_discoveries"],
                "cleaned_emails": scan_result["cleaned_emails"],
            }
        )

    @app.route("/api/analyze", methods=["POST"])
    def api_analyze():
        """
        Run full AI analysis on unanalyzed jobs.

        Route: POST /api/analyze

        Process:
            1. Finds jobs where score=0 or NULL (not yet analyzed)
            2. Runs detailed analyze_job() on each
            3. Stores qualification_score and detailed analysis
            4. Sets status to 'interested' if should_apply=true

        Only analyzes jobs that:
            - Passed initial AI filter (is_filtered=0)
            - Don't have a qualification score yet

        Returns:
            JSON: {analyzed: number of jobs analyzed}

        Raises:
            400: If no resumes found

        Examples:
            POST /api/analyze
            Response: {"analyzed": 8}
        """
        resume_text = load_resumes()
        if not resume_text:
            return jsonify({"error": "No resumes found"}), 400

        conn = get_db()
        jobs = [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM jobs WHERE is_filtered = 0 AND (score = 0 OR score IS NULL)"
            ).fetchall()
        ]

        for job in jobs:
            logger.info(f"Analyzing: {job['title']}")
            analysis = analyze_job(job, resume_text)

            # Only change status if it's still 'new', otherwise preserve user's choice
            new_status = job["status"]
            if job["status"] == "new":
                new_status = "interested" if analysis.get("should_apply") else "new"

            conn.execute(
                "UPDATE jobs SET score = ?, analysis = ?, status = ?, updated_at = ? WHERE job_id = ?",
                (
                    analysis.get("qualification_score", 0),
                    json.dumps(analysis),
                    new_status,
                    datetime.now().isoformat(),
                    job["job_id"],
                ),
            )
            conn.commit()

        conn.close()
        return jsonify({"analyzed": len(jobs)})

    @app.route("/api/score-jobs", methods=["POST"])
    def api_score_jobs():
        """
        Re-score existing jobs that lack baseline scores.

        Route: POST /api/score-jobs

        Use case: Backfill scores for old jobs or jobs imported without scoring.

        Process:
            1. Finds jobs with score=0 or NULL and is_filtered=0
            2. Runs ai_filter_and_score() on each
            3. Updates score and notes with reasoning

        Returns:
            JSON with:
            - scored: Number of jobs scored
            - total: Total jobs found needing scores

        Raises:
            400: If no resumes found

        Examples:
            POST /api/score-jobs
            Response: {"scored": 15, "total": 15}
        """
        resume_text = load_resumes()
        if not resume_text:
            return jsonify({"error": "No resumes found"}), 400

        conn = get_db()
        # Get jobs that don't have scores yet
        jobs = [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM jobs WHERE (score = 0 OR score IS NULL) AND is_filtered = 0"
            ).fetchall()
        ]

        scored_count = 0
        for job in jobs:
            try:
                # Use AI to score the job
                _, baseline_score, reason = ai_filter_and_score(job, resume_text)

                # Update job with new score
                conn.execute(
                    "UPDATE jobs SET score = ?, notes = ?, updated_at = ? WHERE job_id = ?",
                    (baseline_score, reason, datetime.now().isoformat(), job["job_id"]),
                )
                conn.commit()
                scored_count += 1
                logger.info(f"✓ Scored: {job['title'][:50]} - Score {baseline_score}")
            except Exception as e:
                logger.error(f"❌ Error scoring job {job['job_id']}: {e}")
                continue

        conn.close()
        return jsonify({"scored": scored_count, "total": len(jobs)})

    @app.route("/api/scan-followups", methods=["POST"])
    def api_scan_followups():
        """
        Scan Gmail for application follow-up emails.

        Route: POST /api/scan-followups

        Scans last 30 days of Gmail (including spam folder) for:
            - Interview requests
            - Rejection emails
            - Job offers
            - Application confirmations
            - Coding assessments

        Process:
            1. Calls scan_followup_emails() to extract follow-ups
            2. Classifies each email type using keyword matching
            3. Fuzzy matches company names to jobs in database
            4. Stores in followups table
            5. Auto-updates job status if matched:
               - 'rejection' → status='rejected'
               - 'interview' → status='interviewing'
               - 'offer' → status='offered'

        Returns:
            JSON with:
            - found: Total follow-ups found
            - new: New follow-ups added to database
            - updated_jobs: Number of jobs auto-updated

        Examples:
            POST /api/scan-followups
            Response: {"found": 12, "new": 8, "updated_jobs": 5}
        """
        followups = scan_followup_emails(days_back=30)

        conn = get_db()
        new_count = 0
        updated_jobs = 0

        try:
            for followup in followups:
                # Check if this follow-up already exists (by gmail_message_id or company+subject+date)
                gmail_msg_id = followup.get("gmail_message_id")
                if gmail_msg_id:
                    existing = conn.execute(
                        "SELECT id FROM followups WHERE gmail_message_id = ?", (gmail_msg_id,)
                    ).fetchone()
                else:
                    existing = conn.execute(
                        "SELECT id FROM followups WHERE company = ? AND subject = ? AND email_date = ?",
                        (followup["company"], followup["subject"], followup["email_date"]),
                    ).fetchone()

                if existing:
                    continue  # Skip duplicates

                # Insert follow-up into database with expanded fields
                conn.execute(
                    """INSERT INTO followups (
                        company, subject, type, snippet, email_date, job_id, created_at,
                        gmail_message_id, sender_email, ai_summary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        followup["company"],
                        followup["subject"],
                        followup["type"],
                        followup["snippet"],
                        followup["email_date"],
                        followup["job_id"],
                        datetime.now().isoformat(),
                        followup.get("gmail_message_id"),
                        followup.get("sender_email"),
                        f"{followup['type'].title()} from {followup['company']}"
                        + (f" for {followup.get('role')}" if followup.get("role") else ""),
                    ),
                )
                conn.commit()
                new_count += 1

                # Auto-update job status if matched
                if followup["job_id"]:
                    job = conn.execute(
                        "SELECT status FROM jobs WHERE job_id = ?", (followup["job_id"],)
                    ).fetchone()

                    if job:
                        current_status = job[0]
                        new_status = current_status

                        # Update status based on follow-up type
                        if followup["type"] == "rejection" and current_status != "rejected":
                            new_status = "rejected"
                        elif followup["type"] == "interview" and current_status not in [
                            "interviewing",
                            "offered",
                            "accepted",
                        ]:
                            new_status = "interviewing"
                        elif followup["type"] == "offer" and current_status not in [
                            "offered",
                            "accepted",
                        ]:
                            new_status = "offered"

                        if new_status != current_status:
                            conn.execute(
                                "UPDATE jobs SET status = ?, updated_at = ? WHERE job_id = ?",
                                (new_status, datetime.now().isoformat(), followup["job_id"]),
                            )
                            conn.commit()
                            updated_jobs += 1
                            logger.info(f"✓ Updated {followup['company']} → {new_status}")

        finally:
            conn.close()

        return jsonify({"found": len(followups), "new": new_count, "updated_jobs": updated_jobs})

    @app.route("/api/followups", methods=["GET"])
    def api_get_followups():
        """
        Retrieve all follow-up emails with statistics.

        Route: GET /api/followups

        Returns:
            JSON with:
            - followups: List of follow-up dictionaries (with job title/company if linked)
            - stats: Statistics object with:
              - total: Total follow-ups
              - interviews: Count of interview requests
              - rejections: Count of rejections
              - offers: Count of offers
              - assessments: Count of coding challenges
              - response_rate: Percentage (total_followups / applied_jobs * 100)

        Limit: Returns last 100 follow-ups only

        Examples:
            GET /api/followups
        """
        conn = get_db()

        followups = conn.execute("""
            SELECT f.*, j.title, j.company as job_company, j.url
            FROM followups f
            LEFT JOIN jobs j ON f.job_id = j.job_id
            ORDER BY f.email_date DESC
            LIMIT 100
        """).fetchall()

        # Calculate statistics
        stats = {
            "total": len(followups),
            "interviews": len([f for f in followups if f["type"] == "interview"]),
            "rejections": len([f for f in followups if f["type"] == "rejection"]),
            "offers": len([f for f in followups if f["type"] == "offer"]),
            "assessments": len([f for f in followups if f["type"] == "assessment"]),
        }

        # Calculate response rate
        applied_count = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status IN ('applied', 'interviewing', 'offered', 'rejected')"
        ).fetchone()[0]
        if applied_count > 0:
            stats["response_rate"] = round((stats["total"] / applied_count) * 100, 1)
        else:
            stats["response_rate"] = 0

        conn.close()

        return jsonify({"followups": [dict(row) for row in followups], "stats": stats})

    @app.route("/api/followups/actions", methods=["GET"])
    def get_followup_actions():
        """
        Get followups that require action, sorted by deadline.

        Route: GET /api/followups/actions

        Returns:
            JSON with:
            - actions: List of followups with action_required=1
            - count: Total number of pending actions
        """
        conn = get_db()
        actions = conn.execute("""
            SELECT f.*, j.title, j.company as job_company, j.url
            FROM followups f
            LEFT JOIN jobs j ON f.job_id = j.job_id
            WHERE f.action_required = 1
            ORDER BY f.action_deadline ASC, f.email_date DESC
        """).fetchall()
        conn.close()

        return jsonify({"actions": [dict(row) for row in actions], "count": len(actions)})

    @app.route("/api/followups/<int:followup_id>/read", methods=["PATCH"])
    def mark_followup_read(followup_id):
        """
        Mark a followup as read.

        Route: PATCH /api/followups/<id>/read

        Returns:
            JSON with success status
        """
        conn = get_db()
        conn.execute("UPDATE followups SET is_read = 1 WHERE id = ?", (followup_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})

    @app.route("/api/followups/<int:followup_id>/reclassify", methods=["PATCH"])
    def reclassify_followup(followup_id):
        """
        Reclassify a followup email type.

        Route: PATCH /api/followups/<id>/reclassify

        Request Body:
            type (str): New classification type

        Returns:
            JSON with success status
        """
        data = request.json
        new_type = data.get("type", "").strip()

        if not new_type:
            return jsonify({"error": "Type is required"}), 400

        valid_types = ["interview", "rejection", "received", "offer", "assessment", "update"]
        if new_type not in valid_types:
            return jsonify({"error": f"Invalid type. Must be one of: {valid_types}"}), 400

        conn = get_db()
        conn.execute("UPDATE followups SET type = ? WHERE id = ?", (new_type, followup_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "type": new_type})

    @app.route("/api/jobs/<job_id>/cover-letter", methods=["POST"])
    def api_cover_letter(job_id):
        """
        Generate tailored cover letter for a specific job.

        Route: POST /api/jobs/{job_id}/cover-letter

        Uses Claude AI to create a personalized cover letter based on:
            - Job description and requirements
            - User's resume content
            - Previous AI analysis strengths

        Generated cover letters:
            - 3-4 paragraphs, under 350 words
            - Professional but enthusiastic tone
            - Only cite actual resume experience
            - Include specific examples and metrics

        Stores generated cover letter in database for future reference.

        Returns:
            JSON: {cover_letter: string}

        Examples:
            POST /api/jobs/abc123/cover-letter
        """
        resume_text = load_resumes()
        conn = get_db()
        job = dict(conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone())

        cover_letter = generate_cover_letter(job, resume_text)
        conn.execute(
            "UPDATE jobs SET cover_letter = ?, updated_at = ? WHERE job_id = ?",
            (cover_letter, datetime.now().isoformat(), job_id),
        )
        conn.commit()
        conn.close()
        return jsonify({"cover_letter": cover_letter})

    @app.route("/api/jobs/<job_id>/activity", methods=["GET"])
    def get_job_activity(job_id):
        """
        Get email activity timeline for a specific job.

        Route: GET /api/jobs/{job_id}/activity

        Returns:
            JSON: {activities: [{type, subject, date, classification, snippet}, ...]}

        The classification field contains: "interview", "offer", "rejection", "update"
        Activities are sorted by date descending (most recent first).
        """
        conn = get_db()
        try:
            # Get followups linked to this job
            followups = conn.execute(
                """
                SELECT
                    type,
                    subject,
                    email_date as date,
                    snippet,
                    type as classification,
                    company
                FROM followups
                WHERE job_id = ?
                ORDER BY email_date DESC
                """,
                (job_id,),
            ).fetchall()

            activities = []
            for row in followups:
                activity = dict(row)
                # Normalize classification
                classification = (activity.get("type") or "").lower()
                if "interview" in classification:
                    activity["classification"] = "interview"
                elif "offer" in classification:
                    activity["classification"] = "offer"
                elif "reject" in classification or "declined" in classification:
                    activity["classification"] = "rejection"
                else:
                    activity["classification"] = "update"
                activities.append(activity)

            return jsonify({"activities": activities})
        except Exception as e:
            logger.error(f"Error fetching job activity: {e}")
            return jsonify({"activities": [], "error": str(e)})
        finally:
            conn.close()

    # ===================================================================
    # Debug Scan Endpoint
    # ===================================================================

    @app.route("/api/debug-scan", methods=["POST"])
    def api_debug_scan():
        """
        Debug scan: process the N most recent emails with full verbose logging.

        Route: POST /api/debug-scan

        Request Body (optional JSON):
            - count: Number of recent emails to process (default 10, max 25)
            - days_back: How many days to look back (default 7)

        Returns:
            JSON with:
            - log_file: Path to the generated debug log file
            - emails_processed: Number of emails examined
            - results: Array of per-email debug info
        """
        import io
        import textwrap
        from app.email.scanner import (
            _html_to_text,
            _get_headers,
            normalize_sender,
            extract_sender_name,
            classify_followup_email,
            extract_company_from_email,
            extract_role_from_subject,
            _matches_any_source,
            _load_email_sources,
        )
        from app.email.client import get_gmail_service, get_email_body
        from app.database import is_email_processed

        data = request.get_json() or {}
        count = min(data.get("count", 10), 25)
        days_back = data.get("days_back", 7)

        after_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")

        log_lines = []

        def log(msg, indent=0):
            prefix = "  " * indent
            line = f"{prefix}{msg}"
            log_lines.append(line)
            logger.debug(f"[DEBUG-SCAN] {line}")

        log(f"=== Hammy Debug Scan ===")
        log(f"Timestamp: {datetime.now().isoformat()}")
        log(f"Looking back {days_back} days (after {after_date})")
        log(f"Processing up to {count} emails")
        log("")

        try:
            service = get_gmail_service()
        except Exception as e:
            return jsonify({"error": f"Gmail auth failed: {e}"}), 500

        email_sources = _load_email_sources()
        log(f"Loaded {len(email_sources)} email sources:")
        for src in email_sources:
            log(f"- {src['name']} ({src.get('sender_email', src.get('sender_pattern', 'N/A'))})", 1)
        log("")

        # Fetch most recent emails (broad query)
        queries = [
            f"after:{after_date}",
        ]

        all_msg_ids = []
        for q in queries:
            try:
                results = (
                    service.users().messages().list(userId="me", q=q, maxResults=count).execute()
                )
                for m in results.get("messages", []):
                    if m["id"] not in [x["id"] for x in all_msg_ids]:
                        all_msg_ids.append(m)
            except Exception as e:
                log(f"ERROR fetching emails: {e}")

        all_msg_ids = all_msg_ids[:count]
        log(f"Fetched {len(all_msg_ids)} message IDs from Gmail")
        log("")

        # Load resume for scoring context
        resume_text = load_resumes()

        results = []
        for idx, msg_info in enumerate(all_msg_ids):
            msg_id = msg_info["id"]
            log(f"--- Email {idx + 1}/{len(all_msg_ids)} (ID: {msg_id}) ---")

            email_result = {
                "msg_id": msg_id,
                "index": idx + 1,
            }

            try:
                message = (
                    service.users().messages().get(userId="me", id=msg_id, format="full").execute()
                )

                hdrs = _get_headers(message)
                subject = hdrs.get("subject", "(no subject)")
                from_raw = hdrs.get("from", "(unknown)")
                sender = normalize_sender(from_raw)
                display_name = extract_sender_name(from_raw)
                snippet = message.get("snippet", "")
                email_date = datetime.fromtimestamp(
                    int(message.get("internalDate", 0)) / 1000
                ).isoformat()

                log(f"From:     {from_raw}")
                log(f"Sender:   {sender}")
                log(f"Display:  {display_name}")
                log(f"Subject:  {subject}")
                log(f"Date:     {email_date}")
                log(f"Snippet:  {snippet[:200]}...")
                log("")

                email_result.update(
                    {
                        "from": from_raw,
                        "sender": sender,
                        "display_name": display_name,
                        "subject": subject,
                        "date": email_date,
                        "snippet": snippet[:300],
                    }
                )

                # Check if already processed
                already = is_email_processed(msg_id)
                log(f"Already processed: {already}")
                email_result["already_processed"] = already

                # Check if matches a known source
                matches_source = _matches_any_source(sender, email_sources)
                matched_source_name = None
                if matches_source:
                    for src in email_sources:
                        se = (src.get("sender_email") or "").lower()
                        if se and se in sender.lower():
                            matched_source_name = src["name"]
                            break
                log(
                    f"Matches known source: {matches_source}"
                    + (f" ({matched_source_name})" if matched_source_name else "")
                )
                email_result["matches_known_source"] = matches_source
                email_result["matched_source"] = matched_source_name

                # Get full body
                body_html = get_email_body(message.get("payload", {}))
                body_text = _html_to_text(body_html) if body_html else ""
                body_len = len(body_text)
                log(f"Body length: {body_len} chars")
                if body_text:
                    log(f"Body preview (first 500 chars):")
                    for line in textwrap.wrap(body_text[:500], width=100):
                        log(f"  {line}", 1)
                log("")
                email_result["body_length"] = body_len
                email_result["body_preview"] = body_text[:500]

                # Classify
                email_type = classify_followup_email(subject, snippet, body_text)
                log(f"Classification: {email_type}")
                email_result["classification"] = email_type

                # Extract company
                company = extract_company_from_email(from_raw, subject)
                log(f"Extracted company: {company}")
                email_result["company"] = company

                # Extract role
                role = extract_role_from_subject(subject)
                log(f"Extracted role: {role}")
                email_result["role"] = role

                # AI scoring (if resume available and it's a job-like email)
                if resume_text and matches_source:
                    log(f"AI scoring context:")
                    job_stub = {
                        "title": subject[:100],
                        "company": company,
                        "location": "Unknown",
                        "raw_text": body_text[:500] if body_text else snippet[:300],
                    }
                    try:
                        keep, score, reason = ai_filter_and_score(job_stub, resume_text)
                        log(f"  Keep: {keep}")
                        log(f"  Score: {score}")
                        log(f"  Reason: {reason}")
                        email_result["ai_keep"] = keep
                        email_result["ai_score"] = score
                        email_result["ai_reason"] = reason
                    except Exception as e:
                        log(f"  AI scoring error: {e}")
                        email_result["ai_error"] = str(e)

                log("")
                email_result["status"] = "ok"

            except Exception as e:
                log(f"ERROR processing email {msg_id}: {e}")
                email_result["status"] = "error"
                email_result["error"] = str(e)

            results.append(email_result)

        # Write log file
        log("")
        log(f"=== Debug Scan Complete ===")
        log(f"Processed {len(results)} emails")

        log_content = "\n".join(log_lines)
        log_filename = f"debug_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_path = os.path.join(APP_DIR, log_filename)

        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(log_content)
            logger.info(f"Debug scan log written to {log_path}")
        except Exception as e:
            logger.error(f"Failed to write debug log: {e}")
            log_path = None

        return jsonify(
            {
                "emails_processed": len(results),
                "log_file": log_path,
                "log_content": log_content,
                "results": results,
            }
        )

    # ===================================================================
    # Enrich-Pending Endpoint
    # ===================================================================

    @app.route("/api/enrich-pending", methods=["POST"])
    def api_enrich_pending():
        """
        Enrich and re-score jobs that have enrichment_status='pending'.

        Route: POST /api/enrich-pending

        Process:
            1. Finds jobs with enrichment_status='pending' and is_filtered=0
            2. For each: runs web search enrichment (salary, description, URL)
            3. Re-scores based on enriched data
            4. Updates enrichment_status to 'complete' or 'failed'

        Query Params:
            - max: Maximum jobs to enrich (default 10)
            - min_score: Minimum baseline_score threshold (default 0)

        Returns:
            JSON with enrichment results
        """
        max_jobs = request.args.get("max", 10, type=int)
        min_score = request.args.get("min_score", 0, type=int)

        try:
            from app.enrichment.pipeline import enrich_job

            conn = get_db()
            pending = conn.execute(
                """
                SELECT job_id, title, company, baseline_score
                FROM jobs
                WHERE enrichment_status = 'pending'
                  AND is_filtered = 0
                  AND baseline_score >= ?
                ORDER BY baseline_score DESC
                LIMIT ?
            """,
                (min_score, max_jobs),
            ).fetchall()
            conn.close()

            results = []
            successful = 0
            failed = 0

            for job in pending:
                job_id = job["job_id"]
                result = enrich_job(job_id)
                results.append(
                    {
                        "job_id": job_id,
                        "title": job["title"],
                        "company": job["company"],
                        "success": result.get("success", False),
                        "enriched_fields": result.get("enriched_fields", []),
                        "new_score": result.get("new_score"),
                    }
                )

                # Update enrichment_status
                conn = get_db()
                status = "complete" if result.get("success") else "failed"
                conn.execute(
                    "UPDATE jobs SET enrichment_status = ? WHERE job_id = ?",
                    (status, job_id),
                )
                conn.commit()
                conn.close()

                if result.get("success"):
                    successful += 1
                else:
                    failed += 1

            return jsonify(
                {
                    "total": len(results),
                    "successful": successful,
                    "failed": failed,
                    "results": results,
                }
            )
        except Exception as e:
            logger.error(f"Error in enrich-pending: {e}")
            return jsonify({"error": str(e)}), 500

    # ===================================================================
    # Discovered Sources Endpoints
    # ===================================================================

    @app.route("/api/discovered-sources", methods=["GET"])
    def api_get_discovered_sources():
        """
        Get discovered email sources pending review.

        Route: GET /api/discovered-sources

        Query Params:
            - status: Filter by status (default 'pending'). Use 'all' for all.

        Returns:
            JSON with sources list and count
        """
        import json as json_module

        status_filter = request.args.get("status", "pending")
        conn = get_db()
        try:
            if status_filter == "all":
                rows = conn.execute(
                    "SELECT * FROM discovered_email_sources ORDER BY email_count DESC"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM discovered_email_sources WHERE status = ? ORDER BY email_count DESC",
                    (status_filter,),
                ).fetchall()

            sources = []
            for row in rows:
                source = dict(row)
                # Parse sample_subjects from JSON string
                if source.get("sample_subjects"):
                    try:
                        source["sample_subjects"] = json_module.loads(source["sample_subjects"])
                    except (json_module.JSONDecodeError, TypeError):
                        source["sample_subjects"] = []
                else:
                    source["sample_subjects"] = []
                sources.append(source)

            return jsonify({"sources": sources, "count": len(sources)})
        finally:
            conn.close()

    @app.route("/api/discovered-sources/<int:source_id>/add", methods=["POST"])
    def api_add_discovered_source(source_id):
        """
        Convert a discovered source into a configured email source.

        Route: POST /api/discovered-sources/<id>/add
        """
        from app.database import detect_parser_type

        conn = get_db()
        try:
            discovered = conn.execute(
                "SELECT * FROM discovered_email_sources WHERE id = ?", (source_id,)
            ).fetchone()

            if not discovered:
                return jsonify({"error": "Not found"}), 404

            if discovered["status"] == "added":
                return jsonify({"error": "Source already added"}), 400

            parser_type = detect_parser_type(discovered["sender_email"])
            name = (
                discovered["sender_name"]
                or discovered["sender_email"].split("@")[1].split(".")[0].title()
            )
            now = datetime.now().isoformat()

            conn.execute(
                """
                INSERT INTO custom_email_sources
                (name, sender_email, parser_class, enabled, is_builtin, created_at, updated_at)
                VALUES (?, ?, ?, 1, 0, ?, ?)
            """,
                (name, discovered["sender_email"], parser_type, now, now),
            )

            conn.execute(
                "UPDATE discovered_email_sources SET status = 'added', updated_at = ? WHERE id = ?",
                (now, source_id),
            )
            conn.commit()

            return jsonify({"success": True, "name": name, "parser_type": parser_type})
        except Exception as e:
            logger.error(f"Error adding discovered source: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

    @app.route("/api/discovered-sources/<int:source_id>/dismiss", methods=["POST"])
    def api_dismiss_discovered_source(source_id):
        """
        Dismiss a discovered source so it doesn't appear again.

        Route: POST /api/discovered-sources/<id>/dismiss
        """
        conn = get_db()
        try:
            conn.execute(
                "UPDATE discovered_email_sources SET status = 'dismissed', updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), source_id),
            )
            conn.commit()
            return jsonify({"success": True})
        finally:
            conn.close()

    @app.route("/api/discovered-sources/<int:source_id>/preview", methods=["GET"])
    def api_preview_discovered_source(source_id):
        """
        Preview the sample email from a discovered source.

        Route: GET /api/discovered-sources/<id>/preview
        """
        conn = get_db()
        try:
            discovered = conn.execute(
                "SELECT sample_email_id FROM discovered_email_sources WHERE id = ?",
                (source_id,),
            ).fetchone()
            conn.close()

            if not discovered or not discovered["sample_email_id"]:
                return jsonify({"error": "No sample email available"}), 404

            service = get_gmail_service()
            message = (
                service.users()
                .messages()
                .get(userId="me", id=discovered["sample_email_id"], format="full")
                .execute()
            )

            headers = message.get("payload", {}).get("headers", [])
            subject = ""
            from_addr = ""
            date = ""
            for h in headers:
                if h["name"].lower() == "subject":
                    subject = h["value"]
                elif h["name"].lower() == "from":
                    from_addr = h["value"]
                elif h["name"].lower() == "date":
                    date = h["value"]

            body = get_email_body(message.get("payload", {}))

            return jsonify(
                {
                    "subject": subject,
                    "from": from_addr,
                    "date": date,
                    "body": (body or "")[:5000],
                }
            )
        except Exception as e:
            logger.error(f"Error previewing discovered source: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/capture", methods=["POST"])
    def api_capture():
        """
        Capture job from Chrome extension.

        Route: POST /api/capture

        Request Body (JSON):
            - url: Job posting URL (required)
            - title: Job title (required)
            - company: Company name
            - location: Job location (default: 'Remote')
            - description: Job description text
            - source: Source platform (auto-detected from URL if not provided)

        Process:
            1. Cleans job URL to remove tracking parameters
            2. Auto-detects source from URL (linkedin, indeed, etc.)
            3. Generates job_id from URL/title/company
            4. If job exists: Updates description (if missing)
            5. If new job: Runs AI scoring and saves to database

        Returns:
            JSON with:
            - status: 'created' or 'updated'
            - job_id: Generated job identifier
            - baseline_score: AI-generated score (if created)

        Raises:
            400: If url or title missing

        Examples:
            POST /api/capture
            {"url": "linkedin.com/jobs/123", "title": "Engineer", "company": "Acme"}
        """
        data = request.json

        url = clean_job_url(data.get("url", ""))
        title = data.get("title", "")
        company = data.get("company", "")
        location = data.get("location", "Remote")
        description = data.get("description", "")
        source = data.get("source", "extension")

        # Auto-detect source from URL
        if "linkedin.com" in url:
            source = "linkedin"
        elif "indeed.com" in url:
            source = "indeed"
        elif "weworkremotely.com" in url:
            source = "weworkremotely"

        if not url or not title:
            return jsonify({"error": "url and title required"}), 400

        job_id = generate_job_id(url, title, company)

        conn = get_db()
        existing = conn.execute("SELECT 1 FROM jobs WHERE job_id = ?", (job_id,)).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE jobs SET description = ?, raw_text = ?, updated_at = ?
                WHERE job_id = ? AND (description IS NULL OR description = '')
            """,
                (description[:5000], description[:2000], datetime.now().isoformat(), job_id),
            )
            conn.commit()
            conn.close()
            return jsonify({"status": "updated", "job_id": job_id})

        # New job from extension - add with baseline score
        resume_text = load_resumes()
        baseline_score = 50  # Default

        if resume_text:
            temp_job = {
                "title": title,
                "company": company,
                "location": location,
                "raw_text": description[:500] if description else title,
            }
            keep, baseline_score, reason = ai_filter_and_score(temp_job, resume_text)

        conn.execute(
            """
            INSERT INTO jobs (job_id, title, company, location, url, source, description, raw_text, 
                             baseline_score, created_at, updated_at, is_filtered)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
            (
                job_id,
                title[:200],
                company[:100],
                location[:100],
                url,
                source,
                description[:5000],
                description[:2000],
                baseline_score,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

        return jsonify({"status": "created", "job_id": job_id, "baseline_score": baseline_score})

    @app.route("/api/analyze-instant", methods=["POST"])
    def api_analyze_instant():
        """
        Instant job analysis for Chrome extension.

        Route: POST /api/analyze-instant

        Request Body (JSON):
            - title: Job title (required)
            - company: Company name
            - description: Job description (required)

        Uses Claude AI to provide immediate qualification analysis without
        saving to database. Designed for quick feedback while browsing jobs.

        Analysis includes:
            - qualification_score (1-100)
            - should_apply (boolean)
            - strengths (matching skills from resume)
            - gaps (missing requirements)
            - recommendation (honest assessment)
            - resume_to_use (which variant to submit)

        Returns:
            JSON with:
            - analysis: Full analysis object
            - job: Echo of job title/company

        Raises:
            400: If title or description missing, or no resumes found

        Examples:
            POST /api/analyze-instant
            {"title": "Software Engineer", "company": "Acme", "description": "..."}
        """
        data = request.json

        title = data.get("title", "")
        company = data.get("company", "Unknown")
        description = data.get("description", "")

        if not title or not description:
            return jsonify({"error": "title and description required"}), 400

        resume_text = load_resumes()
        if not resume_text:
            return jsonify({"error": "No resumes found"}), 400

        client = anthropic.Anthropic()

        prompt = f"""Analyze job fit with STRICT ACCURACY. Only mention roles/skills candidate ACTUALLY has.

    CANDIDATE'S RESUME:
    {resume_text}

    JOB LISTING:
    Title: {title}
    Company: {company}
    Description: {description[:2000]}

    CRITICAL RULES:
    1. ONLY cite job titles the candidate has held (check resume carefully)
    2. ONLY mention technologies/tools explicitly in resume
    3. Do NOT invent experience or extrapolate skills
    4. should_apply = true ONLY if score >= 65 AND no major red flags
    5. Red flags: requires 5+ years when candidate has 2, wrong tech stack entirely, senior leadership position

    SCORING:
    - 80-100: Strong match, candidate has done similar work
    - 60-79: Good match, meets most requirements with minor gaps
    - 40-59: Partial match, missing key skills but could learn
    - 20-39: Weak match, significant gaps in experience/skills
    - 1-19: Very poor match, wrong level or domain entirely

    Return ONLY valid JSON:
    {{
        "qualification_score": <1-100>,
        "should_apply": <bool>,
        "strengths": ["actual matching skills from resume", "relevant experience candidate has"],
        "gaps": ["specific missing requirements", "areas to develop"],
        "recommendation": "Honest 2-3 sentence assessment based on actual resume fit",
        "resume_to_use": "backend|cloud|fullstack"
    }}
    """

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text
            match = re.search(r"\{[\s\S]*\}", response_text)

            if match:
                analysis = json.loads(match.group())
            else:
                raise ValueError("No JSON in response")

            return jsonify({"analysis": analysis, "job": {"title": title, "company": company}})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/wwr", methods=["POST"])
    def api_scan_wwr():
        """
        Scan WeWorkRemotely RSS feeds with AI filtering.

        Route: POST /api/wwr

        Process:
            1. Fetches jobs from WWR RSS feeds (last 7 days)
            2. Loads user resumes
            3. Runs AI filter on each job
            4. Saves jobs that pass filter to database
            5. Marks filtered jobs with is_filtered=1

        Returns:
            JSON with:
            - found: Total jobs from RSS feeds
            - new: Jobs added to database
            - filtered: Jobs filtered out by AI
            - duplicates: Jobs already in database

        Raises:
            400: If no resumes found

        Examples:
            POST /api/wwr
            Response: {"found": 30, "new": 8, "filtered": 18, "duplicates": 4}
        """
        logger.info("🌐 Starting WWR scan...")
        jobs = fetch_wwr_jobs()
        logger.info(f"📥 Fetched {len(jobs)} jobs from RSS feeds")

        resume_text = load_resumes()

        if not resume_text:
            return jsonify({"error": "No resumes found"}), 400

        conn = get_db()
        new_count = 0
        filtered_count = 0
        duplicate_count = 0

        try:
            for i, job in enumerate(jobs, 1):
                logger.info(f"Processing {i}/{len(jobs)}: {job['title'][:50]}...")

                existing = conn.execute(
                    "SELECT 1 FROM jobs WHERE job_id = ?", (job["job_id"],)
                ).fetchone()
                if existing:
                    duplicate_count += 1
                    logger.info(f"  ⏭️  Duplicate")
                    continue

                keep, baseline_score, reason = ai_filter_and_score(job, resume_text)

                if keep:
                    conn.execute(
                        """
                        INSERT INTO jobs (job_id, title, company, location, url, source, raw_text,
                                         baseline_score, created_at, updated_at, email_date, is_filtered)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """,
                        (
                            job["job_id"],
                            job["title"],
                            job["company"],
                            job["location"],
                            job["url"],
                            job["source"],
                            job.get("description", job["raw_text"]),
                            baseline_score,
                            job["created_at"],
                            datetime.now().isoformat(),
                            job.get("email_date", job["created_at"]),
                        ),
                    )
                    conn.commit()
                    new_count += 1
                    logger.info(f"  ✓ Kept - Score {baseline_score}")
                else:
                    conn.execute(
                        """
                        INSERT INTO jobs (job_id, title, company, location, url, source, raw_text,
                                         baseline_score, created_at, updated_at, email_date, is_filtered, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                        (
                            job["job_id"],
                            job["title"],
                            job["company"],
                            job["location"],
                            job["url"],
                            job["source"],
                            job.get("description", job["raw_text"]),
                            baseline_score,
                            job["created_at"],
                            datetime.now().isoformat(),
                            job.get("email_date", job["created_at"]),
                            reason,
                        ),
                    )
                    conn.commit()
                    filtered_count += 1
                    logger.info(f"  ✗ Filtered - {reason[:50]}")
        finally:
            conn.close()

        logger.info(
            f"\n✅ WWR Scan Complete: {new_count} new, {filtered_count} filtered, {duplicate_count} duplicates"
        )
        return jsonify(
            {
                "found": len(jobs),
                "new": new_count,
                "filtered": filtered_count,
                "duplicates": duplicate_count,
            }
        )

    @app.route("/api/generate-cover-letter", methods=["POST"])
    def api_generate_cover_letter():
        """
        Generate cover letter from Chrome extension.

        Route: POST /api/generate-cover-letter

        Request Body (JSON):
            - job: Job object with title, company, description
            - analysis: Previous AI analysis with strengths/gaps

        Creates tailored cover letter using:
            - Job description
            - User's resume(s)
            - Verified strengths from analysis

        Cover letter format:
            - 3-4 paragraphs
            - Under 350 words
            - Professional but enthusiastic
            - Only cites actual resume content
            - Specific examples with metrics

        Returns:
            JSON: {cover_letter: string}

        Raises:
            400: If no resumes found
            500: If AI generation fails

        Examples:
            POST /api/generate-cover-letter
            {"job": {...}, "analysis": {...}}
        """
        data = request.json
        job = data.get("job", {})
        analysis = data.get("analysis", {})

        resume_text = load_resumes()
        if not resume_text:
            return jsonify({"error": "No resumes found"}), 400

        client = anthropic.Anthropic()

        strengths = ", ".join(analysis.get("strengths", []))

        prompt = f"""Write a tailored cover letter (3-4 paragraphs, under 350 words).

    CRITICAL: Only mention experience and skills the candidate ACTUALLY has from their resume.

    CANDIDATE'S RESUME:
    {resume_text}

    JOB:
    Title: {job.get('title')}
    Company: {job.get('company')}
    Description: {job.get('description', '')[:1000]}

    KEY STRENGTHS (verified from resume):
    {strengths}

    INSTRUCTIONS:
    1. ONLY cite projects, roles, and technologies from the resume
    2. Use specific examples and metrics from resume
    3. Do NOT invent experience or extrapolate skills
    4. Keep professional but enthusiastic tone
    5. 3-4 paragraphs: opening, 2 body (experience/fit), closing

    Write only the cover letter text (no subject line):"""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            cover_letter = response.content[0].text.strip()
            return jsonify({"cover_letter": cover_letter})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/generate-answer", methods=["POST"])
    def api_generate_answer():
        """
        Generate interview answer using AI.

        Route: POST /api/generate-answer

        Request Body (JSON):
            - question: Interview question (required)
            - job: Job context (title, company, description)
            - analysis: Previous analysis with strengths/gaps

        Uses Claude AI to craft strong interview answers:
            - Only cites actual resume projects/experience
            - Uses specific examples with concrete details
            - 2-3 paragraphs, 150-200 words
            - Natural, conversational tone
            - Honest about gaps but frames positively

        Returns:
            JSON: {answer: string}

        Raises:
            400: If question missing or no resumes found
            500: If AI generation fails

        Examples:
            POST /api/generate-answer
            {"question": "Tell me about a time...", "job": {...}, "analysis": {...}}
        """
        data = request.json
        job = data.get("job", {})
        question = data.get("question")
        analysis = data.get("analysis", {})

        if not question:
            return jsonify({"error": "Question required"}), 400

        resume_text = load_resumes()
        if not resume_text:
            return jsonify({"error": "No resumes found"}), 400

        client = anthropic.Anthropic()

        prompt = f"""Generate a strong interview answer using ONLY actual resume content.

    QUESTION: {question}

    JOB CONTEXT:
    Title: {job.get('title')}
    Company: {job.get('company')}
    Description: {job.get('description', '')[:500]}

    CANDIDATE'S RESUME:
    {resume_text}

    VERIFIED ANALYSIS:
    Strengths: {', '.join(analysis.get('strengths', []))}
    Gaps: {', '.join(analysis.get('gaps', []))}

    CRITICAL RULES:
    1. ONLY cite projects, roles, metrics from the actual resume
    2. Do NOT invent experience or extrapolate skills
    3. Use specific examples with concrete details
    4. Be honest about gaps but frame positively
    5. Natural, conversational tone (not rehearsed)

    Generate 2-3 paragraph answer (150-200 words):"""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}],
            )
            answer = response.content[0].text.strip()
            return jsonify({"answer": answer})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/watchlist", methods=["GET"])
    def get_watchlist():
        """
        Retrieve all watchlist companies.

        Route: GET /api/watchlist

        Returns companies user wants to monitor for future openings,
        sorted by most recently added.

        Returns:
            JSON: {items: List of watchlist dictionaries}

        Examples:
            GET /api/watchlist
        """
        conn = get_db()
        items = [
            dict(row)
            for row in conn.execute("SELECT * FROM watchlist ORDER BY created_at DESC").fetchall()
        ]
        conn.close()
        return jsonify({"items": items})

    @app.route("/api/watchlist", methods=["POST"])
    def add_watchlist():
        """
        Add company to watchlist.

        Route: POST /api/watchlist

        Request Body (JSON):
            - company: Company name (required)
            - url: Career page URL (optional)
            - notes: Notes about when to check back (optional)

        Use case: Track companies not currently hiring or requiring
        specific timing to apply.

        Returns:
            JSON: {success: true}

        Raises:
            400: If company name missing

        Examples:
            POST /api/watchlist
            {"company": "Acme Corp", "url": "acme.com/careers", "notes": "Check Q2"}
        """
        data = request.json
        company = data.get("company", "").strip()
        url = data.get("url", "").strip()
        notes = data.get("notes", "").strip()

        if not company:
            return jsonify({"error": "Company required"}), 400

        conn = get_db()
        conn.execute(
            "INSERT INTO watchlist (company, url, notes, created_at) VALUES (?, ?, ?, ?)",
            (company, url, notes, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True})

    @app.route("/api/watchlist/<int:watch_id>", methods=["DELETE"])
    def delete_watchlist(watch_id):
        """
        Remove company from watchlist.

        Route: DELETE /api/watchlist/{watch_id}

        Returns:
            JSON: {success: true}

        Examples:
            DELETE /api/watchlist/5
        """
        conn = get_db()
        conn.execute("DELETE FROM watchlist WHERE id = ?", (watch_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})

    # ============== Tracked Companies ==============
    @app.route("/api/tracked-companies", methods=["GET"])
    def get_tracked_companies():
        """Get all tracked companies ordered by most recently added."""
        conn = get_db()
        companies = [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM tracked_companies ORDER BY created_at DESC"
            ).fetchall()
        ]
        conn.close()
        return jsonify({"companies": companies})

    @app.route("/api/tracked-companies", methods=["POST"])
    def add_tracked_company():
        """Add a new tracked company."""
        data = request.json
        company_name = data.get("company_name", "").strip()
        career_page_url = data.get("career_page_url", "").strip()
        job_alert_email = data.get("job_alert_email", "").strip()
        notes = data.get("notes", "").strip()

        if not company_name:
            return jsonify({"error": "Company name is required"}), 400

        conn = get_db()
        now = datetime.now().isoformat()
        conn.execute(
            """INSERT INTO tracked_companies
               (company_name, career_page_url, job_alert_email, notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (company_name, career_page_url, job_alert_email, notes, now, now),
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True})

    @app.route("/api/tracked-companies/<int:company_id>", methods=["PATCH"])
    def update_tracked_company(company_id):
        """Update a tracked company."""
        data = request.json
        company_name = data.get("company_name", "").strip()
        career_page_url = data.get("career_page_url", "").strip()
        job_alert_email = data.get("job_alert_email", "").strip()
        notes = data.get("notes", "").strip()

        if not company_name:
            return jsonify({"error": "Company name is required"}), 400

        conn = get_db()
        now = datetime.now().isoformat()
        conn.execute(
            """UPDATE tracked_companies
               SET company_name = ?, career_page_url = ?, job_alert_email = ?, notes = ?, updated_at = ?
               WHERE id = ?""",
            (company_name, career_page_url, job_alert_email, notes, now, company_id),
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True})

    @app.route("/api/tracked-companies/<int:company_id>", methods=["DELETE"])
    def delete_tracked_company(company_id):
        """Delete a tracked company."""
        conn = get_db()
        conn.execute("DELETE FROM tracked_companies WHERE id = ?", (company_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})

    # ============== Email Sources (Built-in + Custom) ==============
    @app.route("/api/email-sources", methods=["GET"])
    def get_email_sources():
        """
        Get all email sources (both built-in and custom).

        Returns sources grouped by category with built-in sources first.
        """
        conn = get_db()
        sources = [dict(row) for row in conn.execute("""SELECT * FROM custom_email_sources
               ORDER BY is_builtin DESC, category, name""").fetchall()]
        conn.close()

        # Group by category
        categories = {}
        for source in sources:
            cat = source.get("category", "custom")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(source)

        return jsonify(
            {
                "sources": sources,
                "categories": categories,
                "total": len(sources),
                "builtin_count": sum(1 for s in sources if s.get("is_builtin")),
                "custom_count": sum(1 for s in sources if not s.get("is_builtin")),
            }
        )

    # Legacy endpoint for backwards compatibility
    @app.route("/api/custom-email-sources", methods=["GET"])
    def get_custom_email_sources():
        """Get all custom email sources (legacy endpoint)."""
        conn = get_db()
        sources = [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM custom_email_sources ORDER BY is_builtin DESC, created_at DESC"
            ).fetchall()
        ]
        conn.close()
        return jsonify({"sources": sources})

    @app.route("/api/email-sources", methods=["POST"])
    @app.route("/api/custom-email-sources", methods=["POST"])
    def add_email_source():
        """Add a new custom email source."""
        data = request.json
        name = data.get("name", "").strip()
        sender_email = data.get("sender_email", "").strip()
        sender_pattern = data.get("sender_pattern", "").strip()
        subject_keywords = data.get("subject_keywords", "").strip()
        category = data.get("category", "custom").strip()

        if not name:
            return jsonify({"error": "Source name is required"}), 400

        if not sender_email and not sender_pattern:
            return jsonify({"error": "Either sender email or pattern is required"}), 400

        conn = get_db()
        now = datetime.now().isoformat()
        cursor = conn.execute(
            """INSERT INTO custom_email_sources
               (name, sender_email, sender_pattern, subject_keywords, category,
                is_builtin, enabled, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 0, 1, ?, ?)""",
            (name, sender_email, sender_pattern, subject_keywords, category, now, now),
        )
        source_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"success": True, "id": source_id})

    @app.route("/api/email-sources/<int:source_id>", methods=["PATCH"])
    @app.route("/api/custom-email-sources/<int:source_id>", methods=["PATCH"])
    def update_email_source(source_id):
        """Update an email source. Built-in sources can only toggle enabled."""
        data = request.json
        conn = get_db()

        # Check if it's a built-in source
        source = conn.execute(
            "SELECT is_builtin FROM custom_email_sources WHERE id = ?", (source_id,)
        ).fetchone()

        if not source:
            conn.close()
            return jsonify({"error": "Source not found"}), 404

        now = datetime.now().isoformat()

        # Validate post_scan_action if provided (allowed for both built-in and custom)
        post_scan_action = data.get("post_scan_action")
        if post_scan_action is not None and post_scan_action not in ("none", "archive", "delete"):
            conn.close()
            return (
                jsonify({"error": "Invalid post_scan_action. Must be: none, archive, delete"}),
                400,
            )

        if source["is_builtin"]:
            # Built-in sources can toggle enabled and post_scan_action
            enabled = data.get("enabled", 1)
            if post_scan_action is not None:
                conn.execute(
                    "UPDATE custom_email_sources SET enabled = ?, post_scan_action = ?, updated_at = ? WHERE id = ?",
                    (enabled, post_scan_action, now, source_id),
                )
            else:
                conn.execute(
                    "UPDATE custom_email_sources SET enabled = ?, updated_at = ? WHERE id = ?",
                    (enabled, now, source_id),
                )
        else:
            # Custom sources can be fully updated
            name = data.get("name", "").strip()
            sender_email = data.get("sender_email", "").strip()
            sender_pattern = data.get("sender_pattern", "").strip()
            subject_keywords = data.get("subject_keywords", "").strip()
            enabled = data.get("enabled", 1)
            category = data.get("category", "custom").strip()

            if not name:
                conn.close()
                return jsonify({"error": "Source name is required"}), 400

            conn.execute(
                """UPDATE custom_email_sources
                   SET name = ?, sender_email = ?, sender_pattern = ?,
                       subject_keywords = ?, enabled = ?, category = ?,
                       post_scan_action = ?, updated_at = ?
                   WHERE id = ?""",
                (
                    name,
                    sender_email,
                    sender_pattern,
                    subject_keywords,
                    enabled,
                    category,
                    post_scan_action or "none",
                    now,
                    source_id,
                ),
            )

        conn.commit()
        conn.close()
        return jsonify({"success": True})

    @app.route("/api/email-sources/<int:source_id>", methods=["DELETE"])
    @app.route("/api/custom-email-sources/<int:source_id>", methods=["DELETE"])
    def delete_email_source(source_id):
        """Delete a custom email source. Built-in sources cannot be deleted."""
        conn = get_db()

        # Check if it's a built-in source
        source = conn.execute(
            "SELECT is_builtin, name FROM custom_email_sources WHERE id = ?", (source_id,)
        ).fetchone()

        if not source:
            conn.close()
            return jsonify({"error": "Source not found"}), 404

        if source["is_builtin"]:
            conn.close()
            return (
                jsonify(
                    {
                        "error": f"Cannot delete built-in source '{source['name']}'. You can disable it instead."
                    }
                ),
                400,
            )

        conn.execute("DELETE FROM custom_email_sources WHERE id = ?", (source_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})

    # =========================================================================
    # SETTINGS ENDPOINTS
    # =========================================================================

    @app.route("/api/settings", methods=["GET"])
    def get_settings():
        """
        Get current application settings and AI provider info.

        Route: GET /api/settings

        Returns:
            JSON with:
            - ai_provider: Current AI provider name
            - ai_model: Current AI model name
            - available_providers: List of providers with installed packages
            - email_sources_count: Number of enabled email sources
            - jobs_count: Total jobs in database
            - followups_count: Total followups in database
        """
        from app.ai.factory import get_provider, get_available_providers, get_provider_info

        # Get current AI provider info
        try:
            provider = get_provider()
            provider_name = provider.provider_name
            model_name = provider.model_name
        except Exception as e:
            provider_name = "unknown"
            model_name = str(e)

        # Get available providers
        available = get_available_providers()

        # Get counts from database
        conn = get_db()
        email_sources_count = conn.execute(
            "SELECT COUNT(*) FROM custom_email_sources WHERE enabled = 1"
        ).fetchone()[0]
        jobs_count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        followups_count = conn.execute("SELECT COUNT(*) FROM followups").fetchone()[0]
        conn.close()

        return jsonify(
            {
                "ai_provider": provider_name,
                "ai_model": model_name,
                "available_providers": available,
                "email_sources_count": email_sources_count,
                "jobs_count": jobs_count,
                "followups_count": followups_count,
            }
        )

    @app.route("/api/settings/test-provider", methods=["POST"])
    def test_ai_provider():
        """
        Test AI provider connection with a simple query.

        Route: POST /api/settings/test-provider

        Returns:
            JSON with:
            - success: Boolean indicating if test passed
            - provider: Provider name
            - model: Model name
            - response: Test response from AI
            - error: Error message if failed
        """
        from app.ai.factory import get_provider

        try:
            provider = get_provider()

            # Simple test: ask AI to respond with JSON
            test_result = provider.filter_and_score(
                {
                    "title": "Test Job",
                    "company": "Test Company",
                    "location": "Remote",
                    "raw_text": "This is a test job posting.",
                },
                "Test resume with Python and JavaScript skills.",
            )

            return jsonify(
                {
                    "success": True,
                    "provider": provider.provider_name,
                    "model": provider.model_name,
                    "response": test_result,
                }
            )
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/email-sources/test-pattern", methods=["POST"])
    def test_email_pattern():
        """
        Test an email source pattern against recent emails.

        Request Body:
            sender_pattern (str): Pattern to match (e.g., "@linkedin.com")
            sender_email (str): Exact email to match
            subject_keywords (str): Comma-separated keywords
            days_back (int): How many days to look back (default: 7)

        Returns:
            JSON with:
            - matches: Number of matching emails found
            - sample_subjects: Sample matching email subjects
            - sample_senders: Sample matching senders
        """
        try:
            data = request.get_json() or {}
            sender_pattern = data.get("sender_pattern", "").strip().lower()
            sender_email = data.get("sender_email", "").strip().lower()
            subject_keywords = data.get("subject_keywords", "").strip().lower()
            days_back = int(data.get("days_back", 7))

            if not sender_pattern and not sender_email:
                return jsonify({"error": "Either sender_pattern or sender_email is required"}), 400

            # Import email scanner
            from gmail_scanner import get_gmail_service, get_email_details, get_email_body
            from datetime import datetime, timedelta

            service = get_gmail_service()
            if not service:
                return jsonify({"error": "Gmail service not configured"}), 400

            # Build search query
            after_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
            query_parts = [f"after:{after_date}"]

            if sender_email:
                query_parts.append(f"from:{sender_email}")
            elif sender_pattern:
                # For patterns like "@linkedin.com", search for emails from that domain
                if sender_pattern.startswith("@"):
                    query_parts.append(f"from:*{sender_pattern}")
                else:
                    query_parts.append(f"from:{sender_pattern}")

            query = " ".join(query_parts)
            logger.info(f"Testing pattern with query: {query}")

            # Search for emails
            results = service.users().messages().list(userId="me", q=query, maxResults=50).execute()

            messages = results.get("messages", [])
            matching_emails = []
            sample_subjects = []
            sample_senders = []

            # Process keywords if provided
            keywords = (
                [k.strip() for k in subject_keywords.split(",") if k.strip()]
                if subject_keywords
                else []
            )

            for msg_info in messages[:20]:  # Check up to 20 messages
                try:
                    msg = (
                        service.users()
                        .messages()
                        .get(
                            userId="me",
                            id=msg_info["id"],
                            format="metadata",
                            metadataHeaders=["Subject", "From"],
                        )
                        .execute()
                    )

                    headers = {
                        h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])
                    }
                    subject = headers.get("Subject", "")
                    sender = headers.get("From", "")

                    # If keywords provided, check if any match
                    if keywords:
                        subject_lower = subject.lower()
                        if not any(kw in subject_lower for kw in keywords):
                            continue

                    matching_emails.append({"subject": subject, "sender": sender})

                    if subject and subject not in sample_subjects:
                        sample_subjects.append(subject[:100])
                    if sender and sender not in sample_senders:
                        sample_senders.append(sender)

                except Exception as e:
                    logger.warning(f"Error processing test message: {e}")
                    continue

            return jsonify(
                {
                    "matches": len(matching_emails),
                    "total_found": len(messages),
                    "sample_subjects": sample_subjects[:5],
                    "sample_senders": list(set(sample_senders))[:5],
                    "query_used": query,
                }
            )

        except Exception as e:
            logger.error(f"Error testing email pattern: {e}")
            return jsonify({"error": str(e)}), 500

    # ============== External Applications ==============
    @app.route("/api/external-applications", methods=["GET"])
    def get_external_applications():
        """
        Get all external applications with optional filtering.
        Query params: status, company, source
        """
        logger.debug(
            f"[Backend] GET /api/external-applications - Query params: {dict(request.args)}"
        )
        conn = get_db()

        # Build query with optional filters
        query = "SELECT * FROM external_applications WHERE 1=1"
        params = []

        if request.args.get("status"):
            query += " AND status = ?"
            params.append(request.args.get("status"))

        if request.args.get("company"):
            query += " AND company LIKE ?"
            params.append(f"%{request.args.get('company')}%")

        if request.args.get("source"):
            query += " AND source = ?"
            params.append(request.args.get("source"))

        query += " ORDER BY applied_date DESC"

        applications = [dict(row) for row in conn.execute(query, params).fetchall()]
        conn.close()

        logger.debug(f"[Backend] Returning {len(applications)} external applications")
        return jsonify({"applications": applications})

    @app.route("/api/external-applications", methods=["POST"])
    def create_external_application():
        """
        Create a new external application.
        Required fields: title, company, applied_date, source

        This endpoint now creates BOTH:
        1. An entry in the external_applications table (for tracking application details)
        2. An entry in the jobs table (so it appears in the main job list with status='applied')
        """
        data = request.json
        logger.debug(f"[Backend] POST /api/external-applications - Received data: {data}")

        # Validate required fields
        required_fields = ["title", "company", "applied_date", "source"]
        for field in required_fields:
            if not data.get(field):
                logger.warning(f"[Backend] Validation failed: {field} is missing")
                return jsonify({"error": f"{field} is required"}), 400

        # Generate unique IDs
        app_id = str(uuid.uuid4())[:16]
        job_id = str(uuid.uuid4())[:16]  # Create a new job_id for the job entry
        logger.debug(f"[Backend] Generated app_id: {app_id}, job_id: {job_id}")

        # Get optional fields
        location = data.get("location", "")
        url = data.get("url", "")
        application_method = data.get("application_method", "")
        contact_name = data.get("contact_name", "")
        contact_email = data.get("contact_email", "")
        status = data.get("status", "applied")
        follow_up_date = data.get("follow_up_date")
        notes = data.get("notes", "")

        now = datetime.now().isoformat()

        try:
            conn = get_db()

            # First, create a job entry in the jobs table
            # This makes the external application show up in the main job list
            conn.execute(
                """
                INSERT INTO jobs (
                    job_id, title, company, location, url, source,
                    status, score, baseline_score, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    job_id,
                    data["title"],
                    data["company"],
                    location,
                    url,
                    f"external_{data['source']}",  # Prefix source to identify it came from external tracking
                    "applied",  # Set status to 'applied' since this is an external application
                    0,  # Default score
                    0,  # Default baseline score
                    now,
                    now,
                ),
            )
            logger.debug(f"[Backend] Created job entry with job_id: {job_id}")

            # Then, create the external application entry linked to the job
            conn.execute(
                """
                INSERT INTO external_applications (
                    app_id, job_id, title, company, location, url, source,
                    application_method, applied_date, contact_name, contact_email,
                    status, follow_up_date, notes, created_at, updated_at, is_linked_to_job
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    app_id,
                    job_id,
                    data["title"],
                    data["company"],
                    location,
                    url,
                    data["source"],
                    application_method,
                    data["applied_date"],
                    contact_name,
                    contact_email,
                    status,
                    follow_up_date,
                    notes,
                    now,
                    now,
                    1,  # is_linked_to_job = 1
                ),
            )
            logger.debug(f"[Backend] Created external application entry linked to job_id: {job_id}")

            conn.commit()
            conn.close()
            logger.info(
                f"[Backend] Successfully inserted external application and job: {data['title']} at {data['company']}"
            )
        except Exception as e:
            logger.error(f"❌ [Backend] Database error: {str(e)}")
            return jsonify({"error": f"Database error: {str(e)}"}), 500

        return jsonify({"success": True, "app_id": app_id, "job_id": job_id})

    @app.route("/api/external-applications/<app_id>", methods=["GET"])
    def get_external_application(app_id):
        """Get details of a specific external application."""
        conn = get_db()
        app = conn.execute(
            "SELECT * FROM external_applications WHERE app_id = ?", (app_id,)
        ).fetchone()
        conn.close()

        if not app:
            return jsonify({"error": "Application not found"}), 404

        return jsonify({"application": dict(app)})

    @app.route("/api/external-applications/<app_id>", methods=["PATCH"])
    def update_external_application(app_id):
        """Update an external application and sync status to linked job."""
        data = request.json
        conn = get_db()

        # Build update query dynamically
        allowed_fields = [
            "title",
            "company",
            "location",
            "url",
            "source",
            "application_method",
            "applied_date",
            "contact_name",
            "contact_email",
            "status",
            "follow_up_date",
            "notes",
            "job_id",
            "is_linked_to_job",
        ]
        updates = []
        params = []

        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = ?")
                params.append(data[field])

        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(app_id)

            query = f"UPDATE external_applications SET {', '.join(updates)} WHERE app_id = ?"
            conn.execute(query, params)

            # If status is being updated, also update the linked job's status
            if "status" in data:
                # Get the job_id for this external application
                app = conn.execute(
                    "SELECT job_id FROM external_applications WHERE app_id = ?", (app_id,)
                ).fetchone()

                if app and app["job_id"]:
                    conn.execute(
                        "UPDATE jobs SET status = ?, updated_at = ? WHERE job_id = ?",
                        (data["status"], datetime.now().isoformat(), app["job_id"]),
                    )
                    logger.debug(
                        f"[Backend] Synced status '{data['status']}' to linked job: {app['job_id']}"
                    )

            conn.commit()

        conn.close()
        return jsonify({"success": True})

    @app.route("/api/external-applications/<app_id>", methods=["DELETE"])
    def delete_external_application(app_id):
        """Delete an external application and its linked job."""
        conn = get_db()

        # First, get the job_id if it exists
        app = conn.execute(
            "SELECT job_id FROM external_applications WHERE app_id = ?", (app_id,)
        ).fetchone()

        # Delete the external application
        conn.execute("DELETE FROM external_applications WHERE app_id = ?", (app_id,))

        # If there's a linked job, delete it too
        if app and app["job_id"]:
            conn.execute("DELETE FROM jobs WHERE job_id = ?", (app["job_id"],))
            logger.debug(f"[Backend] Deleted linked job: {app['job_id']}")

        conn.commit()
        conn.close()
        return jsonify({"success": True})

    # ============== Resume Management ==============
    @app.route("/api/resumes", methods=["GET"])
    def get_resumes():
        """Get all resume variants."""
        logger.debug("[Backend] GET /api/resumes")
        resumes = load_resumes_from_db()
        logger.debug(f"[Backend] Returning {len(resumes)} resumes")
        return jsonify({"resumes": resumes})

    @app.route("/api/resumes/<resume_id>", methods=["GET"])
    def get_resume(resume_id):
        """Get a specific resume by ID."""
        logger.debug(f"[Backend] GET /api/resumes/{resume_id}")
        conn = get_db()
        resume = conn.execute(
            "SELECT * FROM resume_variants WHERE resume_id = ?", (resume_id,)
        ).fetchone()
        conn.close()

        if not resume:
            return jsonify({"error": "Resume not found"}), 404

        return jsonify({"resume": dict(resume)})

    @app.route("/api/resumes", methods=["POST"])
    def create_resume():
        """
        Create a new resume variant.
        Accepts either file upload or direct content.
        """
        logger.debug("[Backend] POST /api/resumes")
        data = request.json

        # Validate required fields
        if not data.get("name"):
            return jsonify({"error": "name is required"}), 400

        if not data.get("content"):
            return jsonify({"error": "content is required"}), 400

        # Generate ID and hash
        resume_id = str(uuid.uuid4())[:16]
        content = data["content"]
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        now = datetime.now().isoformat()

        # Get optional fields
        focus_areas = data.get("focus_areas", "")
        target_roles = data.get("target_roles", "")
        file_path = data.get("file_path", "")

        try:
            conn = get_db()

            # Check for duplicate content
            existing = conn.execute(
                "SELECT resume_id, name FROM resume_variants WHERE content_hash = ?",
                (content_hash,),
            ).fetchone()

            if existing:
                conn.close()
                return (
                    jsonify(
                        {
                            "error": f'This resume already exists as "{existing["name"]}"',
                            "existing_id": existing["resume_id"],
                        }
                    ),
                    409,
                )

            # Insert new resume
            conn.execute(
                """
                INSERT INTO resume_variants (
                    resume_id, name, focus_areas, target_roles, file_path,
                    content, content_hash, created_at, updated_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
                (
                    resume_id,
                    data["name"],
                    focus_areas,
                    target_roles,
                    file_path,
                    content,
                    content_hash,
                    now,
                    now,
                ),
            )

            conn.commit()
            conn.close()

            logger.info(f"[Backend] Created resume: {data['name']}")
            return jsonify({"success": True, "resume_id": resume_id})

        except Exception as e:
            logger.error(f"❌ [Backend] Error creating resume: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/resumes/upload", methods=["POST"])
    def upload_resume():
        """
        Upload a resume file (PDF, TXT, or MD) and extract text.
        """
        logger.debug("[Backend] POST /api/resumes/upload")

        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Validate file extension
        allowed_extensions = {".pdf", ".txt", ".md"}
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()

        if file_ext not in allowed_extensions:
            return jsonify({"error": f"Invalid file type. Only PDF, TXT, MD allowed"}), 400

        try:
            # Extract text based on file type
            if file_ext == ".pdf":
                # Try to extract PDF text
                try:
                    from pypdf import PdfReader

                    pdf_reader = PdfReader(file)
                    text_parts = []
                    for page in pdf_reader.pages:
                        text_parts.append(page.extract_text())
                    resume_text = "\n\n".join(text_parts)

                    if not resume_text.strip():
                        return (
                            jsonify(
                                {
                                    "error": "Could not extract text from PDF. It may be scanned or image-based."
                                }
                            ),
                            400,
                        )

                except ImportError:
                    return (
                        jsonify(
                            {
                                "error": "PDF support not installed. Install with: pip install pypdf",
                                "hint": 'For now, please copy text from PDF and use "Paste Text" mode',
                            }
                        ),
                        400,
                    )
                except Exception as e:
                    return jsonify({"error": f"PDF extraction failed: {str(e)}"}), 400
            else:
                # Text or Markdown file
                resume_text = file.read().decode("utf-8")

            # Get metadata from form
            name = request.form.get("name", filename.rsplit(".", 1)[0])
            focus_areas = request.form.get("focus_areas", "")
            target_roles = request.form.get("target_roles", "")

            # Generate ID and hash
            resume_id = str(uuid.uuid4())[:16]
            content_hash = hashlib.sha256(resume_text.encode()).hexdigest()
            now = datetime.now().isoformat()

            conn = get_db()

            # Check for duplicate content
            existing = conn.execute(
                "SELECT resume_id, name FROM resume_variants WHERE content_hash = ?",
                (content_hash,),
            ).fetchone()

            if existing:
                conn.close()
                return (
                    jsonify(
                        {
                            "error": f'This resume already exists as "{existing["name"]}"',
                            "existing_id": existing["resume_id"],
                        }
                    ),
                    409,
                )

            # Insert new resume
            conn.execute(
                """
                INSERT INTO resume_variants (
                    resume_id, name, focus_areas, target_roles, file_path,
                    content, content_hash, created_at, updated_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
                (
                    resume_id,
                    name,
                    focus_areas,
                    target_roles,
                    filename,
                    resume_text,
                    content_hash,
                    now,
                    now,
                ),
            )

            conn.commit()
            conn.close()

            logger.info(f"[Backend] Uploaded resume: {name} ({len(resume_text)} chars)")
            return jsonify(
                {
                    "success": True,
                    "resume_id": resume_id,
                    "name": name,
                    "text_length": len(resume_text),
                    "pages_extracted": resume_text.count("\n\n") + 1 if file_ext == ".pdf" else 1,
                }
            )

        except Exception as e:
            logger.error(f"❌ [Backend] Error uploading resume: {e}")
            import traceback

            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route("/api/resumes/<resume_id>", methods=["PATCH"])
    def update_resume(resume_id):
        """Update resume metadata (not content - that requires new variant)."""
        logger.debug(f"[Backend] PATCH /api/resumes/{resume_id}")
        data = request.json
        conn = get_db()

        # Build update query for metadata only
        allowed_fields = ["name", "focus_areas", "target_roles", "is_active"]
        updates = []
        params = []

        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = ?")
                params.append(data[field])

        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(resume_id)

            query = f"UPDATE resume_variants SET {', '.join(updates)} WHERE resume_id = ?"
            conn.execute(query, params)
            conn.commit()

        conn.close()
        logger.info(f"[Backend] Updated resume: {resume_id}")
        return jsonify({"success": True})

    @app.route("/api/resumes/<resume_id>", methods=["DELETE"])
    def delete_resume(resume_id):
        """Soft delete a resume (sets is_active = 0)."""
        logger.debug(f"[Backend] DELETE /api/resumes/{resume_id}")
        conn = get_db()

        conn.execute(
            "UPDATE resume_variants SET is_active = 0, updated_at = ? WHERE resume_id = ?",
            (datetime.now().isoformat(), resume_id),
        )

        conn.commit()
        conn.close()

        logger.info(f"[Backend] Deactivated resume: {resume_id}")
        return jsonify({"success": True})

    # ============== Resume Recommendations ==============
    @app.route("/api/jobs/<job_id>/recommend-resume", methods=["POST"])
    def get_resume_recommendation(job_id):
        """Get AI resume recommendation for a specific job."""
        logger.debug(f"[Backend] POST /api/jobs/{job_id}/recommend-resume")

        conn = get_db()
        job = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()

        if not job:
            conn.close()
            return jsonify({"error": "Job not found"}), 404

        job_dict = dict(job)

        # Check if recommendation already exists
        if job_dict.get("resume_recommendation"):
            try:
                cached_rec = json.loads(job_dict["resume_recommendation"])
                conn.close()
                logger.debug(f"[Backend] Returning cached recommendation for {job_id}")
                return jsonify({"recommendation": cached_rec, "cached": True})
            except:
                pass  # If parsing fails, generate new recommendation

        # Generate new recommendation
        try:
            recommendation = recommend_resume_for_job(
                job_dict.get("raw_text", ""), job_dict.get("title", ""), job_dict.get("company", "")
            )

            # Store recommendation in database
            now = datetime.now().isoformat()
            conn.execute(
                """
                UPDATE jobs
                SET recommended_resume_id = ?,
                    resume_recommendation = ?,
                    resume_match_score = ?,
                    updated_at = ?
                WHERE job_id = ?
            """,
                (
                    recommendation["resume_id"],
                    json.dumps(recommendation),
                    recommendation["confidence"],
                    now,
                    job_id,
                ),
            )

            # Log the recommendation
            log_id = str(uuid.uuid4())[:16]
            conn.execute(
                """
                INSERT INTO resume_usage_log (
                    log_id, resume_id, job_id, recommended_at,
                    confidence_score, reasoning
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    log_id,
                    recommendation["resume_id"],
                    job_id,
                    now,
                    recommendation["confidence"],
                    recommendation["reasoning"],
                ),
            )

            # Update resume usage count
            conn.execute(
                """
                UPDATE resume_variants
                SET usage_count = usage_count + 1
                WHERE resume_id = ?
            """,
                (recommendation["resume_id"],),
            )

            conn.commit()
            conn.close()

            logger.info(
                f"[Backend] Generated resume recommendation for {job_id}: {recommendation['resume_name']}"
            )
            return jsonify({"recommendation": recommendation, "cached": False})

        except Exception as e:
            conn.close()
            logger.error(f"❌ [Backend] Error generating recommendation: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/jobs/recommend-resumes-batch", methods=["POST"])
    def batch_recommend_resumes():
        """
        Generate resume recommendations for multiple jobs in batch.
        Processes up to 100 jobs with rate limiting.
        """
        logger.debug("[Backend] POST /api/jobs/recommend-resumes-batch")
        data = request.json
        job_ids = data.get("job_ids", [])

        if not job_ids:
            return jsonify({"error": "job_ids required"}), 400

        if len(job_ids) > 100:
            return jsonify({"error": "Maximum 100 jobs per batch"}), 400

        conn = get_db()
        results = []
        errors = []

        for idx, job_id in enumerate(job_ids):
            try:
                # Get job
                job = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()

                if not job:
                    errors.append({"job_id": job_id, "error": "Job not found"})
                    continue

                job_dict = dict(job)

                # Skip if already has recommendation
                if job_dict.get("resume_recommendation"):
                    results.append(
                        {
                            "job_id": job_id,
                            "status": "skipped",
                            "reason": "Already has recommendation",
                        }
                    )
                    continue

                # Generate recommendation
                recommendation = recommend_resume_for_job(
                    job_dict.get("raw_text", ""),
                    job_dict.get("title", ""),
                    job_dict.get("company", ""),
                )

                # Store in database
                now = datetime.now().isoformat()
                conn.execute(
                    """
                    UPDATE jobs
                    SET recommended_resume_id = ?,
                        resume_recommendation = ?,
                        resume_match_score = ?,
                        updated_at = ?
                    WHERE job_id = ?
                """,
                    (
                        recommendation["resume_id"],
                        json.dumps(recommendation),
                        recommendation["confidence"],
                        now,
                        job_id,
                    ),
                )

                # Log the recommendation
                log_id = str(uuid.uuid4())[:16]
                conn.execute(
                    """
                    INSERT INTO resume_usage_log (
                        log_id, resume_id, job_id, recommended_at,
                        confidence_score, reasoning
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        log_id,
                        recommendation["resume_id"],
                        job_id,
                        now,
                        recommendation["confidence"],
                        recommendation["reasoning"],
                    ),
                )

                # Update usage count
                conn.execute(
                    """
                    UPDATE resume_variants
                    SET usage_count = usage_count + 1
                    WHERE resume_id = ?
                """,
                    (recommendation["resume_id"],),
                )

                results.append(
                    {
                        "job_id": job_id,
                        "status": "success",
                        "resume_id": recommendation["resume_id"],
                        "resume_name": recommendation["resume_name"],
                        "confidence": recommendation["confidence"],
                    }
                )

                # Rate limiting: small delay between API calls
                if idx < len(job_ids) - 1:  # Don't delay after last one
                    import time

                    time.sleep(0.5)

            except Exception as e:
                errors.append({"job_id": job_id, "error": str(e)})
                logger.error(f"❌ [Backend] Error processing {job_id}: {e}")

        conn.commit()
        conn.close()

        success_count = len([r for r in results if r["status"] == "success"])
        logger.info(
            f"[Backend] Batch recommendation complete: {success_count}/{len(job_ids)} successful"
        )

        return jsonify(
            {
                "success": True,
                "results": results,
                "errors": errors,
                "summary": {
                    "total": len(job_ids),
                    "successful": success_count,
                    "skipped": len([r for r in results if r["status"] == "skipped"]),
                    "failed": len(errors),
                },
            }
        )

    # ===== ENRICHMENT ENDPOINTS =====

    @app.route("/api/jobs/<job_id>/enrich", methods=["POST"])
    def api_enrich_job(job_id):
        """
        Enrich a single job with additional data from web search.

        Route: POST /api/jobs/<job_id>/enrich

        Request Body (optional):
            force (bool): Force re-enrichment even if already enriched

        Returns:
            JSON with enrichment results including salary, description, etc.
        """
        try:
            from app.enrichment import enrich_job

            data = request.get_json() or {}
            force = data.get("force", False)

            result = enrich_job(job_id, force=force)

            if result.get("success"):
                return jsonify(result)
            else:
                return jsonify(result), 400

        except Exception as e:
            logger.error(f"Error enriching job {job_id}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/jobs/enrich-batch", methods=["POST"])
    def api_enrich_jobs_batch():
        """
        Enrich multiple jobs with additional data.

        Route: POST /api/jobs/enrich-batch

        Request Body:
            job_ids (list): List of job IDs to enrich
            max_jobs (int): Maximum number of jobs to process (default 10)

        Returns:
            JSON with batch enrichment results
        """
        try:
            from app.enrichment import enrich_jobs_batch

            data = request.get_json() or {}
            job_ids = data.get("job_ids", [])
            max_jobs = min(data.get("max_jobs", 10), 50)  # Cap at 50

            if not job_ids:
                return jsonify({"error": "No job_ids provided"}), 400

            result = enrich_jobs_batch(job_ids, max_jobs=max_jobs)
            return jsonify(result)

        except Exception as e:
            logger.error(f"Error in batch enrichment: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/jobs/auto-enrich", methods=["POST"])
    def api_auto_enrich():
        """
        Automatically enrich top-scoring unenriched jobs.

        Route: POST /api/jobs/auto-enrich

        Request Body (optional):
            count (int): Number of jobs to enrich (default 5, max 20)
            min_score (int): Minimum score threshold (default 50)

        Returns:
            JSON with batch enrichment results
        """
        try:
            from app.enrichment import auto_enrich_top_jobs

            data = request.get_json() or {}
            count = min(data.get("count", 5), 20)
            min_score = data.get("min_score", 50)

            result = auto_enrich_top_jobs(count=count, min_score=min_score)
            return jsonify(result)

        except Exception as e:
            logger.error(f"Error in auto enrichment: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/jobs/<job_id>/enrichment", methods=["GET"])
    def api_get_enrichment(job_id):
        """
        Get enrichment status and data for a job.

        Route: GET /api/jobs/<job_id>/enrichment

        Returns:
            JSON with enrichment data:
            - salary_estimate
            - salary_confidence
            - full_description (truncated)
            - last_enriched
            - enrichment_source
            - is_aggregator
            - logo_url
        """
        try:
            conn = get_db()
            job = conn.execute(
                """
                SELECT salary_estimate, salary_confidence, full_description,
                       last_enriched, enrichment_source, is_aggregator, logo_url
                FROM jobs WHERE job_id = ?
            """,
                (job_id,),
            ).fetchone()
            conn.close()

            if not job:
                return jsonify({"error": "Job not found"}), 404

            return jsonify(
                {
                    "job_id": job_id,
                    "salary_estimate": job["salary_estimate"],
                    "salary_confidence": job["salary_confidence"] or "none",
                    "full_description": (
                        (job["full_description"][:1000] + "...")
                        if job["full_description"] and len(job["full_description"]) > 1000
                        else job["full_description"]
                    ),
                    "last_enriched": job["last_enriched"],
                    "enrichment_source": job["enrichment_source"],
                    "is_aggregator": bool(job["is_aggregator"]),
                    "logo_url": job["logo_url"],
                    "is_enriched": job["last_enriched"] is not None,
                }
            )

        except Exception as e:
            logger.error(f"Error getting enrichment for {job_id}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/jobs/<job_id>/logo", methods=["POST"])
    def api_fetch_logo(job_id):
        """
        Fetch and update logo for a job.

        Route: POST /api/jobs/<job_id>/logo

        Returns:
            JSON with logo URL and update status
        """
        try:
            from app.enrichment import update_job_logo

            conn = get_db()
            job = conn.execute("SELECT company FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            conn.close()

            if not job:
                return jsonify({"error": "Job not found"}), 404

            result = update_job_logo(job_id, job["company"])
            return jsonify(result)

        except Exception as e:
            logger.error(f"Error fetching logo for {job_id}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/jobs/<job_id>/detect-aggregator", methods=["POST"])
    def api_detect_aggregator(job_id):
        """
        Detect if a job is from a staffing agency.

        Route: POST /api/jobs/<job_id>/detect-aggregator

        Returns:
            JSON with detection results
        """
        try:
            from app.enrichment import detect_and_flag_aggregator

            conn = get_db()
            job = conn.execute(
                "SELECT company, title, raw_text FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            conn.close()

            if not job:
                return jsonify({"error": "Job not found"}), 404

            result = detect_and_flag_aggregator(
                job_id=job_id,
                company=job["company"],
                title=job["title"],
                description=job["raw_text"] or "",
            )
            return jsonify(result)

        except Exception as e:
            logger.error(f"Error detecting aggregator for {job_id}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/research-jobs", methods=["POST"])
    def research_jobs():
        """
        Use Claude AI to research and recommend jobs based on user's resume and location preferences.
        Generates 5-10 job recommendations with company names, roles, and why they're a good fit.
        """
        logger.debug("[Backend] POST /api/research-jobs - Starting Claude job research")

        try:
            # Load resumes from database
            resumes = load_resumes_from_db()
            if not resumes:
                return jsonify({"error": "No resumes found in database"}), 400

            # Combine resume content
            resume_text = "\n\n---RESUME VARIANT---\n\n".join(
                [
                    f"{r['name']}\nFocus: {r.get('focus_areas', 'N/A')}\n\n{r['content']}"
                    for r in resumes
                ]
            )

            # Get location preferences from config
            primary_locations = [loc["name"] for loc in CONFIG.primary_locations]

            # Get experience level and preferences
            exp_level_dict = CONFIG.experience_level
            exp_level = exp_level_dict.get("current_level", "mid")
            min_years = exp_level_dict.get("min_years", 1)
            max_years = exp_level_dict.get("max_years", 5)

            # Create research prompt
            research_prompt = f"""You are a job search research assistant. Based on the candidate's resume and preferences, recommend 5-10 specific job opportunities they should pursue.

    CANDIDATE'S RESUME:
    {resume_text[:10000]}

    LOCATION PREFERENCES:
    Primary locations: {', '.join(primary_locations)}

    EXPERIENCE LEVEL:
    Current level: {exp_level}
    Years of experience: {min_years}-{max_years}

    TASK:
    Research and recommend 5-10 specific job opportunities that:
    1. Match the candidate's skills and experience level
    2. Are in their preferred locations (especially remote opportunities)
    3. Are realistic and currently in-demand roles
    4. Align with their career trajectory

    For each job recommendation, provide:
    - Company name (real companies that commonly hire for these roles)
    - Job title
    - Career page URL (if you know the company's career/jobs page URL, otherwise leave blank)
    - Why it's a good fit (2-3 specific reasons based on their resume)
    - Key skills from their resume that match
    - Estimated match score (0-100)

    Return ONLY a valid JSON array with this structure:
    [
      {{
        "company": "Company Name",
        "title": "Job Title",
        "location": "Location",
        "career_page_url": "https://company.com/careers or blank if unknown",
        "why_good_fit": "Specific reasons why this role matches their background...",
        "matching_skills": ["skill1", "skill2", "skill3"],
        "match_score": 85,
        "job_type": "Full-time"
      }}
    ]

    Focus on real, reputable companies and current in-demand roles. Be specific and actionable."""

            # Call Claude API
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            response = client.messages.create(
                model=CONFIG.ai_model or "claude-sonnet-4-20250514",
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": research_prompt}],
            )

            # Parse response
            response_text = response.content[0].text.strip()

            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            recommendations = json.loads(response_text)

            logger.info(f"[Backend] Claude generated {len(recommendations)} job recommendations")

            # Save recommendations to database as "researched" jobs
            conn = get_db()
            saved_jobs = []
            now = datetime.now().isoformat()

            for rec in recommendations[:10]:  # Limit to 10
                # Generate job ID
                job_id = hashlib.sha256(
                    f"{rec['company']}:{rec['title']}:claude_research".encode()
                ).hexdigest()[:16]

                # Check if already exists
                existing = conn.execute(
                    "SELECT job_id FROM jobs WHERE job_id = ?", (job_id,)
                ).fetchone()

                if existing:
                    logger.debug(
                        f"[Backend] Skipping duplicate: {rec['title']} at {rec['company']}"
                    )
                    continue

                # Create analysis JSON
                analysis = {
                    "qualification_score": rec.get("match_score", 80),
                    "should_apply": True,
                    "strengths": rec.get("matching_skills", []),
                    "gaps": [],
                    "recommendation": rec.get("why_good_fit", ""),
                    "resume_to_use": resumes[0]["name"] if resumes else "default",
                }

                # Generate job URL - prefer career page, fallback to Google Jobs search
                career_url = rec.get("career_page_url", "").strip()
                if career_url and career_url.startswith("http"):
                    job_url = career_url
                else:
                    # Create Google Jobs search URL (better than regular Google search)
                    search_query = f"{rec['title']} {rec['company']}".replace(" ", "+")
                    job_url = f"https://www.google.com/search?q={search_query}&ibp=htl;jobs"

                # Insert into database
                conn.execute(
                    """
                    INSERT INTO jobs (
                        job_id, title, company, location, url, source,
                        status, score, baseline_score, analysis, raw_text,
                        created_at, updated_at, is_filtered
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        job_id,
                        rec["title"],
                        rec["company"],
                        rec.get(
                            "location", primary_locations[0] if primary_locations else "Remote"
                        ),
                        job_url,
                        "claude_research",
                        "new",
                        rec.get("match_score", 80),
                        rec.get("match_score", 80),
                        json.dumps(analysis),
                        rec.get("why_good_fit", ""),
                        now,
                        now,
                        0,
                    ),
                )

                saved_jobs.append(
                    {
                        "job_id": job_id,
                        "title": rec["title"],
                        "company": rec["company"],
                        "score": rec.get("match_score", 80),
                    }
                )

            conn.commit()
            conn.close()

            logger.info(f"[Backend] Saved {len(saved_jobs)} new research jobs to database")

            return jsonify(
                {
                    "success": True,
                    "jobs_found": len(recommendations),
                    "jobs_saved": len(saved_jobs),
                    "saved_jobs": saved_jobs,
                }
            )

        except Exception as e:
            logger.error(f"❌ [Backend] Error in job research: {str(e)}")
            import traceback

            traceback.print_exc()
            return jsonify({"error": f"Research failed: {str(e)}"}), 500

    @app.route("/api/research-jobs/<resume_id>", methods=["POST"])
    def research_jobs_for_resume(resume_id):
        """
        Research jobs tailored specifically to a single resume.
        Uses Claude AI to find 5-10 jobs that match this resume's focus areas and target roles.
        """
        logger.debug(f"[Backend] POST /api/research-jobs/{resume_id}")

        try:
            conn = get_db()

            # Get the resume
            resume = conn.execute(
                "SELECT * FROM resume_variants WHERE resume_id = ? AND is_active = 1", (resume_id,)
            ).fetchone()

            if not resume:
                return jsonify({"error": "Resume not found"}), 404

            resume_name = resume["name"]
            resume_content = resume["content"]
            focus_areas = resume["focus_areas"] or "Not specified"
            target_roles = resume["target_roles"] or "Not specified"

            logger.info(f"[Backend] Researching jobs for resume: {resume_name}")
            logger.info(f"  Focus areas: {focus_areas}")
            logger.info(f"  Target roles: {target_roles}")

            # Build research prompt tailored to this specific resume
            research_prompt = f"""You are a job search assistant. Research and recommend specific job opportunities for a candidate based on their resume.

    CANDIDATE'S RESUME:
    {resume_content[:3000]}

    FOCUS AREAS: {focus_areas}
    TARGET ROLES: {target_roles}

    LOCATION PREFERENCES:
    Primary locations: {', '.join([loc.get('name', '') for loc in CONFIG.preferences.get('locations', {}).get('primary', [])])}

    TASK:
    Research and recommend 5-10 specific job opportunities that:
    1. Match this resume's specific skills and experience
    2. Align with the focus areas: {focus_areas}
    3. Match target roles: {target_roles}
    4. Are in preferred locations (especially remote opportunities)
    5. Are realistic and currently in-demand roles

    For each job recommendation, provide:
    - Company name (real companies that commonly hire for these roles)
    - Job title
    - Career page URL (if you know the company's career/jobs page URL, otherwise leave blank)
    - Why it's a perfect fit for THIS specific resume (2-3 reasons citing actual resume content)
    - Key skills from this resume that match
    - Estimated match score (0-100)

    Return ONLY a valid JSON array with this structure:
    [
      {{
        "company": "Company Name",
        "title": "Job Title",
        "location": "Location",
        "career_page_url": "https://company.com/careers or blank if unknown",
        "why_good_fit": "Specific reasons why this role matches THIS resume...",
        "matching_skills": ["skill1", "skill2", "skill3"],
        "match_score": 85,
        "job_type": "Full-time"
      }}
    ]

    Focus on roles that specifically match the focus areas and target roles for THIS resume."""

            # Call Claude API
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            response = client.messages.create(
                model=CONFIG.ai_model or "claude-sonnet-4-20250514",
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": research_prompt}],
            )

            # Parse response
            response_text = response.content[0].text.strip()

            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            recommendations = json.loads(response_text)

            logger.info(
                f"[Backend] Claude generated {len(recommendations)} job recommendations for {resume_name}"
            )

            # Save recommendations to database
            saved_jobs = []
            now = datetime.now().isoformat()

            for rec in recommendations[:10]:  # Limit to 10
                # Generate job ID
                job_id = hashlib.sha256(
                    f"{rec['company']}:{rec['title']}:resume_{resume_id}".encode()
                ).hexdigest()[:16]

                # Check if already exists
                existing = conn.execute(
                    "SELECT job_id FROM jobs WHERE job_id = ?", (job_id,)
                ).fetchone()

                if existing:
                    logger.debug(
                        f"[Backend] Skipping duplicate: {rec['title']} at {rec['company']}"
                    )
                    continue

                # Create analysis JSON
                analysis = {
                    "qualification_score": rec.get("match_score", 80),
                    "should_apply": True,
                    "strengths": rec.get("matching_skills", []),
                    "gaps": [],
                    "recommendation": rec.get("why_good_fit", ""),
                    "resume_to_use": resume_name,
                }

                # Generate job URL - prefer career page, fallback to Google Jobs search
                career_url = rec.get("career_page_url", "").strip()
                if career_url and career_url.startswith("http"):
                    job_url = career_url
                else:
                    # Create Google Jobs search URL (better than regular Google search)
                    search_query = f"{rec['title']} {rec['company']}".replace(" ", "+")
                    job_url = f"https://www.google.com/search?q={search_query}&ibp=htl;jobs"

                # Insert into database
                conn.execute(
                    """
                    INSERT INTO jobs (
                        job_id, title, company, location, url, source,
                        status, score, baseline_score, analysis, raw_text,
                        created_at, updated_at, is_filtered
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                    (
                        job_id,
                        rec["title"],
                        rec["company"],
                        rec.get("location", "Remote"),
                        job_url,
                        f"claude_research_{resume_name}",
                        "new",
                        rec.get("match_score", 80),
                        rec.get("match_score", 80),
                        json.dumps(analysis),
                        json.dumps(rec),
                        now,
                        now,
                    ),
                )

                saved_jobs.append(
                    {
                        "title": rec["title"],
                        "company": rec["company"],
                        "score": rec.get("match_score", 80),
                    }
                )

            conn.commit()
            conn.close()

            return jsonify(
                {
                    "success": True,
                    "jobs_found": len(recommendations),
                    "jobs_saved": len(saved_jobs),
                    "resume_name": resume_name,
                    "saved_jobs": saved_jobs,
                }
            )

        except Exception as e:
            logger.error(f"❌ [Backend] Error in resume-specific job research: {str(e)}")
            import traceback

            traceback.print_exc()
            return jsonify({"error": f"Research failed: {str(e)}"}), 500

    # ============== Backup API Routes ==============

    @app.route("/api/backup/create", methods=["POST"])
    def api_create_backup():
        """Create a manual database backup."""
        try:
            backup_manager = BackupManager(DB_PATH, max_backups=10)
            backup_path = backup_manager.create_backup()

            if backup_path:
                return jsonify(
                    {
                        "success": True,
                        "message": "Backup created successfully",
                        "filename": backup_path.name,
                        "path": str(backup_path),
                    }
                )
            else:
                return jsonify({"success": False, "error": "Failed to create backup"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/backup/list", methods=["GET"])
    def api_list_backups():
        """List all available backups."""
        try:
            backup_manager = BackupManager(DB_PATH)
            backups = backup_manager.list_backups()
            stats = backup_manager.get_backup_stats()

            return jsonify({"backups": backups, "stats": stats})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/backup/restore/<filename>", methods=["POST"])
    def api_restore_backup(filename):
        """Restore database from a backup file."""
        try:
            backup_manager = BackupManager(DB_PATH)
            success = backup_manager.restore_backup(filename)

            if success:
                return jsonify({"success": True, "message": f"Database restored from {filename}"})
            else:
                return jsonify({"success": False, "error": "Restore failed"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/ai/providers")
    def api_ai_providers():
        """
        Get information about available AI providers.

        Route: GET /api/ai/providers

        Returns:
            JSON response with provider information including:
            - providers: Dict of provider info (name, env_var, has_key, models, etc.)
            - current_provider: Currently configured provider name
            - current_model: Currently configured model name
        """
        try:
            providers = get_provider_info()

            # Get current provider and model from config using Config class properties
            current_provider = CONFIG.ai_provider
            current_model = CONFIG.ai_model

            return jsonify(
                {
                    "providers": providers,
                    "current_provider": current_provider,
                    "current_model": current_model,
                }
            )
        except Exception as e:
            logger.error(f"Error getting AI providers: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/ai/test", methods=["POST"])
    def api_ai_test():
        """
        Test an AI provider connection.

        Route: POST /api/ai/test

        Request Body:
            provider (str): Provider to test ('claude', 'openai', 'gemini')

        Returns:
            JSON response with:
            - success: bool indicating if test passed
            - provider: Provider name
            - model: Model used for test
            - message: Result message or error
        """
        try:
            data = request.get_json() or {}
            provider_name = data.get("provider", "claude")

            # Import and test the provider
            from app.ai import get_provider

            test_config = {"ai": {"provider": provider_name}}

            provider = get_provider(test_config)

            # Simple test: just verify we can create the provider
            # The provider init already validates API key
            return jsonify(
                {
                    "success": True,
                    "provider": provider.provider_name,
                    "model": provider.model_name,
                    "message": f"{provider.provider_name} provider is configured correctly",
                }
            )
        except ValueError as e:
            # Missing API key or invalid provider
            return (
                jsonify(
                    {"success": False, "error": str(e), "message": "Provider configuration error"}
                ),
                400,
            )
        except ImportError as e:
            # Package not installed
            return (
                jsonify(
                    {"success": False, "error": str(e), "message": "Required package not installed"}
                ),
                400,
            )
        except Exception as e:
            logger.error(f"Error testing AI provider: {e}")
            return jsonify({"success": False, "error": str(e), "message": "Test failed"}), 500

    return app
