# 知识库独立 Clone 验收

日期：2026-10-30。

## 范围

从 `https://github.com/torr9522/r2drive.git` 全新 Clone 远程文档分支，验收 commit `d5c2b3e042b3165a5695708b4d5cf4a05abc4daf`。验收目录位于临时路径，不读取原开发工作树、生产数据、SSH 配置、应用隐藏配置或 Codex 会话；只使用仓库文件、系统 Python 和公开 PyPI。

## 结果

- Git 远程和 HEAD 与预期一致，初始 worktree clean。
- 新维护者 15 问全部能由 `docs/README.md` 导航到仓库内答案。
- 45 个知识库 Markdown 文件的本地链接全部可解析。
- `python3 -m venv .venv` 成功。
- `pip install -r requirements.txt` 成功，解析到版本范围内的 `python-multipart`。
- `python -m py_compile app.py` 成功。
- `python -m unittest -v tests/test_app.py` 六组全部通过。
- 测试后 worktree 仍 clean（`.venv` 被忽略）。

浏览器脚本未在本次文档 Clone 验收中重跑，因为它会创建大量数据且本轮没有修改应用代码；v1.8.3 的真实 Chromium 证据保存在 `acceptance-history.md`。

合并后的最终 `main` 又从 GitHub Clone 验证一次：HEAD、链接、编译以及核心应用文件与 `v1.8.3` 零差异均通过。该次 HTTP 套件触发了已记录的下载统计时序问题：第 2 组在服务线程提交计数前立即读取，随后 3 组因依赖前置测试状态而连锁失败。它与同一应用代码在上一轮六组全通过共同证明测试具有非确定时序；该失败保留在 `KNOWN_ISSUES.md`，没有被描述为已修复或通过。

## 独立性结论

仅依靠 GitHub 仓库即可确认项目定位、模块、上传设计、四表 schema、API 扩展入口、分享逻辑、测试命令、Debian 部署、备份恢复、兼容红线、已知问题、补丁发布流程和新功能开发入口。无法恢复的早期 GitHub Release 正文已在开发历史中明确标记，而非推测补写。
