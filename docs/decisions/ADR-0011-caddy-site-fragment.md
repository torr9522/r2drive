# ADR-0011：Caddy 使用独立站点片段

- 状态：Accepted（v1.8.3）

重写 `/etc/caddy/Caddyfile` 会破坏同机站点和证书管理。选择 `/etc/caddy/sites-enabled/r2-drive.caddy`，主配置仅在缺少时追加 wildcard import，并在覆盖应用片段前备份。

代价是必须管理 import、文件权限和重复域名；安装脚本目前仍重启 Caddy。真实部署曾因片段权限不可读失败，后续固定 0644。共享服务器需 validate 并检查其他站点，绝不能删除 Caddy 全局 storage。
