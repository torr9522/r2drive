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
- One-command installer for Debian servers

## Image Hosting

The `我的图床` workspace provides public image hosting for PNG, JPG, JPEG, WEBP, and GIF files. It includes serial drag-and-drop uploads, image previews, direct-link/Markdown/HTML copy actions, folder organization, multi-select, batch delete, and moving images between folders.

## One-Command Install

Run this on a fresh Debian 11+ server as root:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/torr9522/r2drive/main/install.sh)
```

The installer will prompt for your drive domain, install dependencies, clone the repository to `/opt/r2-drive`, check out the latest `vX.Y.Z` release tag, configure systemd, generate a Caddy HTTPS reverse proxy config, and start the service. Pass a release tag such as `v1.8.1` as the first argument to install that exact version.

Before running the installer, make sure the domain points to the server IP and ports `80` and `443` are open.

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

## Development / Regression Baseline

The current development and release baseline is documented in [`docs/BASELINE-v1.8.1.md`](docs/BASELINE-v1.8.1.md). Future releases should use it as the compatibility and regression checklist.
