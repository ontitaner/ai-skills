---
inclusion: always
---

# Wiki 页面下载规范

当使用 Confluence Wiki 下载功能（`download_page_as_markdown`）时，遵循以下规则：

1. 默认输出目录为当前工作空间下的 `download` 路径。
2. 每个下载的页面必须存放在独立的子目录中，子目录以页面 ID 或页面标题命名，确保文件隔离。
3. 该页面关联的所有资源（如图片、附件等）也必须约束在同一子目录下，不得散落到其他位置。

示例目录结构：

```
download/
├── <page_id_or_title_1>/
│   ├── page.md
│   └── page_images/
│       ├── img1.png
│       └── img2.png
└── <page_id_or_title_2>/
    ├── page.md
    └── page_images/
        └── img1.png
```
