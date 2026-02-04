"""
Pre-Filters Package - Rule-based filtering before AI

This module provides pre-filtering utilities that can filter jobs based on
simple rules before (or instead of) using AI, reducing cost and latency.

- Location filter: Match job location against user preferences
- Salary filter: Match salary range against user expectations
"""

from .location_filter import (
    LocationFilterResult,
    filter_location,
    normalize_location,
    is_remote_location,
    parse_location_parts,
)
from .salary_filter import (
    SalaryFilterResult,
    filter_salary,
    parse_salary_string,
    normalize_salary_range,
)

__all__ = [
    # Location filter
    'LocationFilterResult',
    'filter_location',
    'normalize_location',
    'is_remote_location',
    'parse_location_parts',
    # Salary filter
    'SalaryFilterResult',
    'filter_salary',
    'parse_salary_string',
    'normalize_salary_range',
]
