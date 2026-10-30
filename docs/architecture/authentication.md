# 认证架构

## 初始化和密码

`POST /api/initialize` 只在 `users` 为空时成功。用户名 3-32 字符，密码至少 10 字符。密码使用每用户 16-byte 随机 salt（hex 保存）和 PBKDF2-HMAC-SHA256 210000 次迭代，数据库只保存 64 字符 hex 哈希和 salt；没有 pepper 或独立认证密钥。

## Session

登录和初始化生成 36-byte URL-safe 随机 Token，客户端获得原 Token，数据库只保存 SHA-256 哈希。Session 有效期 30 天；创建新 Session 时删除已过期行。登出删除当前 Token 哈希并发送 Max-Age=0 Cookie。

Cookie 名为 `r2_drive_session`，属性为 `Path=/; HttpOnly; SameSite=Lax`。当 Caddy 传入 `X-Forwarded-Proto: https` 时增加 `Secure`。反向代理错误配置会导致缺少 `Secure`，部署验收必须检查。

## 权限

当前只有 `admin` 角色，私有查询仍要求记录 `user_id` 与当前用户一致，并拒绝 `disabled` 用户。schema 能存多用户不等于产品已实现用户管理、配额或租户安全；新增多用户必须单独设计。
