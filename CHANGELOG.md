# Changelog

## 未发布 / Next

Added:

- File download count statistics
- File cumulative download traffic statistics
- SQLite automatic migration for old data
- File list download statistics display

## v1.2.0

Added:

- File download traffic limit
- `download_limit_bytes` field
- Support setting per-file maximum download traffic
- Automatically forbid downloads after the limit is exceeded

## v1.3.0

Added:

- Public direct-link format optimization
- New share links no longer display file names
- New format: `/public/<token>`

Compatibility:

- Old `/public/<token>/<filename>` links remain valid

## v1.4.0

Added:

- 下载流量限制改为 GB 输入
- 新增网页内流量限制 Modal
- 文件列表显示格式化流量限制

Improved:

- 文件列表支持桌面窄窗口横向滚动
- 保持移动端卡片布局

Unchanged:

- 下载统计逻辑不变
- 流量限制逻辑不变
- 分享 URL 不变
- 下载接口不变

## v1.0.0

Initial version archive.

## v1.0.1

Added:

- File share page
- Folder sharing

Fixed:

- Download button blank-page issue

## v1.0.2

Fixed:

- Mobile hidden share button issue

Added:

- Mobile file actions:
  - Download
  - Direct-link share
  - Share page
  - Delete

Changed files:

- `app.py`
