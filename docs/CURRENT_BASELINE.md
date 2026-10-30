# 当前交接基线

更新时间：2026-10-30。

## 版本身份

- 仓库：`https://github.com/torr9522/r2drive`
- 当前正式版本：`v1.9.0`，2026-10-30 发布
- APPLICATION_BASELINE：`63e0c7ebaedcab0730e1b7faf53297dbb9dfa4b7`
- `v1.9.0^{}`：`63e0c7ebaedcab0730e1b7faf53297dbb9dfa4b7`
- GitHub Release：`https://github.com/torr9522/r2drive/releases/tag/v1.9.0`，正式、非 prerelease、Latest
- 上一正式版本：`v1.8.3`，annotated tag 保持不变
- PREVIOUS_APPLICATION_BASELINE：`a321eb47cf9a5686285d3e78ea4c47c262224073`
- `v1.8.3^{}`：`a321eb47cf9a5686285d3e78ea4c47c262224073`
- 已验收的文件管理应用 commit：`e8ada2c99787838ad7d19b443ba3cb53e26d9942`
- 实机分享/Range 验收测试 commit：`ac37c8a`
- 发布准备及最终测试 commit：`63e0c7ebaedcab0730e1b7faf53297dbb9dfa4b7`
- Tag 后的知识库提交属于文档基线，不改变应用 Tag 或默认安装内容

知识库主体首次归档 commit 为 `d5c2b3e042b3165a5695708b4d5cf4a05abc4daf`。其后的独立 Clone 验收记录也属于知识库提交；未来维护者应以本文件所在的最新 `main` HEAD 作为知识库基线，以 `APPLICATION_BASELINE` 作为当前应用基线。

## 当前结构

```text
app.py                     前端、路由、业务逻辑、迁移和服务入口
vendor/sortablejs/         SortableJS 1.15.7 及 MIT LICENSE
requirements.txt           python-multipart 版本范围
install.sh                 Debian 安装和正式 Tag 选择
deploy/r2-drive.service    systemd 模板
deploy/Caddyfile           示例站点配置，不应直接覆盖共享 Caddyfile
tests/test_app.py           隔离 HTTP/数据库回归
tests/browser_acceptance.mjs Chromium/移动视口验收
tests/file_management_acceptance.mjs 排序、移动、分享和 Range 实机验收
docs/                      项目知识库
```

## 数据结构基线

SQLite 没有独立 schema 版本表。当前结构由 `init_db()` 创建并用 `ensure_column()` 增量补列：`users`、`sessions`、`folders`、`files`。`folders` 和 `files` 均有 `sort_order`，按用户、分类和父目录隔离。旧库初始化保持 v1.8.3 的目录名称顺序和文件更新时间顺序，不改 ID、Token、路径或统计。

## 当前正式功能

- 文件夹始终在文件之上，两组分别保存手动顺序。
- 桌面使用本地 SortableJS 手柄；移动端使用上移/下移。
- 网盘和图床共用多级目标选择器、混合批量移动和冲突策略。
- 移动只改 SQLite 逻辑关系，保留实体、ID、Token、统计和限额。
- 排序请求串行，拖拽后立即操作不会读旧列表状态。

## 已验证状态

2026-10-30 对 `v1.8.3` 完成：

- 6 组隔离 HTTP/SQLite 回归在开发和独立测试环境通过
- Chromium 桌面验收：上传滚动 710px 保持、搜索焦点保持、shell 节点未替换
- 队列切换目录后仍写入入队时目录；失败项不阻断后续项
- 图床预览、复制、选择、删除和失败后继续队列通过
- 375/390/430px 无横向溢出，移动 Modal 滚动保持
- HEAD、Range 206/416、流量限制、统计和旧分享路径通过
- 旧 SQLite 增量迁移保留旧行通过
- HTTPS Cookie 的 `Secure`、`HttpOnly`、`SameSite=Lax` 通过
- 正式生产运行于 Debian 12，公开入口为 `https://wp.68362596.xyz/`

2026-10-30 对文件管理候选完成：

- 开发机和重装后 Debian 12 测试机的 9/9 HTTP/SQLite 回归通过
- 桌面文件夹/文件拖排、快速连续排序和移动持久化通过
- 单文件、混合文件/文件夹批量移动、自动重命名和循环防护通过
- 图床图片/文件夹移动、预览与复制回归通过
- 移动前后文件/文件夹分享 URL 不变，HEAD 200、Range 206/416 通过
- 375/390/430px 无横向溢出，页面 JavaScript 错误 0
- 原上传验收重跑：滚动 710px、搜索焦点、`.shell` 节点和入队目标均保持
- 服务重启前后 89 个目录、48 条文件记录和 48 个实体的联合摘要一致，SQLite `integrity_check=ok`
- 测试部署最终 commit 为 `63e0c7ebaedcab0730e1b7faf53297dbb9dfa4b7`，Debian 12、R2 Drive 和 Caddy 均正常

2026-10-30 正式发布和生产升级完成：

- GitHub `main` 快进到 `63e0c7e`，创建 annotated tag `v1.9.0` 和 Latest Release；`v1.8.3` 未移动
- 生产 Debian 12 从 `v1.8.3` / `a321eb4` 原地切换到 `v1.9.0` / `63e0c7e`，未运行安装脚本或重建系统
- 升级前一致性备份保留在生产机 `/root/r2-drive-backups/pre-v1.9.0-20261030T100541Z`，权限 `700`
- 生产数据库副本迁移预演与正式迁移均通过；原用户、Session、文件/文件夹 ID、`storage_path`、分享 Token、实体内容和限额保持
- 原管理员账号和密码完成真实 Chromium 登录；Cookie 仍为 `Secure`、`HttpOnly`、`SameSite=Lax`
- 生产临时目录内完成排序、单项/混合批量移动、冲突、循环拒绝、图床、分享、375/390/430px 和服务重启验收，随后按创建 ID 清理
- 旧分享四类路径 HEAD 200，Range 206/416；验收读取使既有累计流量按设计增加 1 字节，未增加完整下载次数
- SQLite `integrity_check=ok`，数据库与实体引用差异为 0；验收清理后业务记录和实体数量/容量回到升级前基线
- HTTPS 证书 SHA256 指纹前后均为 `E3:84:70:D1:E7:C4:66:88:37:5D:54:62:0D:D8:08:BA:3E:32:24:04:48:43:76:93:B1:54:A2:61:F9:C4:80:20`
- `r2-drive`、Caddy、x-ui 均为 active，Caddy/ACME 文件和其他监听端口未改动

生产凭据、SSH 信息、数据库、证书私钥和真实文件不属于仓库知识库。

## 已知问题和未完成项

- 下载统计隔离测试在较慢调度环境可能在服务端 `finally` 提交前立即读取，产生时序敏感失败；真实 HTTPS 轮询验收确认最终正确落库。尚未修复测试。
- 未做 Firefox、Safari、高并发、压力、长期运行和故障注入测试。
- `app.py` 仍是大型单文件；目前没有足够收益支持框架迁移。
- 无 CI workflow；测试由维护者显式运行。
- 无 schema 版本表、外键约束和自动备份器。
- 未对接近 5000 项的单目录排序做性能测试；不支持复制、覆盖或文件夹合并。

## 从这里继续开发

1. 从最新 `origin/main` 新建工作分支。
2. 阅读 `AGENTS.md`、相关 ADR、兼容性和测试文档。
3. 使用独立临时数据目录启动，不复制生产数据。
4. 先添加能复现问题的回归，再修改实现。
5. 更新对应文档和本文件的测试/已知问题部分。
6. 普通提交不得创建正式 Tag 或部署生产。

`v1.9.0` 已发布并运行于生产。后续优先消除下载统计测试的时序假设；若要拆分 `app.py`，先写 ADR 并保持无构建链和旧 API 兼容。任何后续生产部署仍需重新取得明确授权。
