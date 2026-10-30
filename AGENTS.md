# AGENTS.md

本文件是 Codex 和其他自动化开发代理进入 R2 Drive 仓库后的首要工作规范。

## 当前基线

- 项目：R2 Drive Personal Edition
- GitHub：`torr9522/r2drive`
- 当前应用正式版本：`v1.8.3`
- 正式 Tag：`v1.8.3`（annotated tag）
- 应用正式 commit：`a321eb47cf9a5686285d3e78ea4c47c262224073`
- `main` 允许包含正式 Tag 之后的文档提交；安装脚本按正式 Tag 安装

## 开始工作前

按顺序完整阅读：

1. `README.md`
2. `AGENTS.md`
3. `docs/README.md`
4. `docs/CURRENT_BASELINE.md`
5. 与任务相关的架构、ADR、测试和兼容性文档

以当前源码为最终事实。用户描述、旧文档和历史提交只能解释背景，不能覆盖当前实现。修改前先通过 `rg`、Git 历史和测试理解调用链；涉及外部依赖时核对官方文档、许可证和当前维护状态。

## 不可破坏的契约

- 不得无迁移方案地删除或重建 SQLite 数据。
- 保持旧文件/文件夹 ID、`storage_path`、分享 Token、下载统计和流量限制。
- 保持 `/public/<token>`、`/public/<token>/<filename>`、`/share/<token>`、`/share/folder/<token>`。
- 网盘与图床必须继续按 `drive` / `image_host` 分类隔离。
- 上传任务必须独立于页面生命周期，目标目录在入队时冻结。
- 上传进度、Toast 或搜索输入不得触发整页 `render()`；避免恢复滚动跳动、焦点丢失和任务状态丢失。
- 不引入框架或大型上传组件，除非收益、迁移成本和长期维护责任已经形成新的 ADR。

## Codex 工作规范

1. 研究现有实现，不凭单一问题描述直接改代码。
2. 优先复用成熟实现，但不得复制许可证不兼容的代码。
3. 保持修改范围与需求一致，不顺手重构无关代码。
4. 数据库变更必须增量、幂等，并添加旧库迁移测试。
5. API 或分享行为变更必须先更新兼容性评估。
6. 前端修改必须检查上传、搜索、焦点、滚动、Modal、Toast 和移动视口。
7. 修改后执行与风险相称的 HTTP 和浏览器测试。
8. 同步更新相关文档、开发历史和 `docs/CURRENT_BASELINE.md`。
9. 每个 commit 保持单一目的、可回退、说明真实。
10. 不擅自部署生产环境、删除生产数据、发布 Tag 或 Release。
11. 不操作其他 GitHub 仓库、服务器或域名。
12. 不向 Git 提交密码、Token、Cookie、私钥、生产数据库、真实用户文件或生产日志。

## 新功能流程

```text
需求分析
  -> 阅读当前基线、兼容性和历史 ADR
  -> 研究成熟方案及许可证
  -> 写清方案、数据/API影响和回滚方式
  -> 实施最小修改
  -> HTTP/浏览器/迁移测试
  -> 更新文档和 CURRENT_BASELINE
  -> Git commit
  -> 交接记录
```

## 最低验证

```bash
git diff --check
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m py_compile app.py
.venv/bin/python -m unittest -v tests/test_app.py
```

前端、上传或移动端变更还需运行 `tests/browser_acceptance.mjs`；具体环境见 `docs/TESTING.md`。下载统计测试存在已记录的时序敏感性，不能通过删除断言掩盖，见 `docs/KNOWN_ISSUES.md`。

## 发布规则

- 正式版本只使用 `vX.Y.Z` annotated tag。
- 禁止移动、覆盖历史 Tag，禁止 `git push --tags`。
- 发布前确认 worktree clean、远程 `main` 未漂移、迁移和回归通过。
- 安装脚本必须明确解析到目标 Tag 的 peeled commit。
- 推送使用普通 fast-forward；禁止 force push。
- Release 仅在用户明确授权后创建，并记录实际测试和剩余风险。
- 数据库升级前备份 SQLite 与 `storage/`，部署后验证旧链接、Range、统计和服务重启。
- 回滚代码不能回滚数据库结构；先核对目标旧版本能否读取当前 schema。

完整流程见 `docs/RELEASE_PROCESS.md`。
