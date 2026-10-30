# 当前交接基线

更新时间：2026-10-30。

## 版本身份

- 仓库：`https://github.com/torr9522/r2drive`
- 应用正式发布目标：`v1.9.0`
- 上一正式版本：`v1.8.3`，annotated tag
- PREVIOUS_APPLICATION_BASELINE：`a321eb47cf9a5686285d3e78ea4c47c262224073`
- `v1.8.3^{}`：`a321eb47cf9a5686285d3e78ea4c47c262224073`
- 发布准备提交将在最终测试后创建 `v1.9.0` annotated tag
- 已验收的文件管理应用 commit：`e8ada2c99787838ad7d19b443ba3cb53e26d9942`
- 实机分享/Range 验收测试 commit：`ac37c8a`
- 发布准备分支：`codex/release-v1.9.0`
- 本次提交不提前声称生产已升级；生产验收将在 Tag/Release 之后追加记录

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

## 当前功能候选

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
- 测试部署 commit 在应用验收时为 `e8ada2c99787838ad7d19b443ba3cb53e26d9942`；后续只增加测试和文档
- 本轮未连接或修改生产服务器/域名

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

`v1.9.0` 发布和生产升级已获授权。后续优先消除下载统计测试的时序假设；若要拆分 `app.py`，先写 ADR 并保持无构建链和旧 API 兼容。
