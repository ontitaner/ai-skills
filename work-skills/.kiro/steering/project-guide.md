---
inclusion: always
---

# Work-Skills 项目指引

## 项目定位

本工作空间是一个工作技能集合，通过 MCP Server 将外部系统能力（MySQL、SSH 远程服务器、Confluence Wiki、Redmine）暴露给 AI Agent 调用，并承载代码分析、文档生成、Bug 修复等日常开发工作流。

## 目录结构

```
work-skills/
├── .kiro/                         # Kiro 配置
│   ├── hooks/                     # Agent Hooks
│   ├── settings/mcp.json          # MCP Server 启动配置与环境变量
│   └── steering/                  # Steering 规则文件
├── scripts/                       # 工具脚本（AI 生成的辅助脚本统一存放）
└── docs/                          # Wiki 页面、导出数据、生成的图表等下载/输出文件
```

## 文件组织规范

| 用途 | 路径 | 说明 |
|------|------|------|
| 工具脚本 | `scripts/` | Python/Shell 等独立脚本，snake_case 命名 |
| 下载/输出 | `docs/` | Wiki 页面、导出数据、生成的图表等 |

禁止将文件散落到上述约定路径之外。目录不存在时自动创建。

## MCP Server 清单

| Server | 代码路径 | 主要 Tools |
|--------|----------|-----------|
| mysql | `mcp_server/mcp_mysql.py` | execute_sql |
| ssh-remote | `mcp_server/mcp_ssh_remote.py` | ssh_exec, ssh_build, ssh_file_read, ssh_list_dir, ssh_download, ssh_upload_dir, ssh_deploy_file, ssh_scp_transfer |
| confluence-wiki | `mcp_server/mcp_confluence_wiki.py` | get_page, create_page, update_page, search_pages, download_page_as_markdown, upload_markdown_to_page |
| redmine | `mcp_server/mcp_redmine.py` | list_issues, get_issue, create_issue, update_issue, delete_issue, list_projects, get_project, list_versions, create_version, list_time_entries, create_time_entry, search_redmine 等 |

## 技术栈

- Python 3.10+，MCP 框架 `mcp.server.fastmcp.FastMCP`，stdio transport
- 依赖：`requests`（Confluence API）、`pymysql`（MySQL）、`paramiko`（SSH/SFTP）
- MCP Server：一文件一 Server，`@mcp.tool()` 装饰器，返回 `str`（JSON），环境变量传入敏感配置

## 默认代码检索根路径

当需要阅读、搜索或理解业务源代码时，默认从以下本地路径检索：

```
D:\codes\B_4.5.2_x64_daily
```

- 这是项目的主代码仓库根目录，包含完整的业务源码
- 涉及代码查找、定位、阅读、分析等操作时，优先在此路径下进行
- 远程服务器上的对应路径由 `SSH_WORK_DIR` 环境变量控制

## 文档生成规范

当理解代码并生成文档时，按需包含以下章节：

1. 概述 → 2. 架构图（mermaid graph） → 3. 配置文件 → 4. 启动流程图（mermaid flowchart） → 5. 核心模块说明 → 6. 线程/进程模型 → 7. 时序图（mermaid sequence） → 8. 接口说明（含请求/响应 JSON 示例） → 9. 数据结构 → 10. 文件输出 → 11. 外部依赖

Mermaid 要求：节点中文标注，每篇至少 1 架构图 + 1 流程图 + 1 时序图。

## 文档检索优先级

1. Confluence Wiki — 通过 `confluence-wiki` MCP Server 搜索/下载
2. MySQL — 通过 `mysql` MCP Server 查询数据或表结构
3. 远程服务器 — 通过 `ssh-remote` MCP Server 读取文件或日志

## 代码规范

- 所有 AI 生成代码必须使用 `@AI_GENERATED` 注解标记包裹
- 错误返回格式：`f"Error: {status_code} - {text}"`
- 辅助函数以 `_` 开头，不暴露为 Tool
