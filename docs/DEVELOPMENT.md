# Development

All future secondary development should start from the remote Git repository baseline.

## Local Development

Run the application locally:

```bash
python3 app.py
```

Useful environment variables:

```bash
export R2_DRIVE_DATA=/tmp/r2-drive-data
export R2_DRIVE_SITE_NAME="R2 Drive"
export R2_DRIVE_HOST=127.0.0.1
export R2_DRIVE_PORT=8090
python3 app.py
```

## Development Rules

- Do not change storage format without a migration plan.
- Do not remove compatibility for `/public/<token>/<filename>`.
- Keep `/share/<token>` and `/share/folder/<token>` separate from direct links.
- Do not add multi-user behavior unless it is explicitly planned.
- Do not commit runtime data, databases, uploads, logs, secrets, or TLS private keys.

## Baseline Features to Re-test

- File upload
- File list
- Folder management
- Authenticated download
- Public direct-link download
- File share page download
- Folder share page browsing
- Folder share page file download
- PC file action buttons
- Mobile file action buttons
