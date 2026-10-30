# 验收历史

## v1.8.3 独立测试环境

日期：2026-10-30。目标为独立 Debian 12 测试服务器，部署 commit `a321eb47cf9a5686285d3e78ea4c47c262224073`。测试机不作为源码主环境，临时修复均回到开发仓库提交后重新部署。

### HTTP 回归

`tests/test_app.py` 六组通过：

1. 认证、Session 和 HTTPS Secure Cookie。
2. 上传、目录、HEAD、Range 和统计。
3. 重命名、限额、私密/公开、旧路径、删除后失效。
4. 图片格式、批量移动/删除和分类隔离。
5. 文件夹分享与非空删除拒绝。
6. 旧 SQLite 补列并保留旧行。

### Chromium

最终脚本输出的关键证据：

```json
{
  "desktopUploadScroll": 710,
  "desktopUploadFocus": "search",
  "stableShellDuringAndAfterUpload": true,
  "frozenQueueTargetFiles": ["queue-large.bin", "queue-small.txt"],
  "dragUpload": "dragged.txt",
  "imageActions": ["preview", "copy", "select", "delete", "failure-continues"],
  "mobileViewports": [375, 390, 430],
  "mobileModalScroll": 600,
  "mobileUpload": "mobile-upload.txt",
  "mobileImageActionSheet": true,
  "pageErrors": 0,
  "expectedHttpConsoleErrors": 2
}
```

两个预期资源错误是匿名 `/api/me` 401 和故意上传非法图片的 400，不是未处理页面异常。

### 其他证据

- HEAD 200，不增加流量。
- Range 206，四字节；非法 Range 416。
- Range 只增加四字节流量。
- 服务重启后文件数量保持。
- HTTPS 登录 Cookie 有 HttpOnly、SameSite=Lax、Secure。
- R2 Drive 和 Caddy error journal 无条目。

## 生产发布

同日将 `main` fast-forward 到应用基线，单独推送 annotated `v1.8.3` 并创建 Latest Release。没有 force push、历史 Tag 移动或批量推送 Tag。

生产环境实际为 Debian 12，公开入口 `https://wp.68362596.xyz/`。部署前核对线上和磁盘证书，部署后 SHA256 指纹保持 `E3:84:70:D1:E7:C4:66:88:37:5D:54:62:0D:D8:08:BA:3E:32:24:04:48:43:76:93:B1:54:A2:61:F9:C4:80:20`，没有重新签发。

按授权对旧 R2 Drive 建立临时 root-only 回滚包，只迁移管理员认证字段到全新数据库，不迁移 Session、文件、目录、分享或统计。验收后删除回滚包和迁移源。最终数据库为 1 个管理员、0 Session、0 folders、0 files，storage 为空；其他独立服务保持 active。

生产真实 HTTPS 验收覆盖登录、Cookie、上传、下载、重命名、分享、删除、统计最终落库、浏览器交互和重启持久性。测试数据最终全部删除。

## 失败案例

- 首次真实测试部署发现 Caddy 站点片段权限为 0600，Caddy 用户无法读；修复为 0644 并形成 commit `742d59b4`。
- 开发机直接用系统 Python 跑测试时缺少 `python-multipart`；在隔离 venv 按 requirements 安装后通过，说明文档不能写成“仅标准库”。
- 生产机隔离套件两次在完整下载后立即读取到旧统计，后续状态依赖用例连锁失败；真实 HTTPS 用有界轮询确认统计提交。测试竞态未修复，见 `KNOWN_ISSUES.md`。

## 未覆盖

Firefox、Safari、Python 3.13 实机、高并发、压力、数日运行和大规模故障注入均未做。不得从现有结果推断这些范围已经通过。
