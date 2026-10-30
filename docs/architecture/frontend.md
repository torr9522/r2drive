# 前端架构

## 组成

前端是 `INDEX_HTML` 字符串中的原生 HTML/CSS/JavaScript，没有 bundler、npm 运行依赖或组件框架。`S` 是唯一显式状态容器，`api()` 统一 JSON 请求和错误转换。

主要视图为初始化、登录、我的网盘和我的图床。桌面滚动容器是 `.work`；`<=920px` 时使用文档滚动和 Drawer，`<=560px` 进一步收紧布局。

## 渲染规则

- `render()`：登录状态、页面切换、目录或 Modal 结构变化。
- `renderDriveUploads()` / `renderImageUploads()`：上传任务局部更新。
- `updateImageSelectionDom()`：选择状态局部更新。
- `toast()`：直接更新 `#appToast`，不重建页面。
- `refreshUploadedTarget()`：任务完成时仅刷新任务所属且当前可见的列表。
- `renderPreservingScroll()`：仍需结构重建的 Modal/图床操作保存并恢复正确滚动容器。
- `focusWithoutScroll()`：在 animation frame 中使用 `focus({preventScroll:true})`。

禁止让 XHR `progress`、搜索 `input` 或 Toast 调用 `render()`。旧实现会反复替换 `.shell`，丢失焦点、滚动和节点身份。

## 搜索

网盘和图床搜索均对已加载的当前目录数组做 `name.toLowerCase().includes(...)` 过滤。输入事件只调整现有 DOM 可见性，不访问服务器。切换目录会清空搜索。

## 移动端

移动导航使用 Drawer；图床次要操作使用 Action Sheet。Modal 打开/关闭必须保持 `window.scrollY`，桌面则保持 `.work.scrollTop`。浏览器回归固定检查 375、390、430px 的横向溢出和交互。
