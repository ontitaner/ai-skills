---
inclusion: manual
---

# Redmine 默认配置

## 一、默认参数

- 项目标识符: `universal-scada`（项目 ID: `148`）
- 适用工具: `list_issues`, `list_versions`, `list_memberships`, `create_issue`, `create_version`, `search_redmine`
- 当用户未指定 `project_id` 时，自动使用 `universal-scada`

### ⚠️ Issue 更新备注规范

当通过 `update_issue` 执行任何更新操作时，`notes` 参数**必须**添加 AI 生成标记前缀：

**格式：** `[AI by Kiro] <具体变更说明>`

**示例：**
- `[AI by Kiro] 目标Sprint由 平台Sprint2026-03 更新为 平台Sprint2026-04`
- `[AI by Kiro] 状态更新为已解决`
- `[AI by Kiro] 指派人变更为 chengyang.liu`

**规则：**
1. 每次调用 `update_issue` 时，`notes` 不得为空，必须包含 `[AI by Kiro]` 前缀
2. 前缀后紧跟一个空格，再写具体的变更内容描述
3. 变更描述应简洁明确，说明"改了什么"和"从什么改为什么"

### 默认关注成员

| ID | 用户名 | 角色 |
|----|--------|------|
| 35 | guobao.liu | Developer, Dev Leader, Manager |
| 61 | lihu.yang | Developer |
| 750 | xin.wang4 | Developer, Manager+, Dev Leader |
| 1202 | yunfei.liu2 | Developer |
| 1323 | husile.peng | Developer |
| 1325 | fei.lv4 | Developer |
| 1340 | peng.weng | Developer |
| 1345 | chengyang.liu | Developer |
| 1348 | hao.sun | Developer |

### ⚠️ 多人查询强制约束

当用户要求查询"全部成员"、"所有人"、"团队"或未指定具体人员时，**必须且只能**遍历上方"默认关注成员"表中的 9 位成员，逐人使用 `assigned_to_id` 查询。

**严禁以下行为：**
1. 禁止使用 `fixed_version_id` 或其他维度做全项目查询后再按人分组——这会引入非关注成员的数据
2. 禁止在输出结果（表格、图表、汇总）中包含不在默认关注成员名单中的人员
3. 禁止自行扩展成员范围，即使查询结果中出现了其他人员的数据也必须丢弃

**唯一例外：** 用户明确指定了某个不在名单中的人员姓名时，可单独查询该人员，但不得将其混入"全部成员"的汇总结果中。

---

## 二、Sprint 版本 ID 映射表

查询 issue 时经常需要 `fixed_version_id`，以下是项目 `universal-scada`（ID: 148）常用 Sprint 版本的名称→ID 映射。

**查找规则（严格按顺序执行）：**
1. 先在下方映射表中查找，命中则直接使用对应 ID，不调用任何 MCP 工具
2. 若映射表中未找到，调用 `find_version_by_name(name)` 进行模糊匹配
3. 若仍未找到，调用 `refresh_version_cache()` 刷新缓存后重试一次
4. 找到新版本后，提醒用户更新此映射表

### 平台月度 Sprint

| 版本名称 | version_id |
|----------|------------|
| 平台Sprint2024-backup | 4523 |
| 平台Sprint2025-01 | 4774 |
| 平台Sprint2025-02 | 4775 |
| 平台Sprint2025-03 | 4776 |
| 平台Sprint2025-04 | 4827 |
| 平台Sprint2025-05 | 4828 |
| 平台Sprint2025-06 | 4829 |
| 平台Sprint2025-07 | 4830 |
| 平台Sprint2025-08 | 4957 |
| 平台Sprint2025-09 | 4958 |
| 平台Sprint2025-10 | 4959 |
| 平台Sprint2025-11 | 4960 |
| 平台Sprint2025-12 | 4961 |
| 平台Sprint2025-backup | 4831 |
| 平台Sprint2026-01 | 5073 |
| 平台Sprint2026-02 | 5074 |
| 平台Sprint2026-03 | 5118 |
| 平台Sprint2026-04 | 5119 |
| 平台Sprint2026-05 | 5120 |
| 平台Sprint2026-06 | 5121 |

### 产品版本（FT/SP/hotfix）

| 版本名称 | version_id |
|----------|------------|
| 4.5.2_SP | 4368 |
| 4.5.2_SP2 | 4792 |
| 4.5.2_SP3 | 4793 |
| 4.5.2_SP4 | 4889 |
| 4.5.2_SP5 | 4994 |
| 4.5.2_FT008 | 4749 |
| 4.5.2_FT021 | 4977 |
| 4.5.2_FT022 | 4987 |
| 4.5.2_FT023 | 4975 |
| 4.5.2_FT024 | 4999 |
| 4.5.2_FT025 | 5001 |
| 4.5.2_FT026 | 5007 |
| 4.5.2_FT027 | 5021 |
| 4.5.2_FT028 | 5023 |
| 4.5.2_FT029 | 5030 |
| 4.5.2_FT030 | 5032 |
| 4.5.2_FT031 | 5040 |
| 4.5.2_FT032 | 5057 |
| 4.5.2_FT033 | 5077 |
| 4.5.2_FT034 | 5117 |
| 4.5.2_FT035 | 5134 |
| 4.5.2_FT036 | 5137 |

---

## 三、统一查询工作流（Feature / Task / Bug）

所有类型的未完成任务查询使用同一工作流。根据用户意图决定查询哪些类型，**每种类型独立查询、独立统计，不混合输出**。

### 查询类型判定规则

| 用户意图关键词 | 查询的 tracker | tracker_id |
|---------------|---------------|------------|
| "任务"/"Feature"/"Task"/"工作" | Feature(2)，无结果降级 Task(4) | 2 → 4 |
| "Bug"/"缺陷"/"问题" | Bug | 1 |
| "全部"/"汇总"/"所有类型" | Feature(2) + Task(4) + Bug(1) | 2, 4, 1 |

**核心原则：用户只问 Bug 就只查 Bug，只问 Feature/Task 就只查 Feature/Task，不要交叉混入其他类型。**

### ⚠️ Tracker 类型强制约束

本工作流**仅允许查询以下三种 tracker 类型**：

| tracker_id | 名称 | 说明 |
|------------|------|------|
| 1 | Bug | 缺陷 |
| 2 | Feature | 功能需求 |
| 4 | Task | 任务 |

**严禁以下行为：**
1. 禁止查询上述三种以外的 tracker（如 Support、Patch 或其他自定义类型），即使 Redmine 项目中存在也不得使用
2. 禁止省略 `tracker_id` 参数进行无类型限定的查询——这会返回所有类型的 issue，导致结果混入非目标类型
3. 禁止在输出结果中包含非 Feature/Task/Bug 类型的 issue，若返回数据中混入其他类型必须丢弃
4. 每次 `list_issues` 调用必须明确指定 `tracker_id` 为 1、2 或 4 之一

### Step 1: 确定目标人员

1. 从用户输入中提取人员英文用户名（如 `chengyang.liu`）
2. 先在"默认关注成员"表中查找，若命中直接使用对应 `ID`
3. 若未命中，调用 `list_memberships(project_id = "universal-scada")` 获取项目成员列表进行匹配
4. 注意成员列表默认分页 25 条，需关注 `total_count`
5. 若用户要求查询"全部成员"/"所有人"/"团队"，**严格遍历默认关注成员表中的 9 人，不得扩展范围**
6. **禁止使用全项目维度查询（如按 fixed_version_id 查全部 issue 再分组），必须逐人用 assigned_to_id 查询**

### Step 2: 逐人逐类型查询

对每位目标人员，根据判定的查询类型，分别调用（**每次调用必须指定 tracker_id 为 1、2 或 4，禁止省略**）：

**Feature（tracker_id=2）：**
```
list_issues(project_id="universal-scada", assigned_to_id=<user_id>, status="open", tracker_id="2", limit=100, sort="updated_on:desc")
```

**Task（tracker_id=4）— 仅当 Feature 过滤后为空时降级查询：**
```
list_issues(project_id="universal-scada", assigned_to_id=<user_id>, status="open", tracker_id="4", limit=100, sort="updated_on:desc")
```

**Bug（tracker_id=1）：**
```
list_issues(project_id="universal-scada", assigned_to_id=<user_id>, status="open", tracker_id="1", limit=100, sort="updated_on:desc")
```

- `status = "open"` 排除已关闭、已拒绝等终态
- 若 `total_count` > `limit`，需分页查询（offset 递增）

### Step 3: 过滤本月 + 未解决

从返回结果中筛选：
1. `fixed_version.name` 包含当前月份 Sprint（如 `平台Sprint2026-03`，对应 version_id 参见"Sprint 版本 ID 映射表"），或 `created_on` / `updated_on` 在本月范围内
2. 状态为"新建"(status_id=1) 或"开发中"(status_id=2) 视为**未解决**
3. 其他状态（已解决/FT已解决/已验证/SP已解决等）均视为**已解决**，排除在外

### Step 4: 逐人输出

每完成一位成员的查询和过滤后，立即输出该成员的结果（避免数据量过大导致截断）。**输出结果中只允许包含默认关注成员名单中的人员。**

**仅查 Feature/Task 时的输出格式：**

**成员: xxx（ID: xxx）**

| # | ID | 类型 | 状态 | 主题 |
|---|------|------|------|------|
| 1 | xxxxx | Feature/Task | 新建/开发中 | 任务主题 |

**仅查 Bug 时的输出格式：**

**成员: xxx（ID: xxx）— 未解决 Bug: N 条**

| # | Bug ID | 状态 | 严重等级 | 主题 |
|---|--------|------|----------|------|
| 1 | xxxxx  | 新建/开发中 | Major/Average/Minor | Bug 主题 |

若该成员无结果，输出：`xxx — 无未解决项 ✅`

### Step 5: 汇总统计表

全部成员输出完毕后，输出汇总表格（**仅包含默认关注成员名单中的 9 人，不得出现名单外人员**）。

汇总表格的列根据实际查询类型动态生成，**只展示本次查询涉及的类型列**：

**仅查 Feature/Task 时：**

| 成员 | Feature | Task | 合计 |
|------|---------|------|------|
| xxx  | N       | N    | N    |
| **合计** | **N** | **N** | **N** |

**仅查 Bug 时：**

| 成员 | 新建 | 开发中 | 未解决合计 |
|------|------|--------|-----------|
| xxx  | N    | N      | N         |
| **合计** | **N** | **N** | **N** |

**查全部类型时：**

| 成员 | Feature | Task | Bug | 合计 |
|------|---------|------|-----|------|
| xxx  | N       | N    | N   | N    |
| **合计** | **N** | **N** | **N** | **N** |

### Step 6: 生成汇总图表

使用 Python + matplotlib 生成分组柱状图：
- 按成员分组，**柱子颜色仅对应本次查询涉及的类型**（Feature 蓝色 #4472C4 / Task 橙色 #ED7D31 / Bug 红色 #E74C3C）
- 图片保存路径: `download/redmine_summary_<YYYYMMDD>.png`
- 图表标题包含项目名、月份、查询类型信息
- 中文字体使用 `SimHei` 或系统可用中文字体
