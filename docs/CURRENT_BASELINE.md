# 当前交接基线

更新时间：2026-10-30。

## 版本身份

- 仓库：`https://github.com/torr9522/r2drive`
- 应用正式版本：`v1.8.3`
- 应用正式 Tag：`v1.8.3`，annotated tag
- APPLICATION_BASELINE：`a321eb47cf9a5686285d3e78ea4c47c262224073`
- `v1.8.3^{}`：`a321eb47cf9a5686285d3e78ea4c47c262224073`
- Latest Release：`https://github.com/torr9522/r2drive/releases/tag/v1.8.3`
- `main` 在应用 Tag 后可包含知识库提交；这不改变安装基线

本次知识库提交的 commit 在提交完成前未知。未来维护者应以本文件所在的 `main` HEAD 作为知识库基线，以 `APPLICATION_BASELINE` 作为当前应用基线。

## 当前结构

```text
app.py                     前端、路由、业务逻辑、迁移和服务入口
requirements.txt           python-multipart 版本范围
install.sh                 Debian 安装和正式 Tag 选择
deploy/r2-drive.service    systemd 模板
deploy/Caddyfile           示例站点配置，不应直接覆盖共享 Caddyfile
tests/test_app.py           隔离 HTTP/数据库回归
tests/browser_acceptance.mjs Chromium/移动视口验收
docs/                      项目知识库
```

## 数据结构基线

SQLite 没有独立 schema 版本表。当前结构由 `init_db()` 创建并用 `ensure_column()` 增量补列：`users`、`sessions`、`folders`、`files`。当前迁移兼容旧库缺少 `share_token`、分类和下载统计字段的情况，旧行的分类默认值为 `drive`。

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

生产凭据、SSH 信息、数据库、证书私钥和真实文件不属于仓库知识库。

## 已知问题和未完成项

- 下载统计隔离测试在较慢调度环境可能在服务端 `finally` 提交前立即读取，产生时序敏感失败；真实 HTTPS 轮询验收确认最终正确落库。尚未修复测试。
- 未做 Firefox、Safari、高并发、压力、长期运行和故障注入测试。
- `app.py` 仍是大型单文件；目前没有足够收益支持框架迁移。
- 无 CI workflow；测试由维护者显式运行。
- 无 schema 版本表、外键约束和自动备份器。

## 从这里继续开发

1. 从最新 `origin/main` 新建工作分支。
2. 阅读 `AGENTS.md`、相关 ADR、兼容性和测试文档。
3. 使用独立临时数据目录启动，不复制生产数据。
4. 先添加能复现问题的回归，再修改实现。
5. 更新对应文档和本文件的测试/已知问题部分。
6. 普通提交不得创建正式 Tag 或部署生产。

下一优先建议是消除下载统计测试的时序假设；若要拆分 `app.py`，先写 ADR 并保持无构建链和旧 API 兼容。
