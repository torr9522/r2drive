# SQLite 数据库

数据库默认位于 `${R2_DRIVE_DATA:-/opt/r2-drive/data}/drive.sqlite3`。启动时 `init_db()` 创建表、索引并执行幂等补列。没有 schema 版本表，也没有 SQL `FOREIGN KEY`；下列关联由应用逻辑保证。

## users

| 字段 | 类型/约束 | 含义 |
|---|---|---|
| id | TEXT PRIMARY KEY | UUID，其他表逻辑引用 |
| username | TEXT NOT NULL UNIQUE | 登录名 |
| password_hash | TEXT NOT NULL | PBKDF2-SHA256 hex |
| salt | TEXT NOT NULL | 每用户随机 hex salt |
| role | TEXT NOT NULL DEFAULT admin | 当前只使用 admin |
| disabled | INTEGER NOT NULL DEFAULT 0 | 禁用标记 |
| created_at | INTEGER NOT NULL | Unix 秒 |

## sessions

| 字段 | 类型/约束 | 含义 |
|---|---|---|
| id | TEXT PRIMARY KEY | Session 行 UUID |
| user_id | TEXT NOT NULL | 逻辑关联 users.id |
| token_hash | TEXT NOT NULL UNIQUE | Cookie Token 的 SHA-256 |
| expires_at | INTEGER NOT NULL | 过期 Unix 秒 |
| created_at | INTEGER NOT NULL | 创建 Unix 秒 |

## folders

| 字段 | 类型/约束 | 含义 |
|---|---|---|
| id | TEXT PRIMARY KEY | 持久目录 ID |
| user_id | TEXT NOT NULL | 所有者 |
| parent_id | TEXT NOT NULL DEFAULT root | 父 ID；`root` 为虚拟根 |
| name | TEXT NOT NULL | 显示名 |
| share_token | TEXT UNIQUE | 网盘目录公开 Token；null 为私密 |
| folder_category | TEXT NOT NULL DEFAULT drive | `drive` 或 `image_host` |
| created_at / updated_at | INTEGER NOT NULL | Unix 秒 |

索引：`idx_folders_user_parent(user_id,parent_id)`、部分唯一 `idx_folders_share(share_token IS NOT NULL)`、`idx_folders_user_category(user_id,folder_category,parent_id)`。

## files

| 字段 | 类型/约束 | 含义 |
|---|---|---|
| id | TEXT PRIMARY KEY | 持久文件 ID，同时进入磁盘名 |
| user_id | TEXT NOT NULL | 所有者 |
| folder_id | TEXT NOT NULL DEFAULT root | 逻辑父目录 |
| name | TEXT NOT NULL | 原显示名 |
| storage_path | TEXT NOT NULL | 文件实体绝对路径 |
| size | INTEGER NOT NULL | byte |
| content_type | TEXT NOT NULL | 下载 Content-Type |
| download_count | INTEGER NOT NULL DEFAULT 0 | 完整 GET 次数 |
| download_bytes | INTEGER NOT NULL DEFAULT 0 | 实际写出累计 byte |
| download_limit_bytes | INTEGER DEFAULT NULL | null 为不限 |
| is_public | INTEGER NOT NULL DEFAULT 0 | 文件公开标记 |
| share_token | TEXT UNIQUE | 公开 Token |
| file_category | TEXT NOT NULL DEFAULT drive | `drive` 或 `image_host` |
| created_at / updated_at | INTEGER NOT NULL | Unix 秒 |

索引：`idx_files_user_folder(user_id,folder_id)`、`idx_files_share(share_token)`、`idx_files_user_category(user_id,file_category,updated_at)`。

## 迁移

`ensure_column()` 通过 `PRAGMA table_info` 检查并 `ALTER TABLE ADD COLUMN`。当前能为旧目录补 `share_token`、`folder_category`，为旧文件补下载统计、限额和 `file_category`。分类默认 `drive`，因此 v1.7 旧数据不会进入图床。

迁移不会重写 ID、Token、路径或统计，也不搬动文件。新增 NOT NULL 字段必须有兼容默认值并增加旧库测试。不要通过删除数据库“升级”。

## 生命周期

- 初始化只允许第一名 admin。
- Session 在登录/初始化创建，登出或过期清理删除。
- 上传成功后创建 files 行；失败时不留行并清理实体。
- 删除文件清实体和行；缺失实体不阻止清记录。
- 删除目录要求没有子目录和同分类文件。
- 公开切换会生成或清除 Token；再次公开是新 Token。

数据库和 `storage/` 必须作为一个一致性单元备份。详见 [BACKUP_RESTORE.md](BACKUP_RESTORE.md)。
