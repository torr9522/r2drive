# 文件存储

默认结构：

```text
/opt/r2-drive/data/
├── drive.sqlite3
├── drive.sqlite3-wal   # 运行时可能存在
├── drive.sqlite3-shm   # 运行时可能存在
└── storage/
    └── <user-id>/
        └── <file-id>-<sanitized-name>
```

显示名保存在数据库。磁盘名使用 UUID 和 `safe_name()`：只保留 ASCII 字母数字、点、下划线、括号和连字符，其余替换为下划线并截断到 120 字符。业务重命名只更新 `files.name`，不改 `storage_path`。图床移动也只更新 `folder_id`。

## 一致性

正常上传顺序是写唯一新文件、校验、插入数据库；异常删除新文件。删除顺序是删除实体（缺失可容忍）后删行。系统没有后台孤儿扫描、回收站、内容去重或校验和。

不要手工重命名存储实体或单独复制数据库。恢复必须保持数据库中每个 `storage_path` 与实际部署路径一致；从不同安装目录恢复时需有明确路径迁移工具，目前仓库未提供。

## 权限

生产模板使用 `r2-drive:r2-drive`、数据目录 0750、systemd `UMask=0077`。源码可读，只有数据目录允许服务写入。备份应为 root 可读且不放在 Web 根目录。
