# 单页自检：pointcloud-comparison（附录 E 骨架）

## E.1 文件与引用

| 检查项 | 状态 |
|--------|------|
| `page.md` | ⬜ |
| `layout.md` / `layout.puml` | ⬜ |
| `component.puml` 首行 include `layout.puml` | ⬜ |
| `model.puml` include `component.puml` | ⬜ |
| `api.puml` include `model.puml` | ⬜ |
| `style.md` / `checklist.md` | ⬜ |

## E.2 内容完整性

| 检查项 | 状态 |
|--------|------|
| 组件树与 layout 对应 | ⬜ |
| model 支撑请求体/视图状态 | ⬜ |
| api 列表与实际调用一致 | ⬜ |

## E.3 与 server 对齐

| 检查项 | 状态 |
|--------|------|
| API 在 `*-api` 有定义 | ⬜ |
| model 与 DTO 可对齐 | ⬜ |
| UC 在 `page.md` 跟踪列出 | ⬜ |
