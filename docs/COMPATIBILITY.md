# 兼容性契约

## 必须保持

- `/public/<token>`
- `/public/<token>/<filename>`
- `/share/<token>`
- `/share/folder/<token>` 及其后代浏览/文件下载
- 文件、目录和用户 ID
- 有效分享 Token（除非用户主动设私密或删除）
- `storage_path` 与实体对应关系
- 下载次数、字节和限额语义
- HEAD、单 Range 206、非法 Range 416
- 旧数据库增量迁移，旧行默认 `drive`
- 网盘/图床分类隔离

## 当前平台

- 安装脚本声明 Debian 11+。
- Python 最低实践基线为 3.9；v1.8.3 已在 Python 3.11 实测。
- 移除 `cgi` 后按依赖声明面向 Python 3.13 兼容，但未在 3.13 实机验收。
- 浏览器实测为 Chromium；Firefox/Safari 未验证。

## 变更方法

新增字段使用有默认值的幂等 `ensure_column()`，先备份并用旧 schema fixture 回归。不能删除/改名字段后要求用户重建数据库。API 如需新语义，应新增可选字段或新路径，旧客户端和分享链接继续工作。

代码回滚不等于数据回滚：旧版本可能不知道新字段但通常可忽略；若新版本改变了必需数据语义，必须先写双向兼容或明确恢复数据库备份。
