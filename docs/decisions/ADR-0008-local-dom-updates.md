# ADR-0008：进度和反馈使用局部 DOM 更新

- 状态：Accepted（v1.8.3）

`app.innerHTML` 整体替换适合页面结构切换，不适合高频 progress、Toast、搜索和选择。可选方案是保存/恢复 scroll、虚拟 DOM 框架或直接更新局部节点。选择局部更新，因为它同时保持滚动、焦点、节点身份且不引入框架。

代价是局部 DOM 必须与 `S` 同步，代码需明确哪个变化可局部处理。不能用强制 `scrollTop` 掩盖整页替换；结构 Modal 重建才使用有界的 `renderPreservingScroll()`。
