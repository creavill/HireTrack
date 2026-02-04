"""
Enrichment Package - Web search and job data enrichment

This module provides utilities for enriching job data with additional
information from web searches.
"""

from .web_search import (
    search_job_posting,
    WebSearchResult,
    extract_job_info_from_html,
)
from .pipeline import (
    enrich_job,
    enrich_job_data,
    enrich_jobs_batch,
    get_unenriched_jobs,
    auto_enrich_top_jobs,
    rescore_after_enrichment,
)
from .aggregator_detection import (
    detect_aggregator,
    flag_job_as_aggregator,
    detect_and_flag_aggregator,
    scan_jobs_for_aggregators,
)
from .logo_fetcher import (
    fetch_logo_url,
    update_job_logo,
    batch_update_logos,
    get_clearbit_logo_url,
    get_google_favicon_url,
)

__all__ = [
    # Web search
    'search_job_posting',
    'WebSearchResult',
    'extract_job_info_from_html',
    # Pipeline
    'enrich_job',
    'enrich_job_data',
    'enrich_jobs_batch',
    'get_unenriched_jobs',
    'auto_enrich_top_jobs',
    'rescore_after_enrichment',
    # Aggregator detection
    'detect_aggregator',
    'flag_job_as_aggregator',
    'detect_and_flag_aggregator',
    'scan_jobs_for_aggregators',
    # Logo fetcher
    'fetch_logo_url',
    'update_job_logo',
    'batch_update_logos',
    'get_clearbit_logo_url',
    'get_google_favicon_url',
]
