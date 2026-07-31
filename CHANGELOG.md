# Changelog

## 未发布 / Next

Added:

- File download count statistics
- File cumulative download traffic statistics
- SQLite automatic migration for old data
- File list download statistics display

## v1.2.0

Added:

- File download traffic limit
- `download_limit_bytes` field
- Support setting per-file maximum download traffic
- Automatically forbid downloads after the limit is exceeded

## v1.0.0

Initial version archive.

## v1.0.1

Added:

- File share page
- Folder sharing

Fixed:

- Download button blank-page issue

## v1.0.2

Fixed:

- Mobile hidden share button issue

Added:

- Mobile file actions:
  - Download
  - Direct-link share
  - Share page
  - Delete

Changed files:

- `app.py`
