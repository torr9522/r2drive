# Changelog

## 未发布 / Next

Added:

- File download count statistics
- File cumulative download traffic statistics
- SQLite automatic migration for old data
- File list download statistics display
- 新增 `install.sh`
- 支持自动部署
- 支持自动 HTTPS

## v1.8.1

### Changed

- 移动端新增 Drawer 导航
- 移动端 Header 精简
- 网盘移动端工具栏重新布局
- 图床移动端工具栏重新布局
- 图床移动端图片操作改为“预览 / 直链 / 更多”
- 手机图床上传区域压缩并改为点击上传提示
- 批量工具栏移动端重新排版

### Fixed

- 修复移动端“新建文件夹”按钮换行和爆框风险
- 修复网盘移动端上传 label 与按钮视觉不对称
- 修复移动端工具栏两列宽高不一致
- 优化移动端首屏空间占用

## v1.8.0

### Added

- 我的图床，支持图片模式和列表模式
- JPG/JPEG/PNG/WEBP/GIF 上传、拖拽上传和串行上传队列
- 图床文件夹和多级子文件夹
- 图片预览、复制直链、复制 Markdown、复制 HTML
- 单选、多选、全选、批量删除
- 单张和批量移动到文件夹

### Changed

- 图床公共图片链接使用 `inline`，普通网盘文件继续使用 `attachment`
- 网盘和图床文件、文件夹分类隔离
- 优化图床列表长文件名、移动端布局和滚动位置保持

### Fixed

- 修复 systemd `R2_DRIVE_SITE_NAME` Environment 引号
- 修复列表选择按钮布局和选择跳顶部问题
- 上传任务在入队时固定目标文件夹，避免切换目录造成错传

### Compatibility

- v1.7.0 旧数据库自动迁移，旧文件和文件夹归类为 `drive`
- 旧公开链接、Range、下载统计和流量限制保持兼容

## v1.8.0-rc1

Release Candidate，尚未正式发布。

Added:

- 新增“我的图床”
- 图床 PNG/JPG/JPEG/WEBP/GIF 上传
- 图床卡片管理
- 图片预览 Modal
- 复制直链
- 复制 Markdown
- 复制 HTML
- 图片删除 Modal
- `file_category` 隔离 `drive` / `image_host`
- 图片公共直链使用 `inline`
- 普通网盘文件保持 `attachment`

Fixed:

- 修复 systemd `Environment` 引号

## v1.7.0

Added:

- 新上传文件默认公开
- 新建文件夹默认公开
- 文件夹公开/私密切换
- 多文件上传串行队列

Changed:

- 上传任务改为队列执行
- 保留上传进度

Compatible:

- 下载接口未修改
- 分享 URL 未修改
- 数据库结构未破坏
- 下载统计逻辑未修改

## v1.5.0

### Added

- 新增真实下载流量统计
- 下载流量按实际发送字节累计
- 支持 HTTP Range 请求
- 支持 206 Partial Content

### Changed

- 下载次数只统计完整下载
- Range 请求只累计流量，不增加下载次数

### Fixed

- 修复微信/QQ/浏览器探测导致下载次数和流量虚高问题

### Compatible

- 保留旧 `/public/<token>/<filename>`
- 支持新 `/public/<token>`
- 保持 `/share/<token>` 不变

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
