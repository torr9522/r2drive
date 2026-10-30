# 发布流程

## 版本模型

只发布 `vMAJOR.MINOR.PATCH` 正式 annotated tag。没有 RC/Beta/Alpha 通道。历史 Tag 不移动、不覆盖；禁止批量 `git push --tags`。

## 发布前

1. 从最新 `origin/main` 建分支，完成代码、迁移、测试和文档。
2. 更新 `CHANGELOG.md` 和 `docs/CURRENT_BASELINE.md`。
3. 执行 `git diff --check`、Python 编译、HTTP 回归、必要浏览器验收和敏感扫描。
4. 用旧数据库 fixture 验证迁移，制作真实部署备份/回滚方案。
5. 合并后确认远程 main 仍是预期祖先，worktree clean。

## Tag 和 Release

```bash
git fetch origin main --tags
git tag -a vX.Y.Z <verified-commit> -m 'R2 Drive vX.Y.Z'
git push origin refs/heads/main
git push origin refs/tags/vX.Y.Z
git rev-parse 'vX.Y.Z^{}'
```

只在明确授权后创建 GitHub Release，并确认非 draft、非 prerelease、Latest 指向目标。若版本名已存在且目标不同，停止并选择下一个版本，绝不移动旧 Tag。

## 安装选择规则

`install.sh` 无参数时通过远程 Tag 名排序选择最新 `vX.Y.Z`，验证 tag 对象类型为 `tag`，再取 peeled commit 并 detach checkout。文档提交在 Tag 后进入 main 不会被默认安装。

## 部署门禁

- 备份数据库和 storage。
- 固定传入目标版本，不依赖当时最新值。
- 验证服务 commit 等于 `tag^{}`。
- 检查数据库、旧分享、Range、Cookie、上传和服务重启。
- 共享 Caddy 检查其他站点前后状态。

## 生产原地升级

1. 只读确认服务器身份、当前 commit/Tag、数据路径、Caddy 证书指纹和其他服务。
2. 停止 `r2-drive`，保持 Caddy 和其他服务运行；备份源码、SQLite、storage、systemd 和 R2 站点片段。
3. 对备份数据库副本用新代码执行迁移预演，比较 ID、Token、路径、统计、限额和 integrity check。
4. 从独立准备目录校验 `tag^{}`，停服务后原子切换代码；不运行全新安装或重建 Caddy。
5. 启动后检查登录、数据总量、旧分享、Range、新功能、服务重启和其他服务。
6. 验收后保留受限的升级前备份，不自动删除生产回滚点。

## 回滚

保留部署前应用数据备份和旧站点/服务片段。应用失败可恢复旧 Tag，但若新版本已经写入旧程序不理解的数据语义，应恢复成套数据库和 storage 备份。不得只回滚源码后继续写生产数据。

## v1.9.0 发布记录

- 发布时间：2026-10-30
- 应用 commit / `v1.9.0^{}`：`63e0c7ebaedcab0730e1b7faf53297dbb9dfa4b7`
- Release：`https://github.com/torr9522/r2drive/releases/tag/v1.9.0`
- 最终候选在 Debian 12 测试机完成 HTTP/SQLite 和两套 Chromium 验收后才创建 Tag
- 生产先制作一致性回滚备份并对副本预演迁移，再复用现有虚拟环境原地切换；未运行 `install.sh`
- 正式迁移、原凭据登录、原分享、证书指纹、数据/实体摘要、功能和服务重启均通过
- Tag 后的生产交接文档提交只进入 `main`，不得移动 `v1.9.0`
