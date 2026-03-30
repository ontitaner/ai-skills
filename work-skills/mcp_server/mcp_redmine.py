# @AI_GENERATED: Kiro v1.0
"""
Redmine MCP Server - 操作 Redmine 项目管理系统
支持：Issue 增删改查、项目列表、用户查询、时间记录、版本管理
使用 API Key 认证
"""

import json
import os
import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("redmine")

REDMINE_URL = os.environ.get("REDMINE_URL", "").rstrip("/")
REDMINE_API_KEY = os.environ.get("REDMINE_API_KEY", "")


def _headers():
    return {
        "Content-Type": "application/json",
        "X-Redmine-API-Key": REDMINE_API_KEY,
    }


def _get(path: str, params: dict = None) -> dict:
    resp = requests.get(f"{REDMINE_URL}{path}", headers=_headers(), params=params, verify=False)
    if resp.status_code != 200:
        return {"error": f"{resp.status_code} - {resp.text}"}
    return resp.json()


def _post(path: str, payload: dict) -> dict:
    resp = requests.post(f"{REDMINE_URL}{path}", headers=_headers(), json=payload, verify=False)
    if resp.status_code not in (200, 201):
        return {"error": f"{resp.status_code} - {resp.text}"}
    return resp.json()


def _put(path: str, payload: dict) -> dict:
    resp = requests.put(f"{REDMINE_URL}{path}", headers=_headers(), json=payload, verify=False)
    if resp.status_code not in (200, 204):
        return {"error": f"{resp.status_code} - {resp.text}"}
    return {"message": "更新成功"}


def _delete(path: str) -> dict:
    resp = requests.delete(f"{REDMINE_URL}{path}", headers=_headers(), verify=False)
    if resp.status_code not in (200, 204):
        return {"error": f"{resp.status_code} - {resp.text}"}
    return {"message": "删除成功"}


# ============================================================
# Issue 操作
# ============================================================

# @AI_GENERATED: Kiro v1.0
@mcp.tool()
def list_issues(project_id: str = "", status: str = "open", assigned_to_id: str = "",
                tracker_id: str = "", fixed_version_id: str = "",
                limit: int = 25, offset: int = 0, sort: str = "") -> str:
    """
    查询 Issue 列表。
    参数:
      project_id - 项目标识(ID或别名,可选)
      status - 状态过滤: open/closed/*(全部), 默认open
      assigned_to_id - 指派人ID(可选, "me"表示当前用户)
      tracker_id - 跟踪器ID(可选)
      fixed_version_id - 目标版本ID(可选)
      limit - 每页数量(默认25,最大100)
      offset - 偏移量
      sort - 排序字段(如 "updated_on:desc")
    返回: Issue列表
    """
    params = {"limit": min(limit, 100), "offset": offset, "status_id": status}
    if project_id:
        params["project_id"] = project_id
    if assigned_to_id:
        params["assigned_to_id"] = assigned_to_id
    if tracker_id:
        params["tracker_id"] = tracker_id
    if fixed_version_id:
        params["fixed_version_id"] = fixed_version_id
    if sort:
        params["sort"] = sort
    return json.dumps(_get("/issues.json", params), ensure_ascii=False, indent=2)
# @AI_GENERATED: end


@mcp.tool()
def get_issue(issue_id: int, include: str = "") -> str:
    """
    获取单个 Issue 详情。
    参数:
      issue_id - Issue ID
      include - 附加信息(逗号分隔): children,attachments,relations,changesets,journals,watchers,allowed_statuses
    返回: Issue详细信息
    """
    params = {}
    if include:
        params["include"] = include
    return json.dumps(_get(f"/issues/{issue_id}.json", params), ensure_ascii=False, indent=2)


@mcp.tool()
def create_issue(project_id: str, subject: str, description: str = "",
                 tracker_id: int = 0, status_id: int = 0, priority_id: int = 0,
                 assigned_to_id: int = 0, category_id: int = 0,
                 fixed_version_id: int = 0, parent_issue_id: int = 0,
                 start_date: str = "", due_date: str = "",
                 estimated_hours: float = 0, custom_fields: str = "") -> str:
    """
    创建新 Issue。
    参数:
      project_id - 项目标识(必填)
      subject - 主题(必填)
      description - 描述(支持Textile/Markdown)
      tracker_id - 跟踪器ID
      status_id - 状态ID
      priority_id - 优先级ID
      assigned_to_id - 指派人ID
      category_id - 类别ID
      fixed_version_id - 目标版本ID
      parent_issue_id - 父Issue ID
      start_date - 开始日期(YYYY-MM-DD)
      due_date - 截止日期(YYYY-MM-DD)
      estimated_hours - 预估工时
      custom_fields - 自定义字段JSON, 如 '[{"id":1,"value":"v1"}]'
    返回: 创建的Issue信息
    """
    issue = {"project_id": project_id, "subject": subject}
    if description:
        issue["description"] = description
    for key, val in [("tracker_id", tracker_id), ("status_id", status_id),
                     ("priority_id", priority_id), ("assigned_to_id", assigned_to_id),
                     ("category_id", category_id), ("fixed_version_id", fixed_version_id),
                     ("parent_issue_id", parent_issue_id)]:
        if val:
            issue[key] = val
    if start_date:
        issue["start_date"] = start_date
    if due_date:
        issue["due_date"] = due_date
    if estimated_hours > 0:
        issue["estimated_hours"] = estimated_hours
    if custom_fields:
        issue["custom_fields"] = json.loads(custom_fields)
    return json.dumps(_post("/issues.json", {"issue": issue}), ensure_ascii=False, indent=2)


@mcp.tool()
def update_issue(issue_id: int, subject: str = "", description: str = "",
                 status_id: int = 0, priority_id: int = 0,
                 assigned_to_id: int = 0, fixed_version_id: int = 0,
                 start_date: str = "", due_date: str = "",
                 estimated_hours: float = 0, done_ratio: int = -1,
                 notes: str = "", custom_fields: str = "") -> str:
    """
    更新 Issue。
    参数:
      issue_id - Issue ID(必填)
      subject - 新主题
      description - 新描述
      status_id - 新状态ID
      priority_id - 新优先级ID
      assigned_to_id - 新指派人ID
      fixed_version_id - 新目标版本ID
      start_date - 新开始日期
      due_date - 新截止日期
      estimated_hours - 新预估工时
      done_ratio - 完成百分比(0-100)
      notes - 备注(添加到日志)
      custom_fields - 自定义字段JSON
    返回: 更新结果
    """
    issue = {}
    if subject:
        issue["subject"] = subject
    if description:
        issue["description"] = description
    for key, val in [("status_id", status_id), ("priority_id", priority_id),
                     ("assigned_to_id", assigned_to_id), ("fixed_version_id", fixed_version_id)]:
        if val:
            issue[key] = val
    if start_date:
        issue["start_date"] = start_date
    if due_date:
        issue["due_date"] = due_date
    if estimated_hours > 0:
        issue["estimated_hours"] = estimated_hours
    if done_ratio >= 0:
        issue["done_ratio"] = done_ratio
    if notes:
        issue["notes"] = notes
    if custom_fields:
        issue["custom_fields"] = json.loads(custom_fields)
    return json.dumps(_put(f"/issues/{issue_id}.json", {"issue": issue}), ensure_ascii=False, indent=2)


@mcp.tool()
def delete_issue(issue_id: int) -> str:
    """
    删除 Issue。
    参数: issue_id - Issue ID
    返回: 删除结果
    """
    return json.dumps(_delete(f"/issues/{issue_id}.json"), ensure_ascii=False, indent=2)


# ============================================================
# 项目操作
# ============================================================

@mcp.tool()
def list_projects(limit: int = 25, offset: int = 0) -> str:
    """
    查询项目列表。
    参数: limit - 每页数量, offset - 偏移量
    返回: 项目列表
    """
    return json.dumps(_get("/projects.json", {"limit": limit, "offset": offset}), ensure_ascii=False, indent=2)


@mcp.tool()
def get_project(project_id: str, include: str = "") -> str:
    """
    获取项目详情。
    参数:
      project_id - 项目ID或别名
      include - 附加信息: trackers,issue_categories,enabled_modules,time_entry_activities,issue_custom_fields
    返回: 项目详情
    """
    params = {}
    if include:
        params["include"] = include
    return json.dumps(_get(f"/projects/{project_id}.json", params), ensure_ascii=False, indent=2)


# ============================================================
# 用户与成员
# ============================================================

@mcp.tool()
def get_current_user() -> str:
    """获取当前API Key对应的用户信息。"""
    return json.dumps(_get("/users/current.json"), ensure_ascii=False, indent=2)


@mcp.tool()
def list_users(status: int = 1, limit: int = 25, offset: int = 0) -> str:
    """
    查询用户列表(需管理员权限)。
    参数: status - 用户状态(0=匿名,1=活跃,2=已注册,3=已锁定), limit, offset
    返回: 用户列表
    """
    return json.dumps(_get("/users.json", {"status": status, "limit": limit, "offset": offset}),
                      ensure_ascii=False, indent=2)


@mcp.tool()
# @AI_GENERATED: Kiro v1.0
def list_memberships(project_id: str) -> str:
    """
    查询项目成员列表。
    参数: project_id - 项目ID或别名
    返回: 成员列表(含角色)
    """
    all_members = []
    offset = 0
    limit = 100
    while True:
        data = _get(f"/projects/{project_id}/memberships.json", {"limit": limit, "offset": offset})
        if "error" in data:
            return json.dumps(data, ensure_ascii=False, indent=2)
        members = data.get("memberships", [])
        all_members.extend(members)
        total = data.get("total_count", 0)
        if offset + limit >= total or not members:
            break
        offset += limit

    lines = [f"SUCCESS - Members for project {project_id} (total {len(all_members)}):"]
    for m in all_members:
        user = m.get("user") or m.get("group", {})
        uid = user.get("id", "?")
        name = user.get("name", "?")
        roles = ", ".join(r["name"] for r in m.get("roles", []))
        lines.append(f"  ID: {uid}, Name: {name}, Roles: {roles}")
    return "\n".join(lines)
# @AI_GENERATED: end


# ============================================================
# 版本管理
# ============================================================

@mcp.tool()
def list_versions(project_id: str) -> str:
    """
    查询项目版本列表。
    参数: project_id - 项目ID或别名
    返回: 版本列表
    """
    return json.dumps(_get(f"/projects/{project_id}/versions.json"), ensure_ascii=False, indent=2)


# @AI_GENERATED: Kiro v1.0
@mcp.tool()
def get_version(version_id: int) -> str:
    """
    通过版本ID获取版本详情。
    参数: version_id - 版本ID
    返回: 版本详细信息
    """
    return json.dumps(_get(f"/versions/{version_id}.json"), ensure_ascii=False, indent=2)


# 平台Sprint名称→ID缓存（项目148: Universal SCADA）
_SPRINT_NAME_CACHE: dict[str, int] = {}


def _ensure_sprint_cache(project_id: str = "universal-scada") -> None:
    """按需加载项目版本列表到缓存，仅在缓存为空时执行一次。"""
    if _SPRINT_NAME_CACHE:
        return
    offset = 0
    limit = 100
    while True:
        data = _get(f"/projects/{project_id}/versions.json", {"limit": limit, "offset": offset})
        if "error" in data:
            break
        versions = data.get("versions", [])
        for v in versions:
            _SPRINT_NAME_CACHE[v["name"]] = v["id"]
        total = data.get("total_count", 0)
        if offset + limit >= total or not versions:
            break
        offset += limit


@mcp.tool()
def find_version_by_name(name: str, project_id: str = "universal-scada") -> str:
    """
    通过版本名称查找版本ID（使用缓存，首次调用会加载项目全部版本）。
    参数:
      name - 版本名称，支持精确匹配和模糊匹配（如 "Sprint2026-04" 可匹配 "平台Sprint2026-04"）
      project_id - 项目标识(默认 universal-scada)
    返回: 匹配的版本信息（ID和名称）
    """
    _ensure_sprint_cache(project_id)

    # 精确匹配
    if name in _SPRINT_NAME_CACHE:
        vid = _SPRINT_NAME_CACHE[name]
        return json.dumps({"id": vid, "name": name, "match": "exact"}, ensure_ascii=False, indent=2)

    # 模糊匹配：名称包含搜索词
    matches = [(n, vid) for n, vid in _SPRINT_NAME_CACHE.items() if name in n]
    if len(matches) == 1:
        n, vid = matches[0]
        return json.dumps({"id": vid, "name": n, "match": "fuzzy"}, ensure_ascii=False, indent=2)
    if len(matches) > 1:
        results = [{"id": vid, "name": n} for n, vid in matches]
        return json.dumps({"matches": results, "count": len(results), "hint": "多个匹配，请提供更精确的名称"},
                          ensure_ascii=False, indent=2)

    return json.dumps({"error": f"未找到名称包含 '{name}' 的版本", "cache_size": len(_SPRINT_NAME_CACHE)},
                      ensure_ascii=False, indent=2)


@mcp.tool()
def refresh_version_cache(project_id: str = "universal-scada") -> str:
    """
    强制刷新版本名称缓存（当有新版本创建后使用）。
    参数: project_id - 项目标识(默认 universal-scada)
    返回: 缓存刷新结果
    """
    _SPRINT_NAME_CACHE.clear()
    _ensure_sprint_cache(project_id)
    return json.dumps({"message": "缓存已刷新", "cache_size": len(_SPRINT_NAME_CACHE)}, ensure_ascii=False, indent=2)
# @AI_GENERATED: end


# @AI_GENERATED: Kiro v1.0
@mcp.tool()
def list_all_sprints(status: str = "", limit: int = 100) -> str:
    """
    获取所有项目的所有目标Sprint(版本)列表。
    参数:
      status - 版本状态过滤(可选): open/locked/closed, 默认返回全部
      limit - 每个项目获取的最大版本数(默认100)
    返回: 所有项目的Sprint列表, 按项目分组
    """
    # 先获取所有项目
    all_projects = []
    offset = 0
    while True:
        data = _get("/projects.json", {"limit": 100, "offset": offset})
        if "error" in data:
            return json.dumps(data, ensure_ascii=False, indent=2)
        projects = data.get("projects", [])
        if not projects:
            break
        all_projects.extend(projects)
        if len(projects) < 100:
            break
        offset += 100

    # 遍历每个项目获取版本
    all_sprints = []
    for proj in all_projects:
        pid = proj.get("identifier") or proj.get("id")
        data = _get(f"/projects/{pid}/versions.json", {"limit": limit})
        if "error" in data:
            continue
        versions = data.get("versions", [])
        for v in versions:
            if status and v.get("status") != status:
                continue
            v["project"] = {"id": proj["id"], "name": proj["name"], "identifier": proj.get("identifier", "")}
            all_sprints.append(v)

    return json.dumps({"total_count": len(all_sprints), "sprints": all_sprints}, ensure_ascii=False, indent=2)
# @AI_GENERATED: end


@mcp.tool()
def create_version(project_id: str, name: str, status: str = "open",
                   sharing: str = "none", due_date: str = "", description: str = "") -> str:
    """
    创建项目版本。
    参数:
      project_id - 项目ID或别名
      name - 版本名称
      status - 状态: open/locked/closed
      sharing - 共享范围: none/descendants/hierarchy/tree/system
      due_date - 截止日期(YYYY-MM-DD)
      description - 描述
    返回: 创建的版本信息
    """
    version = {"name": name, "status": status, "sharing": sharing}
    if due_date:
        version["due_date"] = due_date
    if description:
        version["description"] = description
    return json.dumps(_post(f"/projects/{project_id}/versions.json", {"version": version}),
                      ensure_ascii=False, indent=2)


# ============================================================
# 时间记录
# ============================================================

@mcp.tool()
def list_time_entries(project_id: str = "", issue_id: int = 0,
                      user_id: int = 0, from_date: str = "", to_date: str = "",
                      limit: int = 25, offset: int = 0) -> str:
    """
    查询时间记录。
    参数:
      project_id - 项目ID(可选)
      issue_id - Issue ID(可选)
      user_id - 用户ID(可选)
      from_date - 起始日期(YYYY-MM-DD)
      to_date - 截止日期(YYYY-MM-DD)
      limit, offset - 分页
    返回: 时间记录列表
    """
    params = {"limit": limit, "offset": offset}
    if project_id:
        params["project_id"] = project_id
    if issue_id:
        params["issue_id"] = issue_id
    if user_id:
        params["user_id"] = user_id
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    return json.dumps(_get("/time_entries.json", params), ensure_ascii=False, indent=2)


@mcp.tool()
def create_time_entry(issue_id: int = 0, project_id: str = "",
                      hours: float = 0, activity_id: int = 0,
                      comments: str = "", spent_on: str = "") -> str:
    """
    创建时间记录。
    参数:
      issue_id - Issue ID(与project_id二选一)
      project_id - 项目ID(与issue_id二选一)
      hours - 工时(必填)
      activity_id - 活动类型ID
      comments - 备注
      spent_on - 日期(YYYY-MM-DD,默认今天)
    返回: 创建的时间记录
    """
    entry = {"hours": hours}
    if issue_id:
        entry["issue_id"] = issue_id
    if project_id:
        entry["project_id"] = project_id
    if activity_id:
        entry["activity_id"] = activity_id
    if comments:
        entry["comments"] = comments
    if spent_on:
        entry["spent_on"] = spent_on
    return json.dumps(_post("/time_entries.json", {"time_entry": entry}), ensure_ascii=False, indent=2)


# ============================================================
# 查询与元数据
# ============================================================

@mcp.tool()
def list_trackers() -> str:
    """获取所有跟踪器(Bug/Feature/Task等)列表。"""
    return json.dumps(_get("/trackers.json"), ensure_ascii=False, indent=2)


@mcp.tool()
def list_issue_statuses() -> str:
    """获取所有Issue状态列表。"""
    return json.dumps(_get("/issue_statuses.json"), ensure_ascii=False, indent=2)


@mcp.tool()
def list_issue_priorities() -> str:
    """获取所有Issue优先级列表。"""
    return json.dumps(_get("/enumerations/issue_priorities.json"), ensure_ascii=False, indent=2)


@mcp.tool()
def search_redmine(query: str, project_id: str = "", scope: str = "",
                   limit: int = 25, offset: int = 0) -> str:
    """
    全文搜索 Redmine。
    参数:
      query - 搜索关键词(必填)
      project_id - 限定项目(可选)
      scope - 搜索范围(可选): issues,news,documents,changesets,wiki_pages
      limit, offset - 分页
    返回: 搜索结果
    """
    params = {"q": query, "limit": limit, "offset": offset}
    if project_id:
        params["project_id"] = project_id
    if scope:
        params["scope"] = scope
    path = f"/projects/{project_id}/search.json" if project_id else "/search.json"
    return json.dumps(_get(path, params), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
# @AI_GENERATED: end
