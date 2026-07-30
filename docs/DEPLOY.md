# Deployment

This document records the deployment process for R2 Drive Personal Edition.

## System Requirements

- Debian 11 or compatible Linux server
- Python 3.9+
- Caddy 2
- systemd
- A domain name pointing to the server

Current production domain:

```text
vmissmx.88988588.xyz
```

## Directory Structure

Recommended runtime directory:

```text
/opt/r2-drive/
├── app.py
├── r2-drive.service
└── data/
    └── drive.sqlite3
```

Repository source directory:

```text
r2-drive-vps/
├── app.py
├── requirements.txt
├── deploy/
│   ├── r2-drive.service
│   └── Caddyfile
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEPLOY.md
│   └── DEVELOPMENT.md
├── CHANGELOG.md
├── README.md
└── .gitignore
```

## Install Dependencies

```bash
apt update
apt install -y python3 caddy
```

R2 Drive currently uses only the Python standard library. `requirements.txt` is kept for future dependency tracking.

## Install Application

```bash
mkdir -p /opt/r2-drive/data
cp app.py /opt/r2-drive/app.py
cp deploy/r2-drive.service /etc/systemd/system/r2-drive.service
```

## Configure systemd

The service file is stored at:

```text
deploy/r2-drive.service
```

Install and start it:

```bash
systemctl daemon-reload
systemctl enable --now r2-drive
systemctl status r2-drive --no-pager
```

The current service uses:

```text
R2_DRIVE_DATA=/opt/r2-drive/data
R2_DRIVE_SITE_NAME=R2 Drive
R2_DRIVE_HOST=127.0.0.1
R2_DRIVE_PORT=8090
```

## Configure Caddy

The Caddy config is stored at:

```text
deploy/Caddyfile
```

Install it:

```bash
cp deploy/Caddyfile /etc/caddy/Caddyfile
caddy validate --config /etc/caddy/Caddyfile
systemctl reload caddy
```

Caddy terminates HTTPS and proxies traffic to:

```text
127.0.0.1:8090
```

## Start and Verify

```bash
systemctl restart r2-drive
systemctl status r2-drive --no-pager
curl -I https://vmissmx.88988588.xyz/
```

Expected result:

- HTTP 200 from the site
- `/api/status` returns initialized status
- Public downloads include `Content-Disposition: attachment`

## Update Procedure

```bash
cd /opt/r2-drive
cp /path/to/new/app.py /opt/r2-drive/app.py
systemctl restart r2-drive
systemctl status r2-drive --no-pager
```

For repository-based updates:

```bash
git pull
cp app.py /opt/r2-drive/app.py
systemctl restart r2-drive
```

Do not overwrite `/opt/r2-drive/data` during an application update.

## Backup Procedure

Back up the runtime data directory:

```bash
tar -czf r2-drive-data-$(date +%F).tar.gz /opt/r2-drive/data
```

The backup should include:

- SQLite database
- Uploaded files

Do not commit backups, database files, uploaded files, passwords, TLS private keys, or `.env` files to Git.
