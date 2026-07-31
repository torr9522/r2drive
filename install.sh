#!/usr/bin/env bash
set -Eeuo pipefail

REPO_URL="https://github.com/torr9522/r2drive.git"
APP_DIR="${R2_DRIVE_APP_DIR:-/opt/r2-drive}"
DATA_DIR="${R2_DRIVE_DATA_DIR:-$APP_DIR/data}"
SERVICE_NAME="${R2_DRIVE_SERVICE_NAME:-r2-drive}"
APP_HOST="${R2_DRIVE_HOST:-127.0.0.1}"
APP_PORT="${R2_DRIVE_PORT:-8090}"
CADDYFILE_PATH="${R2_DRIVE_CADDYFILE:-/etc/caddy/Caddyfile}"
SYSTEMD_DIR="${R2_DRIVE_SYSTEMD_DIR:-/etc/systemd/system}"
DRY_RUN="${R2_DRIVE_INSTALL_DRY_RUN:-0}"
ASSUME_YES="${R2_DRIVE_ASSUME_YES:-0}"
DOMAIN="${R2_DRIVE_DOMAIN:-}"

log() {
    printf '[INFO] %s\n' "$*"
}

warn() {
    printf '[WARN] %s\n' "$*" >&2
}

fail() {
    printf '[ERROR] %s\n' "$*" >&2
    exit 1
}

run() {
    if [ "$DRY_RUN" = "1" ]; then
        printf '[DRY-RUN] %q' "$1"
        shift
        for arg in "$@"; do
            printf ' %q' "$arg"
        done
        printf '\n'
        return 0
    fi
    "$@"
}

need_root() {
    if [ "$(id -u)" -ne 0 ]; then
        fail "请使用 root 用户执行安装脚本"
    fi
}

check_debian() {
    if [ ! -r /etc/os-release ]; then
        fail "无法识别系统版本，仅支持 Debian 11+"
    fi
    # shellcheck disable=SC1091
    . /etc/os-release
    if [ "${ID:-}" != "debian" ]; then
        fail "当前系统为 ${PRETTY_NAME:-unknown}，仅支持 Debian 11+"
    fi
    major="${VERSION_ID%%.*}"
    if ! [[ "$major" =~ ^[0-9]+$ ]] || [ "$major" -lt 11 ]; then
        fail "当前 Debian 版本为 ${VERSION_ID:-unknown}，仅支持 Debian 11+"
    fi
    log "系统检查通过：${PRETTY_NAME:-Debian}"
}

prompt_domain() {
    if [ -n "$DOMAIN" ]; then
        return
    fi
    if [ -r /dev/tty ]; then
        printf '请输入网盘域名，例如 drive.example.com: ' > /dev/tty
        read -r DOMAIN < /dev/tty
    else
        printf '请输入网盘域名，例如 drive.example.com: '
        read -r DOMAIN
    fi
    DOMAIN="$(printf '%s' "$DOMAIN" | tr -d '[:space:]')"
    if [ -z "$DOMAIN" ]; then
        fail "域名不能为空"
    fi
    if ! [[ "$DOMAIN" =~ ^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?(\.[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$ ]]; then
        fail "域名格式不正确：$DOMAIN"
    fi
}

install_caddy_repo_if_needed() {
    if apt-cache show caddy >/dev/null 2>&1; then
        return
    fi
    log "当前 APT 源未找到 caddy，添加 Caddy 官方 Debian 源"
    run apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl gpg
    run install -d -m 0755 /usr/share/keyrings
    if [ "$DRY_RUN" = "1" ]; then
        log "跳过 Caddy GPG key 下载写入（dry-run）"
        return
    fi
    curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key \
        | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt \
        > /etc/apt/sources.list.d/caddy-stable.list
    apt-get update
}

install_dependencies() {
    log "安装依赖：git python3 python3-pip caddy"
    run apt-get update
    run apt-get install -y git python3 python3-pip curl ca-certificates
    install_caddy_repo_if_needed
    run apt-get install -y caddy
}

confirm_update_existing_repo() {
    if [ ! -d "$APP_DIR" ]; then
        return
    fi
    if [ ! -d "$APP_DIR/.git" ]; then
        fail "$APP_DIR 已存在但不是 Git 仓库。为避免覆盖数据，请手动处理后重试。"
    fi
    if [ "$ASSUME_YES" = "1" ]; then
        return
    fi
    answer=""
    if [ -r /dev/tty ]; then
        printf '%s 已存在，是否执行 git pull 更新源码？[y/N]: ' "$APP_DIR" > /dev/tty
        read -r answer < /dev/tty
    else
        printf '%s 已存在，是否执行 git pull 更新源码？[y/N]: ' "$APP_DIR"
        read -r answer
    fi
    case "$answer" in
        y|Y|yes|YES) ;;
        *) fail "用户取消更新" ;;
    esac
}

fetch_source() {
    log "准备源码目录：$APP_DIR"
    if [ -d "$APP_DIR" ]; then
        confirm_update_existing_repo
        run git -C "$APP_DIR" pull --ff-only
    else
        run mkdir -p "$(dirname "$APP_DIR")"
        run git clone "$REPO_URL" "$APP_DIR"
    fi
}

check_python() {
    log "检查 Python 应用"
    run python3 -m py_compile "$APP_DIR/app.py"
    if [ -s "$APP_DIR/requirements.txt" ]; then
        run python3 -m pip install -r "$APP_DIR/requirements.txt"
    else
        log "requirements.txt 为空，跳过 pip 依赖安装"
    fi
}

write_caddyfile() {
    log "生成 Caddy 配置：$CADDYFILE_PATH"
    run mkdir -p "$(dirname "$CADDYFILE_PATH")"
    if [ "$DRY_RUN" = "1" ]; then
        if [ -e "$CADDYFILE_PATH" ]; then
            log "将备份已有 Caddy 配置：$CADDYFILE_PATH.bak-YYYYmmddHHMMSS"
        fi
        cat <<EOF
[DRY-RUN] 将写入 $CADDYFILE_PATH:
$DOMAIN {
    encode zstd gzip
    reverse_proxy $APP_HOST:$APP_PORT

    header {
        X-Content-Type-Options nosniff
        Referrer-Policy strict-origin-when-cross-origin
    }
}
EOF
        return
    fi
    if [ -e "$CADDYFILE_PATH" ]; then
        cp "$CADDYFILE_PATH" "$CADDYFILE_PATH.bak-$(date +%Y%m%d%H%M%S)"
    fi
    cat > "$CADDYFILE_PATH" <<EOF
$DOMAIN {
    encode zstd gzip
    reverse_proxy $APP_HOST:$APP_PORT

    header {
        X-Content-Type-Options nosniff
        Referrer-Policy strict-origin-when-cross-origin
    }
}
EOF
}

install_systemd_service() {
    log "安装 systemd 服务：$SERVICE_NAME"
    run mkdir -p "$SYSTEMD_DIR"
    service_path="$SYSTEMD_DIR/$SERVICE_NAME.service"
    if [ "$DRY_RUN" = "1" ]; then
        if [ -e "$service_path" ]; then
            log "将备份已有 systemd 服务：$service_path.bak-YYYYmmddHHMMSS"
        fi
        log "将复制 $APP_DIR/deploy/r2-drive.service 到 $service_path"
    else
        if [ -e "$service_path" ]; then
            cp "$service_path" "$service_path.bak-$(date +%Y%m%d%H%M%S)"
        fi
        cp "$APP_DIR/deploy/r2-drive.service" "$service_path"
    fi
    run systemctl daemon-reload
    run systemctl enable --now "$SERVICE_NAME"
}

init_data_dir() {
    log "初始化数据目录：$DATA_DIR"
    run mkdir -p "$DATA_DIR"
    run chmod 755 "$DATA_DIR"
}

server_public_ips() {
    {
        hostname -I 2>/dev/null | tr ' ' '\n'
        curl -4 -fsSL --max-time 5 https://api.ipify.org 2>/dev/null || true
    } | awk 'NF && !seen[$0]++'
}

domain_ips() {
    getent ahostsv4 "$DOMAIN" 2>/dev/null | awk '{print $1}' | awk '!seen[$0]++'
}

check_dns() {
    log "检查 DNS 解析"
    mapfile -t resolved < <(domain_ips)
    mapfile -t local_ips < <(server_public_ips)
    if [ "${#resolved[@]}" -eq 0 ]; then
        warn "域名暂未解析到 IPv4 地址：$DOMAIN"
        return
    fi
    printf '域名解析结果：%s\n' "${resolved[*]}"
    printf '服务器检测到的 IP：%s\n' "${local_ips[*]:-unknown}"
    for rip in "${resolved[@]}"; do
        for lip in "${local_ips[@]}"; do
            if [ "$rip" = "$lip" ]; then
                log "DNS 已解析到当前服务器：$rip"
                return
            fi
        done
    done
    warn "DNS 解析结果未匹配当前服务器 IP，Caddy 可能无法签发 HTTPS 证书。"
}

restart_caddy() {
    log "验证并启动 Caddy"
    run caddy validate --config "$CADDYFILE_PATH"
    run systemctl restart caddy
}

print_certificate_status() {
    if [ "$DRY_RUN" = "1" ]; then
        log "跳过证书检查（dry-run）"
        return
    fi
    log "检查 HTTPS 证书"
    for _ in $(seq 1 20); do
        cert_info="$(echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null | openssl x509 -noout -subject -issuer -ext subjectAltName 2>/dev/null || true)"
        if printf '%s\n' "$cert_info" | grep -Fq "DNS:$DOMAIN"; then
            printf '%s\n' "$cert_info"
            return
        fi
        sleep 3
    done
    warn "暂未确认到包含 $DOMAIN 的证书，请检查 DNS、80/443 防火墙和 Caddy 日志。"
}

print_summary() {
    cat <<EOF
================================

R2 Drive 安装完成

访问地址:
https://$DOMAIN

运行目录:
$APP_DIR

服务状态:
systemctl status $SERVICE_NAME

================================
EOF
}

main() {
    need_root
    check_debian
    prompt_domain
    install_dependencies
    fetch_source
    init_data_dir
    check_python
    write_caddyfile
    install_systemd_service
    check_dns
    restart_caddy
    print_certificate_status
    print_summary
}

main "$@"
