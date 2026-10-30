# 开发指南

## 从零启动

```bash
git clone https://github.com/torr9522/r2drive.git
cd r2drive
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
R2_DRIVE_DATA=/tmp/r2-drive-dev \
R2_DRIVE_HOST=127.0.0.1 \
R2_DRIVE_PORT=8090 \
.venv/bin/python app.py
```

浏览器打开 `http://127.0.0.1:8090/` 并创建临时管理员。开发目录与数据目录分离；停止服务后可删除临时数据。

环境变量：

| 名称 | 默认 | 作用 |
|---|---|---|
| `R2_DRIVE_DATA` | `/opt/r2-drive/data` | SQLite 和 storage 根目录 |
| `R2_DRIVE_SITE_NAME` | `R2 Drive` | 页面名称 |
| `R2_DRIVE_HOST` | `127.0.0.1` | 监听地址 |
| `R2_DRIVE_PORT` | `8090` | 监听端口 |
| `R2_DRIVE_MAX_UPLOAD_BYTES` | 10 GiB | 请求 Content-Length 上限 |

## 代码定位

- 前端函数位于 `INDEX_HTML` 的 script 中。
- `Handler.route()` / `api()` 是路由入口。
- 每个业务操作是 `Handler` 方法。
- `init_db()` 是 schema 和迁移唯一入口。
- DTO、Range、名称、图片签名和哈希是模块级 helper。

新增 API 时：先定义方法/路径和认证边界，在 `api()` 中按更具体路径优先注册，实现中同时约束 `user_id` 与分类，使用参数化 SQL，返回现有 DTO 或文档化新 DTO，并添加成功、非法输入、越权和兼容测试。

修改分享逻辑时从 `public_file()`、`share_page()`、`folder_share_route()`、`file_dto()` / `folder_dto()` 开始，同时阅读 `SHARING.md` 和 ADR-0009。

## 修改原则

- 先复现，再修复；测试数据使用临时目录。
- 上传前端保持任务和视图解耦。
- 数据变更只做幂等增量迁移。
- 不为单一修复引入构建链或框架。
- 不直接对生产地址运行浏览器验收脚本，它会创建测试数据且当前不会自动清理。

测试和提交流程见 [TESTING.md](TESTING.md) 与根目录 `CONTRIBUTING.md`。

## 部署归档

项目没有编译产物。需要离线源码包时，从已验证 Tag 创建可重复归档：

```bash
git archive --format=tar.gz --output=r2-drive-v1.8.3.tar.gz 'v1.8.3^{}'
sha256sum r2-drive-v1.8.3.tar.gz
```

正式一键安装仍通过 Git Tag checkout，而不是使用本地未提交目录。
