# 运行维护

## 状态和日志

```bash
systemctl status r2-drive caddy --no-pager
systemctl show r2-drive -p MainPID -p User -p Group -p ExecStart
ss -ltnp | grep -E ':(80|443|8090)\b'
journalctl -u r2-drive -n 200 --no-pager
journalctl -u caddy -n 200 --no-pager
curl -fsS http://127.0.0.1:8090/api/status
curl -fsS https://drive.example.com/api/status
```

应用覆盖 `log_message()`，不输出默认访问日志。HTTP 500 也不输出堆栈，因此诊断信息有限；不要通过记录请求 Cookie 或上传内容来补日志。

## 常见问题

- 502：检查 R2 服务、8090 listener、虚拟环境和数据权限。
- 登录 Cookie 无 Secure：检查 Caddy 是否传 `X-Forwarded-Proto: https`，以及用户确实通过 HTTPS 访问。
- database locked：检查是否有长事务/外部写进程；当前连接 timeout 和 busy timeout 均为 15 秒。
- 上传 413：检查 `R2_DRIVE_MAX_UPLOAD_BYTES` 与反向代理限制。
- 分享 404：确认 Token 当前有效、文件未设私密/删除、目录属于 `drive`。
- Caddy 校验失败：先 `caddy validate`，不要循环重启或覆盖整个配置。

## 维护窗口

一致性备份、恢复和手工数据库检查应停止 R2 服务。Caddy 和其他站点无需随应用停止。重启后检查 `PRAGMA integrity_check`、服务状态和 HTTPS。

## 权限

```bash
stat -c '%a %U:%G %n' /opt/r2-drive/data
find /opt/r2-drive/data -maxdepth 2 -printf '%m %u:%g %p\n'
```

修复数据所有权时只操作确认属于 R2 Drive 的 `/opt/r2-drive/data`，不要递归修改 `/opt`、`/var/lib/caddy` 或其他站点。
