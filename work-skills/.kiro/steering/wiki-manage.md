---
inclusion: manual
---

# Wiki 管理规范

## 一、MCP Tool 速查

| Tool | 用途 | 关键参数 |
|------|------|----------|
| `get_page` | 读取页面内容 | `page_id` |
| `create_page` | 创建新页面 | `space_key`, `title`, `content`(HTML), `parent_id`(可选) |
| `update_page` | 更新页面内容 | `page_id`, `title`, `content`(HTML) |
| `search_pages` | 搜索页面 | `query`, `space_key`(可选), `limit`(默认10) |
| `download_page_as_markdown` | 下载页面为 Markdown（含图片） | `page_id`, `output_dir`(默认 `wiki_pages`) |
| `upload_markdown_to_page` | 上传 Markdown 至页面（含图片/mermaid） | `page_id`, `md_file`, `img_dir`(可选) |

## 二、页面搜索规范

使用 `search_pages` 时：

1. `query` 为 CQL 全文搜索关键词，支持中英文
2. 指定 `space_key` 可缩小搜索范围，提高准确性
3. 返回结果包含 `id`、`title`、`url`，可直接用于后续 `get_page` 或 `download_page_as_markdown`
4. 默认返回 10 条，可通过 `limit` 调整（最大由 Confluence 服务端限制）

## 三、下载规范

使用 `download_page_as_markdown` 时：

1. `output_dir` 必须设置为当前工作空间下的 `docs/<page_id_or_title>` 路径，确保每个页面独立隔离
2. 该页面关联的所有资源（图片、附件）自动下载到 `<safe_title>_images/` 子目录
3. 禁止将文件散落到 `docs/` 约定路径之外

### 调用示例

```
download_page_as_markdown(page_id="123456", output_dir="docs/123456")
```

### 输出目录结构

```
docs/
└── <page_id_or_title>/
    ├── <page_title>.md
    └── <page_title>_images/
        ├── img_001.png
        └── img_002.png
```

### 下载后处理

- 下载的 Markdown 文件首行为 `# 标题`，第二行为元信息（Page ID / Space / Version）
- 图片引用格式为相对路径 `![alt](<title>_images/img_001.png)`
- 支持的 HTML→Markdown 转换：标题、表格、代码块（含语言标注）、有序/无序列表、加粗/斜体/行内代码、链接、图片（ac:image 和 img 标签）、面板宏（info/note/warning/tip）、水平线

## 四、上传规范

### 4.1 文件来源

1. 默认从当前工作空间下的 `docs/` 目录搜索待上传的 Markdown 文件
2. 若用户未指定文件路径，优先在 `docs/` 及其子目录中查找匹配的文件
3. 若该目录下未找到目标文件，再提示用户确认具体路径

### 4.2 上传流程

`upload_markdown_to_page` 执行以下步骤：

1. 读取本地 Markdown 文件
2. 获取目标页面当前标题和版本号（自动递增版本）
3. 自动推断图片目录：`<md文件名去扩展名>_images/`（可通过 `img_dir` 覆盖）
4. 上传图片目录中的所有文件为页面附件（已存在则更新）
5. 将 Markdown 转换为 Confluence storage HTML
6. 渲染 mermaid 代码块为 PNG 并上传
7. 更新页面内容

### 4.3 调用示例

```
# 基本用法（图片目录自动推断为 docs/design_images/）
upload_markdown_to_page(page_id="123456", md_file="docs/design.md")

# 指定图片目录
upload_markdown_to_page(page_id="123456", md_file="docs/design.md", img_dir="docs/design_images")
```

### 4.4 Markdown→HTML 转换能力

上传时自动转换以下 Markdown 元素为 Confluence 格式：

| Markdown 元素 | Confluence 对应 |
|---------------|----------------|
| `# ~ ######` 标题 | `<h1> ~ <h6>` |
| ` ```lang ``` ` 代码块 | `ac:structured-macro[code]` + CDATA |
| ` ```mermaid ``` ` | 渲染为 PNG → `ac:image` 附件引用 |
| `**bold**` / `*italic*` / `` `code` `` | `<strong>` / `<em>` / `<code>` |
| `[text](url)` | `<a href>` |
| `![alt](path)` | `ac:image` 附件引用（需图片已上传） |
| `\| 表格 \|` | `<table>` |
| `- 无序列表` | `<ul><li>` |
| `1. 有序列表` | `<ol><li>` |
| `> 引用` | `ac:structured-macro[info]` 面板 |
| `---` | `<hr/>` |
| `<details><summary>` | `ac:structured-macro[expand]` 折叠块 |

## 五、Mermaid 图表处理

Confluence 不支持原生 mermaid 渲染。`upload_markdown_to_page` 内置自动处理：

1. 解析 Markdown 中的 ` ```mermaid ``` ` 代码块
2. 使用 `mmdc`（mermaid CLI）渲染为 PNG（白底，scale=2）
3. 上传 PNG 为页面附件
4. HTML 中用 `ac:image`（width=800）引用

图片命名规则：`mermaid_001.png`、`mermaid_002.png`，按文档中出现顺序编号。

### 超时处理

当 mermaid 图片数量较多（>5 张）时，MCP 工具调用可能超时。此时应：

1. 先用脚本预渲染所有 mermaid 图片到 `<md文件名>_images/` 目录
2. 调用 `upload_markdown_to_page` 时指定 `img_dir` 参数指向预渲染目录（预渲染图片会作为普通附件上传，mermaid 代码块仍会被转换为 `ac:image` 引用）
3. 或编写独立 Python 脚本放入 `scripts/` 目录完成上传

预渲染命令示例：
```
mmdc -i input.mmd -o output.png -b white -s 2
```

## 六、折叠内容处理

Markdown 中的 `<details><summary>` 标签自动转换为 Confluence 的 `expand` 宏：

- `<summary>` 内的文本作为折叠标题（默认标题："详情"）
- `<details>` 内的正文内容递归转换（支持嵌套代码块、表格、列表等）

Markdown 写法：
```markdown
<details>
<summary>报文格式</summary>

` ``json
{ "msg_type": "heartbeat", "node_id": "node_001" }
` ``

</details>
```

## 七、页面创建与更新

### 7.1 创建页面

`create_page` 参数说明：

- `space_key`：目标空间标识（必填）
- `title`：页面标题（必填，同空间内不可重复）
- `content`：Confluence storage HTML 格式内容（非 Markdown）
- `parent_id`：父页面 ID（可选，不填则创建在空间根目录）

### 7.2 更新页面

`update_page` 自动处理版本递增，无需手动指定版本号。

- `page_id`：目标页面 ID（必填）
- `title`：页面标题（必填，可保持原标题不变）
- `content`：新的 Confluence storage HTML 内容

### 7.3 注意事项

- `create_page` 和 `update_page` 的 `content` 参数接收 Confluence storage HTML，不是 Markdown
- 若需上传 Markdown 文件，应使用 `upload_markdown_to_page`（自动完成 MD→HTML 转换）
- 若需在代码中动态生成页面内容，先用 `_md_to_confluence_html` 的逻辑转换，或直接拼接 Confluence HTML

## 八、常见工作流

### 8.1 下载→编辑→重新上传

```
1. search_pages(query="关键词") → 获取 page_id
2. download_page_as_markdown(page_id, output_dir="docs/<page_id>") → 本地编辑
3. 编辑 Markdown 文件
4. upload_markdown_to_page(page_id, md_file="docs/<page_id>/xxx.md")
```

### 8.2 代码分析→生成文档→上传 Wiki

```
1. 阅读源码，生成 Markdown 分析文档（含 mermaid 图表）
2. 保存到 docs/<文档名>.md
3. search_pages(query="文档标题") → 确认目标页面是否存在
4. 若存在: upload_markdown_to_page(page_id, md_file="docs/<文档名>.md")
5. 若不存在: create_page(space_key, title, content) → 获取新 page_id → upload_markdown_to_page
```

### 8.3 Bug 修复文档同步

在 `redmine-bugfix-workflow` 第 5 步中，将分析文档上传至 Wiki：

```
1. 生成分析文档 Markdown（含问题现象、根因、修复方案、mermaid 图表）
2. upload_markdown_to_page(page_id, md_file) 或 create_page 创建新页面
3. 记录 Wiki URL 供 Redmine notes 和企业微信通知引用
```
