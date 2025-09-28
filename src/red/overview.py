# src/red/overview.py
"""Overview functionality for red CLI."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from .api import get_api_client
from .models import Issue, TimeEntry
from .auth import require_auth


def get_personal_overview(date_range: Optional[tuple] = None) -> Dict[str, Any]:
    """Get personal overview data for current user.
    
    Args:
        date_range: Optional tuple of (start_date, end_date) as date objects
    """
    api = get_api_client()
    session = require_auth()

    # Determine date range for time entries
    if date_range:
        start_date, end_date = date_range
        from_date = start_date.strftime('%Y-%m-%d') if start_date else None
        to_date = end_date.strftime('%Y-%m-%d') if end_date else None
    else:
        # Default to last 30 days
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        from_date = thirty_days_ago
        to_date = None

    # Get user's issues
    issues_data = api.get_issues(assigned_to_id='me')

    # Get time entries for the specified date range
    time_entries_data = api.get_time_entries(
        user_id=session.user_id,
        from_date=from_date,
        to_date=to_date
    )

    # Convert to models
    issues = [Issue.from_api_data(issue) for issue in issues_data]
    time_entries = [TimeEntry.from_api_data(entry) for entry in time_entries_data]

    # Calculate statistics
    stats = calculate_personal_stats(issues, time_entries, date_range)

    return {
        'issues': issues,
        'time_entries': time_entries,
        'stats': stats,
        'date_range': date_range
    }


def get_project_overview(project_identifier: str, date_range: Optional[tuple] = None) -> Dict[str, Any]:
    """Get project overview data.
    
    Args:
        project_identifier: Name or identifier of the project
        date_range: Optional tuple of (start_date, end_date) as date objects
    """
    api = get_api_client()

    # For now, we'll get all issues and filter by project
    # In a real implementation, we'd use project-specific API calls
    issues_data = api.get_issues()

    # Filter issues by project (this is a simplification)
    project_issues = [
        issue for issue in issues_data
        if issue.get('project', {}).get('name', '').lower() == project_identifier.lower() or
           issue.get('project', {}).get('identifier', '').lower() == project_identifier.lower()
    ]

    # For project time entries, we'd need project-specific filtering
    # For now, we'll skip detailed time tracking per project
    time_entries = []

    # Convert to models
    issues = [Issue.from_api_data(issue) for issue in project_issues]

    # Calculate statistics
    stats = calculate_project_stats(issues, time_entries, date_range)

    return {
        'project_name': project_identifier,
        'issues': issues,
        'time_entries': time_entries,
        'stats': stats,
        'date_range': date_range
    }


def calculate_personal_stats(issues: List[Issue], time_entries: List[TimeEntry], date_range: Optional[tuple] = None) -> Dict[str, Any]:
    """Calculate personal statistics."""
    # Issues by status
    status_counts = defaultdict(int)
    for issue in issues:
        status_counts[issue.status] += 1

    # Issues by tracker
    tracker_counts = defaultdict(int)
    for issue in issues:
        tracker_counts[issue.tracker] += 1

    # Issues by project
    project_counts = defaultdict(int)
    for issue in issues:
        project_counts[issue.project] += 1

    # Time tracking stats
    total_hours = sum(entry.hours for entry in time_entries)
    
    # Calculate this week hours based on date range or default
    if date_range and date_range[0]:
        # If start date is provided, calculate hours from that date
        start_date = datetime.combine(date_range[0], datetime.min.time())
        this_week_hours = sum(
            entry.hours for entry in time_entries
            if entry.spent_on >= start_date
        )
    else:
        # Default to last 7 days
        this_week_hours = sum(
            entry.hours for entry in time_entries
            if entry.spent_on >= datetime.now() - timedelta(days=7)
        )

    # Recent activity (last 7 days or from start date)
    if date_range and date_range[0]:
        start_date = datetime.combine(date_range[0], datetime.min.time())
        recent_issues = [
            issue for issue in issues
            if issue.updated_on >= start_date
        ]
    else:
        recent_issues = [
            issue for issue in issues
            if issue.updated_on >= datetime.now() - timedelta(days=7)
        ]

    return {
        'total_issues': len(issues),
        'status_counts': dict(status_counts),
        'tracker_counts': dict(tracker_counts),
        'project_counts': dict(project_counts),
        'total_hours': total_hours,
        'this_week_hours': this_week_hours,
        'recent_issues_count': len(recent_issues),
        'open_issues': status_counts.get('New', 0) + status_counts.get('Open', 0) + status_counts.get('Assigned', 0)
    }


def calculate_project_stats(issues: List[Issue], time_entries: List[TimeEntry], date_range: Optional[tuple] = None) -> Dict[str, Any]:
    """Calculate project statistics."""
    # Issues by status
    status_counts = defaultdict(int)
    for issue in issues:
        status_counts[issue.status] += 1

    # Issues by tracker
    tracker_counts = defaultdict(int)
    for issue in issues:
        tracker_counts[issue.tracker] += 1

    # Time tracking stats
    total_hours = sum(entry.hours for entry in time_entries)

    # Contributors
    contributors = set(entry.user for entry in time_entries)

    return {
        'total_issues': len(issues),
        'status_counts': dict(status_counts),
        'tracker_counts': dict(tracker_counts),
        'total_hours': total_hours,
        'contributors_count': len(contributors),
        'contributors': list(contributors)
    }