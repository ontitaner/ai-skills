---
inclusion: always
---

# AI_SKILLS 项目指引

## 项目定位

本工作空间是一个 AI 技能集合，通过 MCP Server 将外部系统能力（MySQL、SSH 远程服务器、Confluence Wiki）暴露给 AI Agent 调用。

## 目录结构

```
AI_SKILLS/
├── .kiro/                         # Kiro 配置（工作空间级）
│   ├── hooks/                     # Agent Hooks
│   ├── settings/mcp.json          # MCP Server 启动配置与环境变量
│   └── steering/                  # Steering 规则文件
├── mcp_server/                    # MCP Server 实现（核心代码）
│   ├── mcp_mysql.py               # MySQL 查询 — Tool: execute_sql
│   ├── mcp_ssh_remote.py          # SSH 远程操作 — Tools: ssh_exec, ssh_build, ssh_file_read, ssh_list_dir, ssh_download, ssh_upload_dir, ssh_deploy_file, ssh_scp_transfer
│   ├── mcp_confluence_wiki.py     # Confluence Wiki — Tools: get_page, create_page, update_page, search_pages, download_page_as_markdown, upload_markdown_to_page
│   └── mcp_redmine.py            # Redmine 项目管理 — Tools: list_issues, get_issue, create_issue, update_issue, delete_issue, list_projects, get_project, list_versions, create_version, list_time_entries, create_time_entry, search_redmine 等
├── scripts/                       # 工具脚本（AI 生成的辅助脚本统一存放）
├── ontitaner.github.io/           # 文档站点（Next.js）
│   └── docs/                      # 生成文档的默认存放目录
├── rag_skill/                     # RAG 检索增强技能模块
│   └── rag/                       # RAG 向量知识库引擎
├── ai_build/                      # AI 编写的项目代码（每个项目一个子目录）
└── AI_SKILLS.code-workspace       # VS Code / Kiro 工作空间文件
```

## 技术栈

- Python 3.10+（使用 `str | int` 等新语法）
- MCP 框架：`mcp.server.fastmcp.FastMCP`，stdio transport
- 依赖：`requests`（Confluence API）、`pymysql`（MySQL）、`paramiko`（SSH/SFTP）

## MCP Server 开发约定

- 每个 Server 一个文件，放在 `mcp_server/mcp_<name>.py`
- Tool 函数使用 `@mcp.tool()` 装饰器，返回值统一为 `str`（JSON 字符串）
- 敏感配置通过环境变量传入，在 `.kiro/settings/mcp.json` 中声明
- 入口：`if __name__ == "__main__": mcp.run(transport="stdio")`
- 新增 Server 后需同步更新 `mcp.json` 配置

## 默认代码检索根路径

当需要阅读、搜索或理解业务源代码时，默认从以下本地路径检索：

```
D:\codes\B_4.5.2_x64_daily
```

- 这是项目的主代码仓库根目录，包含完整的业务源码
- 涉及代码查找、定位、阅读、分析等操作时，优先在此路径下进行
- 远程服务器上的对应路径由 `SSH_WORK_DIR` 环境变量控制（当前为 `/home/windos/envision/src_452_daily`）

## 文档生成约定

当理解代码并生成文档时：

- 默认保存路径：`ontitaner.github.io/docs/`
- 文件命名：以进程名（可执行文件名）作为文件名，如 `ontitaner.github.io/docs/DataCollector.md`
- 格式：Markdown
- 若同名文件已存在，更新内容而非新建

## 脚本存放约定

AI 生成的辅助脚本（工具脚本、自动化脚本等）统一存放在工作空间根目录的 `scripts/` 下：

- 默认保存路径：`scripts/`
- 文件命名：使用 snake_case，简洁描述脚本用途，如 `scripts/sync_docs.py`
- 禁止将脚本散落在其他目录

### 文档结构规范

生成的文档必须包含以下章节（按顺序），根据实际代码内容取舍：

1. **概述** — 进程用途、运行模式、一句话定位
2. **架构图** — 使用 mermaid 展示模块/组件关系：
   ```mermaid
   graph TD
     A[模块A] --> B[模块B]
     A --> C[模块C]
   ```
3. **配置文件** — 配置项说明 + 示例
4. **启动流程图** — 使用 mermaid flowchart 展示初始化链路：
   ```mermaid
   flowchart TD
     Start[main] --> Init[初始化]
     Init --> Run[启动服务]
   ```
5. **核心模块说明** — 每个类/模块的职责、关键方法、配置参数
6. **线程/进程模型** — 如有多线程，用 mermaid 展示线程交互
7. **关键时序图** — 使用 mermaid sequence diagram 展示核心业务流程：
   ```mermaid
   sequenceDiagram
     participant A as 模块A
     participant B as 模块B
     A->>B: 请求数据
     B-->>A: 返回结果
   ```
8. **接口说明**（如存在网络接口/API/消息总线接口）：
   - 接口列表表格：方法、URL（含端口）、说明
   - 每个接口提供完整的请求/响应 JSON 示例，格式如下：
     ```
     ### 接口名称
     - 方法: POST
     - URL: `http://host:port/api/path`
     - 说明: 接口用途

     请求示例:
     ```json
     {
       "field1": "value1",
       "field2": 123
     }
     ```

     响应示例:
     ```json
     {
       "code": 0,
       "message": "success",
       "data": { ... }
     }
     ```
     ```
   - 若进程不对外暴露 HTTP/TCP 接口，注明"本进程无对外网络接口"并说明其数据交互方式（如共享内存、文件、消息总线等）
9. **数据结构** — 关键 struct/class 的字段说明，二进制格式用图示
10. **文件输出** — 输出文件路径、格式、命名规则
11. **外部依赖** — 依赖库表格

### Mermaid 图表要求

- 架构图使用 `graph TD` 或 `graph LR`，展示模块间依赖和数据流向
- 流程图使用 `flowchart TD`，展示程序启动、初始化、主循环等关键流程
- 时序图使用 `sequenceDiagram`，展示模块间的调用顺序和数据交换
- 图表中的节点名称使用中文标注，便于阅读
- 每个文档至少包含：1 个架构图 + 1 个流程图 + 1 个时序图

## ai_build 项目代码约定

`ai_build/` 目录专门用于存放 AI 编写的项目代码，遵循以下规范：

- 使用 AI 编写项目代码时，默认均在 `ai_build/` 路径下创建
- 每个项目必须存放在 `ai_build/` 的独立子目录中，如 `ai_build/my_project/`、`ai_build/data_tool/`
- 禁止将项目文件直接散落在 `ai_build/` 根目录，必须按项目分目录组织
- 子目录命名使用小写字母 + 下划线（snake_case），简洁描述项目用途
- 每个项目子目录应包含自身的 README.md 或说明文件，描述项目用途和使用方式
- 不同项目之间保持隔离，不得跨项目目录引用或混放文件

## 文档检索优先级

1. 本地 `ontitaner.github.io/docs/` — 项目参考文档（按进程名命名）
2. Confluence Wiki — 通过 `confluence-wiki` MCP Server 搜索/下载
3. MySQL — 通过 `mysql` MCP Server 查询数据或表结构
4. 远程服务器 — 通过 `ssh-remote` MCP Server 读取文件或日志

## 代码规范

- 所有 AI 生成代码必须使用 `@AI_GENERATED` 注解标记包裹
- 错误返回格式：`f"Error: {status_code} - {text}"`
- 辅助函数以 `_` 开头，不暴露为 Tool
