# ADR-0012：部署使用 Python 虚拟环境

- 状态：Accepted（v1.8.3）

引入 `python-multipart` 后，全局 pip 会污染系统和其他站点。选择 `/opt/r2-drive/.venv`，systemd 明确执行其中 Python，安装脚本在环境内升级 pip 和安装 requirements。

代价是升级要重建/更新环境，占用额外空间，并要求 `python3-venv`。不要依赖管理员 shell 的激活状态；服务和命令使用完整 `.venv/bin/python` 路径。
