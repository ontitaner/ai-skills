---
inclusion: manual
---

# Redmine Bug 修复全链路工作流

本规则定义了基于 Redmine 任务驱动的 Bug 修复完整流程。开发者只需在关键节点做决策，其余步骤由 AI 自动串联执行。

## 工作流步骤（共 10 步）

### 第 1 步：捞取任务
- 从 Redmine 获取指定 Issue 详情（`get_issue`），包含 `journals` 和 `children` 信息
- 提取关键字段：主题、描述、优先级、指派人、测试 Owner、关联模块

### 第 2 步：状态流转 → Developing
- ⚠️ **需要用户确认** 后，将 Issue 状态更新为 Developing（status_id=2）
- notes 中必须包含 `[AI]` 标识符前缀
- notes 格式：`[AI] 开始处理：问题简述`

### 第 3 步：代码分析
- 根据 Issue 描述定位相关源码文件
- 阅读并理解相关函数逻辑
- 定位问题根因
- 枚举边界场景，检查是否存在关联问题

### 第 4 步：生成分析文档
- 在本地生成 Markdown 格式的分析文档，包含：
  - 问题现象
  - 根因分析（含代码片段）
  - 修复方案
  - 影响范围评估
  - 边界场景验证

### 第 5 步：Wiki 同步
- 将分析文档上传至 Confluence Wiki（`upload_markdown_to_page` 或 `create_page`）
- 记录 Wiki 页面 URL 供后续引用

### 第 6 步：代码修改
- 按照分析文档中的修复方案修改代码
- 所有 AI 生成的代码必须添加 `@AI_GENERATED` 标注
- 遵守项目编码规范（参考其他 steering 规则）

### 第 7 步：SSH 远程编译
- 通过 SSH 将修改后的代码同步到远程编译服务器
- 执行编译命令（`ssh_build`）
- 确认编译通过，如失败则修复后重新编译

### 第 8 步：版本管理提交（SVN）
- ⚠️ **需要用户确认** 才能执行提交操作
- 展示修改的文件列表和 diff 摘要
- 本地 SVN 工作副本路径：`D:\codes\B_4.5.2_x64_daily\src\`
- SVN 提交信息格式（pre-commit hook 强制要求，否则提交会被拒绝）：
  ```
  (Issue #xxxx) 描述
  ```
  示例：`(Issue #185744) scada_sm3.cpp 中 T() 和 GG() 函数 return 0 补充缺失分号`
- 用户确认后在本地通过 `svn commit` 提交

### 第 9 步：Redmine Resolve
- ⚠️ **需要用户确认** 后，将 Issue 状态更新为 Resolved
- notes 中必须包含 `[AI]` 标识符前缀，表明该操作由 AI 辅助完成
- notes 格式：`[AI] 修改摘要、修改文件列表、Wiki 链接`
- 示例：`[AI] 修复完成：scada_sm3.cpp 第52行和第78行 return 0 补充缺失分号，编译通过`
- 必填自定义字段「问题引入」（id=62），可选值：需求、设计、编码、集成、实施、merge、历史遗留、文档

### 第 10 步：企业微信通知
- 通过 Postman 或 Webhook 发送企业微信群通知
- 通知内容包含：任务ID、主题、类型、状态、测试Owner、修改摘要、Wiki 链接

## 关键约束

1. **版本管理操作（SVN/Git 提交）必须经过用户确认才能执行**
2. **Redmine 状态变更（Developing → Resolved）必须经过用户确认才能执行**
3. 代码修改必须遵守项目编码规范和 AI 代码标注规范
4. 分析文档必须在代码修改前完成
5. 编译必须通过后才能进入提交步骤

## 使用方式

在对话中引用此规则后，提供 Redmine Issue 号即可启动全流程：
```
请按照 Bug 修复工作流处理 #XXXXX
```
