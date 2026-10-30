# 备份与恢复

## 一致性备份

数据库记录包含实体绝对路径，因此最稳妥方法是在短维护窗口停止应用并整体备份 `data/`：

```bash
install -d -m 0700 /var/backups/r2-drive
systemctl stop r2-drive
tar -C /opt/r2-drive -czf /var/backups/r2-drive/data-$(date +%F-%H%M%S).tar.gz data
systemctl start r2-drive
systemctl is-active r2-drive
```

备份不应包含 Caddy 全局存储、其他站点或整个 `/opt`。另行记录正在运行的 Tag/commit 和站点片段。将备份传到受控异机存储，并验证可读：

```bash
tar -tzf /var/backups/r2-drive/data-YYYY-MM-DD-HHMMSS.tar.gz | head
```

## 恢复

恢复会覆盖当前数据，只能在目标和备份已经人工确认后执行：

```bash
systemctl stop r2-drive
mv /opt/r2-drive/data /opt/r2-drive/data.before-restore
tar -C /opt/r2-drive -xzf /var/backups/r2-drive/data-YYYY-MM-DD-HHMMSS.tar.gz
chown -R r2-drive:r2-drive /opt/r2-drive/data
chmod 0750 /opt/r2-drive/data
runuser -u r2-drive -- python3 - <<'PY'
import sqlite3
p = '/opt/r2-drive/data/drive.sqlite3'
with sqlite3.connect(f'file:{p}?mode=ro', uri=True) as db:
    print(db.execute('PRAGMA integrity_check').fetchone()[0])
PY
systemctl start r2-drive
```

只有完整验收后才能删除 `data.before-restore`。恢复到不同应用目录时，旧 `storage_path` 仍指向原绝对路径；当前没有自动重写工具，必须先设计和测试迁移。

## 恢复验收

- 管理员登录和 Cookie 属性。
- 文件/图片列表与磁盘实体数量合理。
- 私有下载、旧公开链接和文件夹分享。
- Range、统计和流量限额。
- 服务重启后数据仍存在。
- 数据库 integrity 为 `ok`。

不要把备份、数据库或文件提交到 Git。
