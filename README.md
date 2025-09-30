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

#### List Issues

```bash
# List your assigned issues (defaults to open status)
red issues

# List with pagination
red issues --show-first 50 --page 2

# Filter by status
red issues --status open      # Open issues only
red issues --status closed    # Closed issues only
red issues --status all       # All issues

# Filter by project
red issues --project "MyProject"

# Display options
red issues --oneline          # Compact single-line format
red issues --no-logged-hours  # Skip logged hours (faster)

# List specific issues by ID
red issues 123 456 789

# Combine filters
red issues --project "MyProject" --status open --show-first 20
```

#### CSV Export

```bash
# Export issues to CSV (stdout)
red issues --csv

# Export to file
red issues --csv -o issues.csv

# Export with filters
red issues --project "MyProject" --status all --csv -o project_issues.csv
```

**CSV Format Details:**
- Header row with `id` first, followed by all other fields alphabetically
- Nested objects are JSON-encoded, lists are semicolon-separated
- Example: `id,assigned_to,author,created_on,status,subject,tracker`

#### Create Issues

##### Single Issue Creation

```bash
# Create with required fields
red create -p "MyProject" -s "Fix login bug"

# Create with all options
red create \
  -p "MyProject" \
  -s "Implement user authentication" \
  -d "Add OAuth2 support for user login" \
  -T "Feature" \
  -S "To Do" \
  -a "john.doe" \
  --start-date "2025-10-01" \
  --due-date "2025-10-15"

# Create with minimal options (assignee defaults to you)
red create -p "MyProject" -s "Quick task"
```

**Available Options:**
- `-p, --project`: Project identifier or ID (required)
- `-s, --subject`: Issue subject (required, prompts if not provided)
- `-d, --description`: Detailed description
- `-T, --tracker`: Tracker name or ID (e.g., "Bug", "Feature")
- `-S, --status`: Status name or ID (e.g., "New", "In Progress")
- `-a, --assignee`: Assignee name, login, or ID (default: "me")
- `--start-date`: Start date (YYYY-MM-DD)
- `--due-date`: Due date (YYYY-MM-DD)

##### Bulk Creation from CSV

```bash
# Create multiple issues from CSV file
red create --csv --input issues.csv

# Create and export results to CSV
red create --csv --input issues.csv --output created_issues.csv
```

**CSV Format for Bulk Creation:**
Required columns: `project_id`, `subject`
Optional columns: `description`, `tracker_id`, `status_id`, `assigned_to_id`, `start_date`, `due_date`

**Example CSV:**
```csv
project_id,subject,description,tracker_id,status_id,assigned_to_id,start_date,due_date
myproject,Fix login bug,Authentication fails on mobile,Bug,To Do,john.doe,2025-10-01,2025-10-07
myproject,Add dark mode,Implement dark theme,Feature,New,,2025-10-08,2025-10-15
myproject,Update docs,Refresh API documentation,,,,,
```

### Reports & Overview

```bash
# Personal overview (assigned issues, recent activity)
red overview

# Project overview
red overview --project "MyProject"
```

## Configuration

The CLI stores authentication sessions securely in your user config directory. Sessions persist across terminal sessions until you explicitly logout.

## Examples

### Complete Workflow

```bash
# Authenticate
red login --server https://redmine.company.com

# Check your assigned issues
red issues

# Create a new feature request
red create -p "web-app" -s "Add export to PDF" -T "Feature" -S "New"

# Create multiple issues from CSV
red create --csv --input sprint_issues.csv --output created_sprint.csv

# Export all project issues for analysis
red issues --project "web-app" --status all --csv -o project_export.csv

# Get project overview
red overview --project "web-app"
```

### Bulk Issue Creation

Create `bulk_issues.csv`:
```csv
project_id,subject,description,tracker_id,status_id,assigned_to_id,start_date,due_date
web-app,Implement search,Add search functionality,Feature,To Do,developer1,2025-10-01,2025-10-10
web-app,Fix mobile layout,Responsive design issues,Bug,In Progress,developer2,2025-10-05,2025-10-12
web-app,Update dependencies,Security updates for libraries,Task,New,,2025-10-08,2025-10-09
```

Then create all issues:
```bash
red create --csv --input bulk_issues.csv --output created_issues.csv
```

## Error Handling

The CLI provides clear error messages for:
- Authentication failures
- Invalid project/tracker/status names
- Malformed CSV files
- Network connectivity issues
- Permission errors

Bulk operations continue processing even if individual items fail, with detailed error reporting at the end.
