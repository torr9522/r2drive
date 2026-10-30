# 后端架构

## 入口

`app.py` 在直接执行时调用 `init_db()`，然后创建 `ThreadingHTTPServer`。默认监听 `127.0.0.1:8090`，可由 `R2_DRIVE_HOST` / `R2_DRIVE_PORT` 覆盖。

`Handler.route()` 的顺序是 API、文件夹分享、文件分享、公开文件，最后对其他 GET/HEAD 返回 SPA shell。业务异常使用 `HttpError(status, message)`，API 错误为 `{"error":"..."}`；未分类异常返回 500，不向客户端泄露堆栈。

## 业务边界

- 私有 API 在路由分发后统一 `require_auth()`。
- 网盘查询要求 `file_category='drive'` / `folder_category='drive'`。
- 图床查询要求 `image_host`，移动目标也必须是图床目录。
- 上传先写唯一磁盘路径，再插入数据库；异常删除已写文件。
- 删除文件先容忍磁盘实体已缺失，再删除记录。
- 非空目录返回 409，不做级联删除。

## 请求限制

- JSON 最大 1 MiB。
- 上传最大值默认 10 GiB，可用 `R2_DRIVE_MAX_UPLOAD_BYTES` 调整。
- multipart 请求必须正好有一个名为 `file` 的文件字段。
- 名称拒绝 `/`、反斜线和 NUL；展示名最长 180，目录名最长 80。

## 下载

下载使用 16 KiB 块写出，支持单一 bytes Range 和 suffix Range，不支持多段 Range。HEAD 发送头但不读取实体、不更新统计。写出中断只累计已经发送的字节。
