# R2 Drive Personal Edition

R2 Drive Personal Edition is a personal private drive and software release center.

It is designed for a single owner who needs a small self-hosted file manager with upload, browsing, download, and public sharing features.

## Current Technology

- Python standard library HTTP server
- SQLite metadata database
- Local filesystem file storage
- Caddy HTTPS reverse proxy
- systemd service management

## Implemented Features

- File upload
- File list
- Folder management
- File download
- Attachment download mode
- File direct-link sharing
- File share page
- Folder share page
- Mobile layout adaptation
- SQLite database storage
- HTTPS through Caddy
- systemd auto start

## Sharing System

R2 Drive has three separate sharing modes. They must remain compatible with each other.

### Direct Link

```text
/public/<token>/<filename>
```

The direct link downloads the file directly. It is intended for software releases, package downloads, and any case where the browser should receive the file as an attachment.

### File Share Page

```text
/share/<token>
```

The file share page displays file metadata before download, including file name, size, type, and update time. Its download button reuses the public file download path.

### Folder Share

```text
/share/folder/<token>
```

The folder share page displays the shared folder name and its file list. Files inside the shared folder can be browsed and downloaded from the folder share page.

## Version Baseline

Current baseline: `v1.0.x`

This repository is the first formal source archive for future secondary development.
