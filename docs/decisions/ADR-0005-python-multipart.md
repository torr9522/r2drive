# ADR-0005：使用 python-multipart

- 状态：Accepted（v1.8.3）
- 取代：标准库 `cgi.FieldStorage`

Python 3.13 删除 `cgi`，继续依赖会阻断运行。方案包括自行解析 multipart、固定旧 Python、其他受维护解析库和 `python-multipart`。选择后者，因为 API 小、维护中、支持流式文件对象，并避免手写复杂边界解析。

代价是项目首次有运行时 PyPI 依赖。版本范围固定为 `>=0.0.20,<0.1`，安装必须使用虚拟环境，升级依赖需回归畸形请求、大小限制和失败清理。
