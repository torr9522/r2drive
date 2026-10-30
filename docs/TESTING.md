# 测试

## HTTP/数据库回归

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest -v tests/test_app.py
```

测试在临时目录启动端口 18090 的独立应用，生成随机密码，覆盖认证、上传、目录、Range、统计/限额、公开/私密、删除、图床、分类隔离、旧 schema 迁移、分组排序和通用移动。不要让其他进程占用 18090。

## 浏览器验收

脚本需要 Node.js、Chromium 和 `playwright-core`。仓库没有锁定 Node 依赖；为避免污染仓库，可安装到临时目录：

```bash
pw_dir=$(mktemp -d)
npm install --prefix "$pw_dir" playwright-core
R2_PLAYWRIGHT_PATH="$pw_dir/node_modules/playwright-core" \
R2_CHROMIUM=/usr/bin/chromium \
R2_TEST_URL=http://127.0.0.1:8090 \
R2_TEST_USERNAME=<temporary-admin> \
R2_TEST_PASSWORD=<temporary-password> \
node tests/browser_acceptance.mjs
```

脚本会创建多个目录和数十 MiB 测试文件，且当前不会自动清理。只能指向可丢弃的测试数据，严禁直接对生产运行。

文件管理验收使用相同环境变量：

```bash
R2_PLAYWRIGHT_PATH="$pw_dir/node_modules/playwright-core" \
R2_CHROMIUM=/usr/bin/chromium \
R2_TEST_URL=https://test.example.com \
R2_TEST_USERNAME=<temporary-admin> \
R2_TEST_PASSWORD=<temporary-password> \
node tests/file_management_acceptance.mjs
```

该脚本覆盖文件夹/文件拖排、快速连续顺序操作、单项和混合批量移动、自动重命名、图床移动、分享 URL 保留、HEAD/206/416、循环拒绝和 375/390/430px。

## 覆盖矩阵

- 上传期间滚动、搜索焦点和 `.shell` 节点身份。
- 拖拽、多文件串行、切目录后的目标冻结、失败后继续。
- 图床合法/非法图片、预览、复制、选择和删除。
- 375/390/430px、Drawer、Action Sheet、Modal 滚动。
- HEAD、206、416、实际流量、完整下载次数和限额。
- 旧公开路径、分享页、文件夹分享和分类越权。
- 旧 SQLite 行增量补列并保持 ID。
- 旧库 `sort_order` 初始化，多级目录分组隔离，上传/创建/删除/移动后顺序。
- 单文件、批量文件、单/批量文件夹、混合选择、冲突策略、循环和跨分类拒绝。
- 移动前后 ID、Token、`storage_path`、统计、Range 和分享路径。

详细手工用例见 [testing/regression-cases.md](testing/regression-cases.md)。

## 已知时序问题

`test_02_drive_upload_folder_and_range_statistics` 在完整响应 `read()` 后立即读取统计。服务线程在 `send_file()` 的 `finally` 中写统计，某些调度环境下查询会先发生，导致测试失败并使依赖它的后续测试连锁错误。真实生产 HTTPS 通过短轮询确认最终统计正确。修复测试时应等待目标计数（有上限超时），不能删除统计断言或在产品代码中人为 sleep。
