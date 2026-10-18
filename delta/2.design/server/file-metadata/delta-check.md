# 域内核对：file-metadata（附录 F 骨架）

## 基准摘要

- 触发源：任务完成写路径、comparison-bundle 查询、受控下载。
- 核心能力：文件元数据、类型枚举（SOURCE_LAS / FILTERED / PREVIEW 等）、**不向浏览器暴露绝对路径**。
- **校验和**：可选；本期可省略，在 `file-metadata-model` 标注 N/A。

## 流程/架构一致性

- 无独立 workflow：**无 timer / 无 workflow**（除非后续孤儿文件清理）。

## 结论

见 `file-metadata-api/delta.md`。
