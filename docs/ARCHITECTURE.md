# Architecture

R2 Drive Personal Edition is a small single-owner file drive.

## Request Flow

```text
User
  ↓
Caddy HTTPS
  ↓
Python application
  ↓
SQLite metadata
  ↓
Local filesystem storage
```

## Components

### Caddy

Caddy handles HTTPS and forwards requests to the Python application on `127.0.0.1:8090`.

### Python Application

The application is implemented in `app.py`. It provides:

- Authentication
- File and folder APIs
- Upload handling
- Download responses
- Public direct links
- File share pages
- Folder share pages

### SQLite

SQLite stores metadata, including:

- Users
- Sessions
- Folders
- Files
- Share state
- Share tokens
- File names, sizes, content types, and update timestamps

The production database is stored under:

```text
/opt/r2-drive/data/drive.sqlite3
```

Database files are runtime data and are not committed to Git.

### File Storage

Uploaded files are stored on the local filesystem under the configured data directory.

The application keeps file metadata in SQLite and serves file contents from local disk.

## Share Token Mechanism

Public file and folder access uses generated share tokens.

File direct links use:

```text
/public/<token>/<filename>
```

File share pages use:

```text
/share/<token>
```

Folder share pages use:

```text
/share/folder/<token>
```

The direct link is optimized for downloading. The share page is optimized for displaying metadata before download. Folder sharing displays files inside the shared folder and provides file download links.

## Download Flow

Authenticated file downloads use:

```text
/api/drive/files/<file_id>/download
```

Public file downloads use:

```text
/public/<token>/<filename>
```

Folder share file downloads use:

```text
/share/folder/<token>/file/<file_id>/download
```

Download responses include:

```text
Content-Disposition: attachment
```

This keeps browser behavior in download mode instead of opening a blank page.
