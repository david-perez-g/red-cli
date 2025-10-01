# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-09-30

### Added

- **Bulk issue creation from CSV**: Create multiple issues at once using CSV files
- **Estimated hours support**: Add estimated hours to issues during creation
- **CSV export functionality**: Export issues to CSV format with all fields
- **Improved CSV column names**: Changed from `project_id`, `tracker_id`, etc. to more user-friendly `project`, `tracker`, etc.
- **Progress indicators**: Added spinners and progress reporting for bulk operations
- **Comprehensive error handling**: Better error messages and validation for bulk operations
- **Project name resolution**: Support both project names and identifiers
- **Enhanced filtering**: Added status filtering, pagination, and project-specific listing
- **Time tracking**: New `hours` command to view logged time entries with date and project filtering
- **Weekly summary**: Time entries grouped by ISO week with date ranges and totals

### Changed

- **CSV format**: Updated column names for better usability (`project_id` → `project`, `tracker_id` → `tracker`, etc.)
- **Documentation**: Comprehensive README with examples for all features

### Fixed

- **CSV parsing**: Improved handling of quoted fields and special characters
- **Date validation**: Better handling of start/due dates in Redmine API

## [0.1.0] - 2025-09-XX

### Added

- Initial release with basic Redmine CLI functionality
- Authentication system with secure token storage
- Issue listing with basic filtering
- Single issue creation
- Project overview and reporting
- Basic error handling and user feedback
