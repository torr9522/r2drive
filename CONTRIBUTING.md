# Contributing

R2 Drive 追求小而稳定。贡献应优先保持数据和链接兼容，避免为了技术更新扩大维护面。

## 开发环境

```bash
git clone https://github.com/torr9522/r2drive.git
cd r2drive
git switch -c work/<topic>
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
R2_DRIVE_DATA=/tmp/r2-drive-dev .venv/bin/python app.py
```

不要使用生产数据库或真实用户文件开发。首次打开本地地址后，用临时凭据初始化。

## 提交要求

- 一个 commit 处理一个目的，提交信息使用 `type: summary`。
- 应用修改必须附测试；迁移修改必须附旧 schema 回归。
- 更新相关文档和 `docs/CURRENT_BASELINE.md`。
- 不提交运行数据、密钥、凭据、浏览器产物或依赖目录。
- 不改变旧接口和数据语义，除非提交中包含兼容迁移及回滚方案。

提交前至少运行：

```bash
git diff --check
.venv/bin/python -m py_compile app.py
.venv/bin/python -m unittest -v tests/test_app.py
```

涉及界面或上传时按 `docs/TESTING.md` 运行浏览器验收。

## 评审清单

- 行为是否与 `docs/FEATURES.md` 一致？
- API、数据库、存储或分享路径是否变化？
- 网盘/图床分类隔离是否仍成立？
- 异常是否会留下孤立文件或假成功？
- 上传时是否仍能滚动、搜索和切页？
- 移动端 375/390/430px 是否无横向溢出？
- 安装、升级和回滚文档是否仍真实？

安全报告不要在公开 Issue 中包含凭据、Token 或生产数据。先以私密渠道联系仓库所有者。
