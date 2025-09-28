# red

A clean, efficient CLI for Redmine issue management.

## Installation

```bash
pip install .
```

## Usage

### Authentication

```bash
# Interactive login (recommended - secure)
red login --server https://redmine.example.com

# Login with specific user
red login --server https://redmine.example.com --user username

# Force token authentication method
red login --server https://redmine.example.com --user username --method token

# Force password authentication method
red login --server https://redmine.example.com --user username --method password

# Show current session
red whoami

# Logout
red logout
```

### Issue Operations

```bash
# List issues (defaults to assigned to you, open status)
red issues

# List with filters
red issues --assignee me --status open
red issues --assignee 123 --status closed --tracker "Bug"
red issues --id 1,3,5..10

# Export to CSV
red issues --csv > issues.csv
red issues --assignee 123 --csv -o issues.csv

# Show specific issue
red show 1234

# Create single issue
red create --subject "Fix login bug" --description "..." --tracker Bug --assignee me

# Create multiple issues from CSV
red create --csv issues.csv

# Update issues
red update 1234 --status "In Progress" --done 50
red update --csv updates.csv

# Close/resolve issues
red close 1234 --note "Fixed in commit abc123"
red close 1,3,5..10
```

### Time Tracking

```bash
# Log time for single issue
red time 1234 --hours 2.5 --comment "Fixed authentication"

# Log time from CSV
red time --csv time_entries.csv

# Show spent time
red time --show --week
red time --show --range 2025-01-01..2025-01-31
red time --show --project "MyProject"
```

### Reports & Overview

```bash
# Personal overview
red overview

# Project overview
red overview --project "MyProject"

# Weekly time report
red report --time --week
red report --time --range 2025-01-01..2025-01-31
```

### Output Formats

```bash
# Default: human-readable table
red issues

# CSV output (for scripting/import)
red issues --csv
red issues --csv -o output.csv

# JSON output (for API integration)
red issues --json
```
