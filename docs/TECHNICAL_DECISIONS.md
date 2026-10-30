# 技术决策索引

以下 ADR 记录当前约束。标记“回溯”的 ADR 是根据源码、Git 演进和 v1.8.3 审计整理，不声称存在未保存的原始会议记录。

| ADR | 决策 |
|---|---|
| [0001](decisions/ADR-0001-keep-sqlite.md) | 保留 SQLite |
| [0002](decisions/ADR-0002-local-filesystem-storage.md) | 使用本地文件系统实体存储 |
| [0003](decisions/ADR-0003-native-frontend.md) | 保留原生前端，不迁移 React/Vue |
| [0004](decisions/ADR-0004-no-uppy-dashboard.md) | 不完整引入 Uppy Dashboard |
| [0005](decisions/ADR-0005-python-multipart.md) | 使用 python-multipart |
| [0006](decisions/ADR-0006-upload-queue-lifecycle.md) | 上传队列独立于页面生命周期 |
| [0007](decisions/ADR-0007-freeze-upload-target.md) | 入队时冻结目标目录 |
| [0008](decisions/ADR-0008-local-dom-updates.md) | 进度和反馈采用局部 DOM 更新 |
| [0009](decisions/ADR-0009-stable-ids-and-tokens.md) | 保持 ID 与分享 Token 兼容 |
| [0010](decisions/ADR-0010-non-root-systemd.md) | systemd 使用专用非 root 用户 |
| [0011](decisions/ADR-0011-caddy-site-fragment.md) | Caddy 使用独立站点片段 |
| [0012](decisions/ADR-0012-python-virtualenv.md) | 部署使用 Python 虚拟环境 |

新决定应创建下一个编号 ADR，说明问题、证据、方案、取舍和兼容影响；不要事后重写已接受 ADR 来掩盖变化，应新增 superseding ADR。
