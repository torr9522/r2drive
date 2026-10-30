# 上传流水线

## 浏览器

```mermaid
sequenceDiagram
  participant U as User
  participant Q as Upload queue
  participant X as XHR
  participant A as API
  participant D as Disk/SQLite
  U->>Q: select/drop files
  Q->>Q: capture kind + targetFolderId
  Q->>X: next queued task only
  X->>A: multipart(file, folderId)
  X-->>Q: progress events update task DOM
  A->>D: validate folder, write file, insert row
  A-->>X: file DTO
  X-->>Q: done or failed; continue queue
  Q->>Q: refresh only relevant visible list
```

`enqueueUploads()` / `enqueueImageUploads()` 为每个文件创建任务。任务持有入队时的目标目录，而不是上传开始时读取当前 `S.folder`。队列串行，避免并发导致界面和 SQLite 写入竞争。切换页面或目录不会取消正在运行的 XHR。

## 局部更新约束

`uploadTask()` 的 `xhr.upload.onprogress` 只能更新任务对象和上传区域。不得调用整页 `render()`。上传期间用户必须能滚动、搜索、打开界面和切换目录；任务完成时 `refreshUploadedTarget()` 只在用户仍查看该任务目标时刷新相关列表。

## 服务端

`parse_upload()` 检查 Content-Length、默认 10 GiB 上限、multipart 类型和单个 `file` 字段。`python-multipart` 解析请求；文件对象以 1 MiB 块复制到使用 `xb` 创建的唯一目标。图片还需扩展名、MIME 和 magic signature 三重匹配。

数据库插入失败、格式失败或其他异常会删除已创建实体。上传没有分片、断点续传、重试协议或服务端队列；浏览器刷新会失去客户端队列状态，但不会回滚已经完成的文件。

## 为什么不能恢复旧 render

`app.innerHTML` 会替换 `.shell` 及其输入、滚动容器和事件节点。频繁进度事件调用它会造成搜索焦点丢失、滚动跳动、Modal 状态冲突，并让测试无法保证任务节点身份稳定。强行恢复 `scrollTop` 不能恢复焦点和节点身份，因此不是可接受修复。
