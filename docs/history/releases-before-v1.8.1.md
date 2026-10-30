# v1.0.0 至 v1.8.0

本页由正式 Tag、commit diff 和各 Tag 中的 `CHANGELOG.md` 恢复。Changelog 中曾出现 `v1.0.1`、`v1.0.2` 和 `v1.8.0-rc1` 小节，但仓库没有对应正式 Tag；不能把这些小节当作已发布版本。

## v1.0.0

正式 commit `6a8c376b0eedd35930c5c544763d34e85afe0098`。建立单文件 Python 应用、SQLite、本地存储、认证、网盘、文件夹和分享的初始基线。

## v1.1.0 至 v1.5.0

- `v1.1.0`：下载次数和累计流量进入文件元数据及界面。
- `v1.2.0`：增加 `download_limit_bytes`，达到上限时拒绝下载。
- `v1.3.0`：新链接隐藏文件名，改为 `/public/<token>`，仍接受 `/public/<token>/<filename>`。
- `v1.4.0`：流量限制 UI 使用 GB 输入和站内 Modal，改善窄桌面列表。
- `v1.5.0`：支持单 Range、206 和实际写出字节统计；完整 GET 才增加下载次数，HEAD 不统计。

## v1.6.0 和 v1.7.0

`v1.6.0` 增加 `install.sh`、Caddy 和 systemd 自动部署。`v1.7.0` 让新文件和新文件夹默认公开，引入串行多文件上传队列，保持既有分享和统计语义。

## v1.8.0

正式 commit `db8c997cf8360595129e236ef63b60e24235ab1d`。加入图床、图片/列表视图、格式签名校验、预览、Markdown/HTML 链接、多选、批量删除和移动。`file_category` / `folder_category` 将图床与网盘隔离；旧行默认迁移为 `drive`。上传目标目录开始在入队时冻结。
