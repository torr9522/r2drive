# ADR-0010：systemd 使用专用非 root 用户

- 状态：Accepted（v1.8.3）

旧服务没有 `User=`，应用和上传以 root 运行，扩大路径漏洞影响。选择系统用户 `r2-drive`，只让其写数据目录，并启用 `NoNewPrivileges`、`PrivateTmp`、`ProtectSystem=strict` 和 0077 umask。

代价是升级/恢复必须正确 chown 数据，源码和虚拟环境需可读执行。不要为解决权限错误取消 hardening 或改回 root；先核对目录所有权和 `ReadWritePaths`。
