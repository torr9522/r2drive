# 安全模型

## 已有控制

- PBKDF2-HMAC-SHA256 210000 次和每用户随机 salt。
- Session 数据库只存 Token SHA-256；Cookie HttpOnly、SameSite=Lax，HTTPS 代理下 Secure。
- 私有 API 绑定当前用户，文件和目录再按分类隔离。
- 参数化 SQL；动态 UPDATE 字段来自固定白名单。
- 名称拒绝路径分隔符和 NUL；磁盘名进一步净化。
- 图床白名单扩展名/MIME/文件头，拒绝 SVG inline。
- JSON/上传大小限制，失败上传清理。
- systemd 非 root、严格文件系统保护、私有临时目录和 0077 umask。
- Caddy 终止 TLS，并设置 nosniff 与 Referrer-Policy。

## 边界和限制

- 没有 CSRF Token、登录速率限制、审计日志、MFA、病毒扫描或内容安全扫描。
- Session 最长 30 天，没有全局“退出所有设备”界面。
- `ThreadingHTTPServer` 不是面向互联网的 TLS 边界，必须置于 Caddy 后并监听回环地址。
- 应用吞掉默认访问日志；诊断依赖 systemd/Caddy 状态，业务审计能力有限。
- 文件分享 Token 等同访问凭证，不应出现在公开日志或 Issue。

## 密钥和数据纪律

禁止提交密码、密码哈希、Session/Cookie、API Token、SSH 密钥、TLS/ACME 私钥、数据库、真实文件、生产日志和 `.env`。文档只写变量名与占位符。发现历史泄露时不要擅自重写历史；先报告对象、commit 范围和轮换建议，由所有者授权处理。

发布前执行当前工作树和 Git 历史扫描，检查 PEM 头、常见 Token 前缀、凭据赋值、数据库和大文件对象。`.gitignore` 只是防误提交，不替代 `git diff --cached` 检查。

2026-10-30 知识库建设时，对全部可达 commit 做了高置信模式扫描，未发现私钥头、常见云/GitHub/Slack/OpenAI Token、Cookie 值、带密码 URL、敏感扩展名对象或大于 1 MiB 的历史 blob。环境没有安装 gitleaks/trufflehog，因此该结果是规则扫描而非专用工具证明；未来发布仍应重复并人工审查 staged diff。
