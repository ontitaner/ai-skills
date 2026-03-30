---
inclusion: always
---

# AI_SKILLS 项目指引

## 项目定位

本工作空间是一个 AI 技能集合，包含 MCP Server 实现代码、文档站点和辅助脚本。

## 目录结构

```
AI_SKILLS/
├── .kiro/                         # Kiro 配置
├── mcp_server/                    # MCP Server 实现（核心代码）
├── scripts/                       # 工具脚本（AI 生成的辅助脚本统一存放）
├── work-skills/                   # 工作技能工作空间（SSH/MySQL/Wiki/Redmine 相关配置）
├── ontitaner.github.io/docs/      # 生成文档的默认存放目录
├── ai_build/                      # AI 编写的项目代码（每个项目一个子目录）
└── AI_SKILLS.code-workspace       # 工作空间文件
```

## 文件组织规范

| 用途 | 路径 | 说明 |
|------|------|------|
| 工具脚本 | `scripts/` | Python/Shell 等独立脚本，snake_case 命名 |
| MCP Server | `mcp_server/` | MCP 服务端代码，`mcp_<name>.py` 格式 |
| 下载/输出 | `download/` | 导出数据、生成的图表等 |
| 文档 | `ontitaner.github.io/docs/` | 以进程名命名，Markdown 格式 |
| AI 项目 | `ai_build/<project>/` | 每个项目独立子目录，snake_case 命名，含 README |

禁止将文件散落到上述约定路径之外。目录不存在时自动创建。

## 技术栈

- Python 3.10+，MCP 框架 `mcp.server.fastmcp.FastMCP`，stdio transport
- MCP Server：一文件一 Server，`@mcp.tool()` 装饰器，返回 `str`（JSON），环境变量传入敏感配置

## 文档生成规范

生成的文档按需包含以下章节：

1. 概述 → 2. 架构图（mermaid graph） → 3. 配置文件 → 4. 启动流程图（mermaid flowchart） → 5. 核心模块说明 → 6. 线程/进程模型 → 7. 时序图（mermaid sequence） → 8. 接口说明（含请求/响应 JSON 示例） → 9. 数据结构 → 10. 文件输出 → 11. 外部依赖

Mermaid 要求：节点中文标注，每篇至少 1 架构图 + 1 流程图 + 1 时序图。

## 代码规范

- 所有 AI 生成代码必须使用 `@AI_GENERATED` 注解标记包裹
- 错误返回格式：`f"Error: {status_code} - {text}"`
- 辅助函数以 `_` 开头，不暴露为 Tool
