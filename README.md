# R2 Drive Personal Edition

R2 Drive 是面向单一所有者的小型自托管网盘和图床。它使用原生浏览器前端、Python HTTP 服务、SQLite 元数据和本地文件系统，不依赖前端构建链。

当前应用正式基线为 **v1.9.1**。正式安装脚本默认选择远程最新的 `vX.Y.Z` annotated tag，不直接部署 `main`。

## 能力

- 网盘文件上传、串行队列、多级目录、手动排序、单项/批量移动、搜索、下载、分享和流量限制
- JPG/JPEG/PNG/WEBP/GIF 图床、预览、链接格式、目录/图片排序、批量选择、移动和删除
- 旧公开路径、HTTP HEAD/Range、下载次数与实际流量统计
- 原生桌面和移动端界面，375/390/430px 视口已做浏览器验收
- Debian 11+ 一键安装、Python 虚拟环境、专用 systemd 用户和 Caddy HTTPS

## 快速开始

开发环境需要 Python 3.9+。应用当前唯一 Python 依赖是 `python-multipart`。

```bash
git clone https://github.com/torr9522/r2drive.git
cd r2drive
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
export R2_DRIVE_DATA=/tmp/r2-drive-data
export R2_DRIVE_HOST=127.0.0.1
export R2_DRIVE_PORT=8090
python app.py
```

打开 `http://127.0.0.1:8090/`，首次访问时创建管理员。不要把 `/tmp/r2-drive-data` 换成仓库内的 tracked 路径。

运行 HTTP 回归：

```bash
.venv/bin/python -m unittest -v tests/test_app.py
```

## 正式安装

在域名已指向 Debian 11+ 服务器且 80/443 端口开放后，以 root 执行：

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/torr9522/r2drive/main/install.sh) v1.9.1
```

不传版本时安装脚本选择远程最新正式 annotated tag。共享 Caddy 或已有站点的服务器必须先阅读[部署指南](docs/DEPLOYMENT.md)，不要盲目执行脚本。

## 文档入口

- [知识库索引](docs/README.md)
- [当前交接基线](docs/CURRENT_BASELINE.md)
- [架构](docs/ARCHITECTURE.md)与[功能规则](docs/FEATURES.md)
- [API](docs/API_REFERENCE.md)、[数据库](docs/DATABASE.md)与[存储](docs/STORAGE.md)
- [开发](docs/DEVELOPMENT_GUIDE.md)、[测试](docs/TESTING.md)与[发布](docs/RELEASE_PROCESS.md)
- [部署](docs/DEPLOYMENT.md)、[运维](docs/OPERATIONS.md)与[备份恢复](docs/BACKUP_RESTORE.md)
- [开发历史](docs/DEVELOPMENT_HISTORY.md)与[技术决策](docs/TECHNICAL_DECISIONS.md)

开始修改前请阅读 [AGENTS.md](AGENTS.md) 和 [CONTRIBUTING.md](CONTRIBUTING.md)。兼容路径、数据库 ID、分享 Token 和上传队列行为均属于稳定契约。
