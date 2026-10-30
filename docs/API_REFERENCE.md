# HTTP API 参考

## 通用约定

- JSON 请求：`Content-Type: application/json`，最大 1 MiB。
- 上传：`multipart/form-data`，字段 `folderId`（可省略，默认 `root`）和且仅一个 `file`。
- 成功通常返回 200；错误返回 JSON `{"error":"消息"}`。
- 除状态、初始化、登录、登出和公开分享外，API 都要求 `r2_drive_session` Cookie。
- 当前没有 CSRF Token；`SameSite=Lax` 是主要跨站保护，部署必须使用 HTTPS。

## 认证和状态

| Method | Path | 请求 | 返回/规则 |
|---|---|---|---|
| GET | `/api/status` | 无 | `{initialized, siteName}` |
| POST | `/api/initialize` | `{username,password}` | 首次创建 admin 和 Session；已有用户时 409 |
| POST | `/api/login` | `{username,password}` | 用户 DTO 并设置 Cookie；失败 401 |
| POST | `/api/logout` | 无 | `{ok:true}`，删除当前 Session |
| GET | `/api/me` | Cookie | `{username,role}` |
| GET | `/api/stats` | Cookie | 当前用户 `drive` 文件的 `{totalFiles,totalBytes}` |

## 网盘

| Method | Path | 请求 | 行为 |
|---|---|---|---|
| GET | `/api/drive/folders` | 无 | 返回该用户全部 `drive` 目录 |
| POST | `/api/drive/folders` | `{name,parentId}` | 创建默认公开目录 |
| PATCH | `/api/drive/folders/<id>` | `{name}` | 重命名 |
| PATCH | `/api/drive/folders/<id>/public` | `{isPublic}` | 公开时生成新 Token，私密时清空 |
| DELETE | `/api/drive/folders/<id>` | 无 | 仅空目录；root 为 400，非空为 409 |
| GET | `/api/drive/files?folderId=<id>` | query | 返回当前目录 `drive` 文件 |
| POST | `/api/upload` | multipart | 上传默认公开文件 |
| PATCH | `/api/drive/files/<id>` | `{name?,downloadLimitBytes?}` | 至少一个字段；限额为非负整数 byte 或 null |
| PATCH | `/api/drive/files/<id>/public` | `{isPublic}` | 更新公开状态和 Token |
| DELETE | `/api/drive/files/<id>` | 无 | 删除磁盘实体和记录 |
| GET/HEAD | `/api/drive/files/<id>/download` | 可带 Range | 私有 attachment 下载 |

## 通用排序与移动

| Method | Path | 请求 | 行为 |
|---|---|---|---|
| POST | `/api/items/reorder` | `{category,itemType,parentId,ids}` | 对当前同级同类型完整集合排序；成功 `{ok:true,ids}` |
| POST | `/api/items/move` | `{category,items,folderId,conflictPolicy}` | 通用单项/批量移动；返回 `{moved,skipped,failed}` |

`category` 只能为 `drive` / `image_host`，`itemType` 为 `folder` / `file`。排序 `ids` 必须无重复、最多 5000 个，并与服务端事务中读取的完整兄弟集合完全相等；目录已变化返回 409。

移动 `items` 最多 1000 项，每项为 `{type,id}`。`conflictPolicy` 为 `cancel`、`rename` 或 `skip`。目标目录不存在或跨分类为 404；`cancel` 遇同名为 409 并回滚。单项结果原因包括 `not_found`、`cycle`、`covered_by_parent`、`same_folder` 和 `name_conflict`。批量可归因失败使用 200 结果数组，调用方不能把 HTTP 200 等同于全部成功。

## 图床

| Method | Path | 请求 | 行为 |
|---|---|---|---|
| GET | `/api/image-host/folders` | 无 | 全部图床目录和直属图片数 |
| POST | `/api/image-host/folders` | `{name,parentId}` | 创建图床目录 |
| PATCH | `/api/image-host/folders/<id>` | `{name}` | 重命名 |
| DELETE | `/api/image-host/folders/<id>` | 无 | 仅空目录 |
| GET | `/api/image-host/files?folderId=<id>` | query | 当前目录图片 |
| POST | `/api/image-host/upload` | multipart | 校验扩展名、MIME、签名并上传 |
| DELETE | `/api/image-host/files/<id>` | 无 | 删除单图 |
| POST | `/api/image-host/files/batch-delete` | `{ids:[...]}` | 返回 `{deleted,failed}`，部分失败不回滚已成功项 |
| POST | `/api/image-host/files/batch-move` | `{ids:[...],folderId}` | 返回 `{moved,skipped,failed}` |

## 公共接口

| Method | Path | 说明 |
|---|---|---|
| GET/HEAD | `/public/<token>` | 文件实体；网盘 attachment、图床 inline |
| GET/HEAD | `/public/<token>/<filename>` | 兼容旧链接；路由只以 Token 定位，文件名段不参与查找 |
| GET/HEAD | `/share/<token>` | 文件信息 HTML，下载按钮指向旧兼容公开路径 |
| GET/HEAD | `/share/folder/<token>` | 文件夹 HTML，可用 `?folderId=` 浏览分享根目录的后代 |
| GET/HEAD | `/share/folder/<token>/file/<file-id>/download` | 仅允许分享根目录后代中的 `drive` 文件 |

文件和文件夹分享 HTML 路由对其他 Method 返回 405。`/public/` 当前没有显式 Method gate，支持并依赖的契约仍只有 GET/HEAD；调用方不得依赖其他 Method 的现状。失效或不匹配返回 404。

## DTO

文件 DTO：

```json
{
  "id": "uuid",
  "folderId": "root-or-uuid",
  "name": "file.txt",
  "size": 12,
  "contentType": "text/plain",
  "fileCategory": "drive",
  "sortOrder": 0,
  "downloadCount": 0,
  "downloadBytes": 0,
  "downloadLimitBytes": null,
  "isPublic": true,
  "publicUrl": "https://host/public/token",
  "shareUrl": "https://host/share/token",
  "downloadUrl": "/api/drive/files/uuid/download",
  "updatedAt": 0
}
```

目录 DTO 为 `{id,parentId,name,isPublic,shareUrl,sortOrder,updatedAt}`；图床目录 DTO 为 `{id,parentId,name,folderCategory,imageCount,sortOrder,updatedAt}`。

## 下载状态

- `200`：完整实体或 HEAD。
- `206`：合法单 Range，带 `Content-Range`。
- `403`：本次响应会超过流量限额。
- `416`：Range 语法不支持或超出文件。
- 所有实体响应带 `Accept-Ranges: bytes`；不支持 multipart ranges。
