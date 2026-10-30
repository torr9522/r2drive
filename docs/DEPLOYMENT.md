# 部署

## 前提

- Debian 11+
- root 权限
- 域名 A 记录指向服务器
- 80/443 可达
- systemd

安装脚本会安装 `git python3 python3-venv curl ca-certificates caddy`，创建 `/opt/r2-drive/.venv` 和专用用户。不要升级或替换系统 Python。

## 环境角色

- 开发环境：唯一源码编辑和 Git 管理位置。
- 独立测试环境：部署精确 commit/Tag 做浏览器和 HTTP 验收，不维护另一套分叉源码。
- 生产环境：只部署已授权正式 Tag，不在服务器现场修改源码；当前公开入口见 `CURRENT_BASELINE.md`。

任何测试机临时修复都必须回到开发分支提交，再部署该 commit。仓库不保存 SSH 凭据或主机私钥。

## 预演

在现有服务器，尤其共享 Caddy 服务器上，先检查端口、服务和配置：

```bash
ss -ltnp
systemctl status caddy --no-pager
caddy validate --config /etc/caddy/Caddyfile
R2_DRIVE_INSTALL_DRY_RUN=1 \
R2_DRIVE_DOMAIN=drive.example.com \
bash install.sh v1.8.3
```

dry-run 仍要求 root，但不执行包装在脚本 `run()` 中的变更。

## 正式安装

```bash
R2_DRIVE_DOMAIN=drive.example.com \
bash <(curl -fsSL https://raw.githubusercontent.com/torr9522/r2drive/main/install.sh) v1.8.3
```

脚本会：

1. 检查 Debian 11+ 并安装依赖。
2. Clone 或 fetch `/opt/r2-drive`。
3. 校验 `v1.8.3` 是正式格式且为 annotated tag，detach checkout peeled commit。
4. 创建 `r2-drive` 用户、数据目录和虚拟环境。
5. 安装 `requirements.txt` 并编译检查 `app.py`。
6. 生成 `/etc/caddy/sites-enabled/r2-drive.caddy`，仅在缺失时向主 Caddyfile追加 import。
7. 安装并启动 systemd 服务，检查 DNS，验证并重启 Caddy。

脚本不会删除 `data/`。若应用目录有 tracked 修改会中止；未跟踪文件会保留并警告。

## 共享 Caddy 注意

独立站点片段降低覆盖其他站点风险，但脚本仍会修改主 Caddyfile（仅追加 import）并执行 `systemctl restart caddy`。共享服务器应先备份并阅读全部 import，确认域名未重复，部署前后检查其他站点。需要零中断 reload 的环境应由运维人员按脚本步骤人工部署，不要伪装成执行了原脚本。

`deploy/Caddyfile` 是示例，不应直接覆盖 `/etc/caddy/Caddyfile`。生产域名由安装脚本动态生成。

## 验收

```bash
git -C /opt/r2-drive rev-parse HEAD
git -C /opt/r2-drive describe --tags --exact-match
systemctl is-active r2-drive caddy
systemctl show r2-drive -p User -p Group -p ExecStart
curl -fsS https://drive.example.com/api/status
journalctl -u r2-drive -n 100 --no-pager
```

首次初始化前不要长期暴露公网；立即创建管理员。随后检查 HTTPS 登录 Cookie、上传/下载、分享、Range 和服务重启。

## 升级

先按 [BACKUP_RESTORE.md](BACKUP_RESTORE.md) 做一致性备份，再运行固定版本安装命令。不要部署不确定的 `main`。升级后校验 commit、数据库完整性和旧链接。

## 回滚

代码回滚只能 checkout 已验证旧 Tag；数据必须使用升级前成套备份恢复。先阅读 [RELEASE_PROCESS.md](RELEASE_PROCESS.md) 的回滚限制，避免旧程序写入新 schema。
