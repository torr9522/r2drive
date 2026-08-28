# R2 Drive v1.8.1 Regression Baseline

本文档是 R2 Drive v1.8.1 的功能、运行、安全和发布基线。后续版本（包括 v1.8.2、v1.9.0 和 v2.x）必须以此清单进行兼容性审查和发布回归。

## 1. 版本身份

- 版本：`v1.8.1`
- 正式 commit：`6a6b8ca1726f67a6aac936b8baf83601f8b1881d`
- 主程序：`app.py`
- 正式版本使用 annotated tag；未经明确迁移方案，不得删除或改变既有接口行为。

## 2. 运行架构

- Python 标准库 HTTP 服务
- SQLite 元数据数据库
- 原生 HTML、CSS、JavaScript 前端（随 `app.py` 提供）
- Caddy 反向代理和自动 HTTPS
- systemd 服务管理
- 应用默认监听 `127.0.0.1:8090`
- Caddy 对外提供 HTTP/HTTPS（80/443）
- `data/`、SQLite、上传实体和运行日志属于外部运行数据，不应提交到 Git。

## 3. 我的网盘功能基线

### 文件

- 上传和串行上传队列
- 下载、HTTP Range、HEAD
- 重命名、删除、搜索
- 公开/私密切换
- 复制直链、分享页
- 下载次数、实际下载流量
- 单文件下载流量限制

### 文件夹

- 新建、进入、重命名
- 多级目录和面包屑
- 空文件夹可删除；非空文件夹删除必须拒绝

## 4. 我的图床功能基线

### 格式和上传

- JPG、JPEG、PNG、WEBP、GIF
- SVG 必须拒绝
- 同时校验扩展名、MIME 和文件头
- 点击选择上传
- 桌面拖拽上传
- 串行队列，最大并发为 1
- 单项失败后继续后续任务
- 入队时冻结 `targetFolderId`

### 视图和图片操作

- 图片模式、列表模式
- 使用 `localStorage` 记忆视图
- 预览、复制直链、复制 Markdown、复制 HTML
- 单选、多选、全选
- 批量删除
- 单图移动、批量移动
- 多级文件夹、面包屑
- 移动到 root 或子目录
- 同目录移动返回 `skipped`

## 5. 分类隔离

- `files.file_category` 只能按功能归类为 `drive` 或 `image_host`
- `folders.folder_category` 只能按功能归类为 `drive` 或 `image_host`
- 网盘 API 只能操作 `drive` 实体；图床 API 只能操作 `image_host` 实体
- 图床文件不得移动到网盘文件夹，反向亦然
- 移动图片只修改 `folder_id` 和时间戳，不修改 `storage_path`

## 6. 公共链接兼容

以下路径必须保持兼容：

- `/public/<token>`
- `/public/<token>/<filename>`
- `/share/<token>`
- `/share/folder/<token>`

图床公共文件使用 `Content-Disposition: inline`；普通网盘文件使用 `attachment`。

## 7. 下载统计基线

- 响应提供 `Accept-Ranges: bytes`
- 有效 Range 返回 `206`
- 非法 Range 返回 `416`
- HEAD 不增加统计
- Range 只增加 `download_bytes`，不增加 `download_count`
- 完整 GET 成功完成后 `download_count + 1`
- `download_bytes` 只累计实际成功写出的字节
- 下载中断时只记录已经写出的字节

## 8. 流量限制

- 字段：`download_limit_bytes`
- `NULL` 表示不限流量
- 达到限制后返回 `403`
- 数据库存储单位为 byte，UI 可使用 MB/GB 显示
- 网盘和图床复用同一套下载统计和限流规则

## 9. UI 交互基线

- 业务代码中的 `alert(`、`confirm(`、`prompt(` 必须为 0
- 统一使用站内 Modal、Toast、Action Sheet
- 选择、全选、上传完成、Modal 关闭不得跳回顶部
- 主要滚动容器为 `.work`，不是 `window`
- 遮罩、Toast、滚动锁关闭后不得残留

## 10. 移动端基线

断点为 `<= 920px`。

- 使用 Drawer 和精简 Header
- 网盘工具栏：`[新建文件夹] [上传文件]`，下一行独占 `[搜索]`
- 图床工具栏：`[新建文件夹] [全选]`、`[图片模式] [列表模式]`、下一行 `[搜索]`
- 图床图片操作：`预览 / 直链 / 更多`
- Action Sheet：Markdown、HTML、移动、删除
- 375、390、430px 必须无横向溢出，按钮文字不得爆框或异常换行

## 11. 数据库兼容

关键表为 `files` 和 `folders`，包含分类字段、分享字段、统计字段和时间字段。数据库升级使用 `ensure_column()` 增量迁移；旧 v1.7 数据默认归类为 `drive`，不得要求删除或重建旧 SQLite。

## 12. 安全基线

- 所有读写 API 必须校验当前用户
- 图床 API 必须额外校验 `file_category='image_host'`
- 图床目录必须额外校验 `folder_category='image_host'`
- 文件名继续经过 `clean_name` 和 `safe_name`
- SVG 不得作为图床 inline 内容
- token、session、密码、数据库内容和测试凭据不得硬编码或提交 Git

## 13. 发布规则

- 正式版本必须使用 annotated tag
- R2 Drive 不使用 RC、Beta、Alpha 或其他多渠道发布模型
- 开发和测试阶段不创建版本 tag
- 完整 Regression Baseline 验收通过后，直接创建 `vX.Y.Z` annotated tag
- 正式推送只推送 `main` 和正式版本 tag
- 禁止使用 `git push --tags`
- 发布前必须检查工作区、敏感信息、Python、JavaScript 和 `git diff --check`

## 14. Release Regression Matrix

### 视口

- 移动端：375、390、430
- 桌面端：1000、1366、1920

### 功能

- 网盘上传、下载、直链、分享、Range、统计、限流
- 图床上传、预览、复制、文件夹、多选、批量删除、批量移动
- 串行上传和 `targetFolderId` 冻结
- Drawer、Action Sheet、Modal、Toast
- 下载后立即复制直链
- 滚动位置保持
- Console 无 TypeError、DOMException 或未处理 Promise rejection
- 无业务原生弹窗、异常重复请求、横向溢出或数据分类越权
