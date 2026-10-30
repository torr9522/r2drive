# 当前交接基线

更新时间：2026-10-30。

## 版本身份

- 仓库：`https://github.com/torr9522/r2drive`
- 当前正式版本：`v1.9.1`，2026-10-30 发布
- APPLICATION_BASELINE：`8a9ecd1902677e96982c2b56a88d7e45b34d94d7`
- `v1.9.1^{}`：`8a9ecd1902677e96982c2b56a88d7e45b34d94d7`
- GitHub Release：`https://github.com/torr9522/r2drive/releases/tag/v1.9.1`，正式、非 prerelease、Latest
- 上一正式版本：`v1.9.0`
- PREVIOUS_APPLICATION_BASELINE：`63e0c7ebaedcab0730e1b7faf53297dbb9dfa4b7`
- `v1.9.0^{}`：`63e0c7ebaedcab0730e1b7faf53297dbb9dfa4b7`
- `v1.8.3^{}` 仍为 `a321eb47cf9a5686285d3e78ea4c47c262224073`
- 已验收的文件管理应用 commit：`e8ada2c99787838ad7d19b443ba3cb53e26d9942`
- 实机分享/Range 验收测试 commit：`ac37c8a`
- v1.9.0 发布准备及最终测试 commit：`63e0c7ebaedcab0730e1b7faf53297dbb9dfa4b7`
- v1.9.1 修复实测 commit：`8792d0577501acc81ba67c2dfc11ff77b792c012`
- v1.9.1 发布准备及最终测试 commit：`8a9ecd1902677e96982c2b56a88d7e45b34d94d7`
- Tag 后的知识库提交属于文档基线，不改变应用 Tag 或默认安装内容
- `v1.9.1` annotated tag 已固定到测试机复验通过的最终发布准备 commit；后续文档提交不得移动该 Tag

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
tests/ui_regression_acceptance.mjs 空状态、桌面/移动分享和分享页专项验收
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

2026-10-30 对 `v1.9.1` 界面修复完成验证和正式发布：

- 根因是 `.empty { display:grid }`、`.row { display:grid }` 等作者样式覆盖浏览器内置 `[hidden] { display:none }`，数据加载和 API 数量判断本身没有丢失记录
- 恢复全局 `[hidden]` 语义，并将目录空状态与搜索无结果状态分开计算；局部刷新后重新基于当前 DOM 项目数和查询匹配数更新
- 网盘移动端文件/文件夹行增加“更多操作”Action Sheet；桌面原按钮和路由未重写
- 文件夹分享页增加独立下载按钮并修复窄屏 content-box 溢出；单文件分享页未修改
- 9/9 HTTP/SQLite、原上传 Chromium、文件管理 Chromium 和专项 Chromium 验收通过；专项覆盖 375/390/430px，页面错误 0
- Debian 12 测试机 `45.77.169.189` 部署并实测 `8792d0577501acc81ba67c2dfc11ff77b792c012`：HTTPS、`r2-drive`、Caddy、9/9 回归和三组 Chromium 验收均通过
- 发布候选进一步通过 Playwright WebKit 的空状态、分享页及 375/390/430px 专项验收；iPhone Safari 无真机条件，真机剪贴板授权行为仍列为未验证
- 最终 commit `8a9ecd1902677e96982c2b56a88d7e45b34d94d7` 在测试机通过 9/9 HTTP/SQLite、Chromium 界面/上传/文件管理和 WebKit 界面回归后，创建 annotated tag `v1.9.1` 与 GitHub Latest Release
- 生产从 `v1.9.0` 原地切换至 `v1.9.1`，未改变数据库 schema、requirements、systemd 或 Caddy 配置；`r2-drive`、Caddy、x-ui 均保持 active
- 新回滚点 `/root/r2-drive-backups/pre-v1.9.1-20261030T121906Z` 约 779 MiB，包含 SQLite Backup API 快照、原始 WAL/SHM、完整 storage、源码、虚拟环境及服务配置；旧 `pre-v1.9.0` 回滚点保持不变
- 升级前后用户、文件夹、文件、分享、统计/限额、实体数量和实体容量保持；所有原 Session ID 保留，验收登录新增 Session；SQLite `integrity_check=ok`
- 生产验收覆盖原凭据登录、Cookie 属性、空状态、移动分享、文件夹/单文件分享、排序、混合移动、循环拒绝、上传、图床、HEAD、Range 206/416 和服务重启；临时数据已按 ID 清理
- HTTPS 证书 SHA256 指纹仍为 `E3:84:70:D1:E7:C4:66:88:37:5D:54:62:0D:D8:08:BA:3E:32:24:04:48:43:76:93:B1:54:A2:61:F9:C4:80:20`；ACME/Caddy 文件摘要、Caddy PID、x-ui PID 和监听端口未改变

生产凭据、SSH 信息、数据库、证书私钥和真实文件不属于仓库知识库。

## 已知问题和未完成项

- 下载统计隔离测试在较慢调度环境可能在服务端 `finally` 提交前立即读取，产生时序敏感失败；真实 HTTPS 轮询验收确认最终正确落库。尚未修复测试。
- 未做 Firefox、真实 Safari、高并发、压力、长期运行和故障注入测试；Playwright WebKit 专项已通过。
- `v1.9.1` 已发布并部署生产；iPhone Safari 分享剪贴板仍未真机验证。
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

`v1.9.1` 已发布并运行于生产。后续优先消除下载统计测试的时序假设；若要拆分 `app.py`，先写 ADR 并保持无构建链和旧 API 兼容。任何后续生产部署仍需重新取得明确授权。
