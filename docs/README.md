# R2 Drive 项目知识库

本目录以 `v1.8.3` 正式源码、当前文件管理升级候选和可访问 Git 历史为事实来源。新开发者只需 Clone 仓库即可重建开发环境、理解设计并继续维护。

## 首次阅读路径

1. [项目概况](PROJECT_OVERVIEW.md)
2. [当前基线](CURRENT_BASELINE.md)
3. [架构](ARCHITECTURE.md)
4. [功能规则](FEATURES.md)
5. [开发指南](DEVELOPMENT_GUIDE.md)
6. [测试](TESTING.md)
7. [兼容性](COMPATIBILITY.md)

## 设计和实现

- [API 参考](API_REFERENCE.md)
- [数据库](DATABASE.md)
- [文件存储](STORAGE.md)
- [上传流水线](UPLOAD_PIPELINE.md)
- [分享和下载](SHARING.md)
- [安全模型](SECURITY.md)
- [前端架构](architecture/frontend.md)
- [后端架构](architecture/backend.md)
- [认证架构](architecture/authentication.md)

## 开发和交付

- [部署](DEPLOYMENT.md)、[运维](OPERATIONS.md)、[备份恢复](BACKUP_RESTORE.md)
- [测试](TESTING.md)、[发布流程](RELEASE_PROCESS.md)、[已知问题](KNOWN_ISSUES.md)
- [开发历史](DEVELOPMENT_HISTORY.md)、[技术决策](TECHNICAL_DECISIONS.md)
- [文件管理升级开发记录](history/file-management-upgrade.md)
- [验收历史](testing/acceptance-history.md)、[回归用例](testing/regression-cases.md)
- [知识库独立 Clone 验收](testing/knowledge-base-acceptance.md)

## 新维护者 15 问导航

| 问题 | 答案位置 |
|---|---|
| 项目是什么、如何启动 | `PROJECT_OVERVIEW.md`、根 `README.md` |
| 模块如何组成 | `ARCHITECTURE.md`、`architecture/` |
| 上传如何工作、为何这样设计 | `UPLOAD_PIPELINE.md`、ADR-0006/0007/0008 |
| 数据库有哪些表 | `DATABASE.md` |
| 如何新增 API | `DEVELOPMENT_GUIDE.md`、`API_REFERENCE.md` |
| 如何修改分享 | `SHARING.md`、ADR-0009 |
| 如何跑完整测试 | `TESTING.md`、`testing/regression-cases.md` |
| 如何部署 Debian | `DEPLOYMENT.md` |
| 如何备份恢复 | `BACKUP_RESTORE.md` |
| 哪些接口不能破坏 | `COMPATIBILITY.md` |
| 当前已知问题 | `KNOWN_ISSUES.md` |
| 如何发布补丁 | `RELEASE_PROCESS.md` |
| 新功能从哪里开始 | `AGENTS.md`、`DEVELOPMENT_GUIDE.md` |
| 当前正式和文档基线 | `CURRENT_BASELINE.md` |
| 为什么采用当前技术 | `TECHNICAL_DECISIONS.md`、`decisions/` |

## 事实等级

- **当前事实**：由 `v1.8.3` 源码、测试或部署模板直接确认。
- **历史事实**：由 Git commit、Tag、历史文件或可访问 Release 元数据确认。
- **验收记录**：由 2026-10-30 审计和部署过程实际输出确认，已去除凭据和真实数据。
- **未恢复**：仓库或 GitHub 不再提供原始资料；文档会明确标注，不用推测补齐。
