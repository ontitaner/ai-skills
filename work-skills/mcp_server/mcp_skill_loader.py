# @AI_GENERATED: Kiro v1.0
"""
Skill Loader MCP Server
按领域/场景匹配并加载工艺 Skill，为 Agent 提供结构化的领域知识和操作规程。
"""

import os
import json
import glob
from typing import Optional

import yaml
from mcp.server.fastmcp import FastMCP

SKILLS_DIR = os.environ.get("SKILLS_DIR", os.path.join(os.path.dirname(__file__), "..", "skills"))

mcp = FastMCP("skill-loader")


def _load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_text(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _scan_skills() -> list[dict]:
    """扫描 skills 目录，返回所有 skill 的元信息列表。"""
    results = []
    for skill_yaml in glob.glob(os.path.join(SKILLS_DIR, "*/skill.yaml")):
        meta = _load_yaml(skill_yaml)
        meta["_dir"] = os.path.dirname(skill_yaml)
        results.append(meta)
    return results


@mcp.tool()
def list_skills(domain: Optional[str] = None) -> str:
    """
    列出所有可用的 Skill，可按领域过滤。

    Args:
        domain: 可选，按领域过滤（如 wind / solar / storage）

    Returns:
        JSON 格式的 Skill 元信息列表
    """
    skills = _scan_skills()
    if domain:
        skills = [s for s in skills if s.get("domain", "").lower() == domain.lower()]
    # 去掉内部字段
    output = []
    for s in skills:
        output.append({
            "name": s.get("name"),
            "display_name": s.get("display_name"),
            "domain": s.get("domain"),
            "scenarios": s.get("scenarios", []),
            "keywords": s.get("keywords", []),
            "version": s.get("version"),
            "tools_required": s.get("tools_required", []),
        })
    return json.dumps(output, ensure_ascii=False, indent=2)


@mcp.tool()
def match_skill(query: str) -> str:
    """
    根据用户意图描述，匹配最相关的 Skill。
    匹配逻辑：关键词命中 + 场景命中，返回得分最高的 Skill。

    Args:
        query: 用户意图描述，如 "风电SCADA版本升级"

    Returns:
        JSON 格式的匹配结果，包含 skill 名称和匹配得分
    """
    skills = _scan_skills()
    query_lower = query.lower()
    scored = []
    for s in skills:
        score = 0
        for kw in s.get("keywords", []):
            if kw.lower() in query_lower:
                score += 2
        for sc in s.get("scenarios", []):
            if sc.lower() in query_lower:
                score += 3
        if s.get("domain", "").lower() in query_lower:
            score += 1
        if s.get("display_name", "").lower() in query_lower:
            score += 2
        if score > 0:
            scored.append({"name": s.get("name"), "display_name": s.get("display_name"), "score": score})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return json.dumps(scored[:5], ensure_ascii=False, indent=2)


@mcp.tool()
def get_skill(name: str, layers: Optional[str] = None) -> str:
    """
    加载指定 Skill 的完整内容或指定层级。

    Args:
        name: Skill 名称（目录名），如 wind_scada
        layers: 可选，逗号分隔的层级名，如 "knowledge,operation,decision"
                不传则返回全部层级

    Returns:
        JSON 格式的 Skill 内容，按层级组织
    """
    skill_dir = os.path.join(SKILLS_DIR, name)
    if not os.path.isdir(skill_dir):
        return json.dumps({"error": f"Skill '{name}' not found"}, ensure_ascii=False)

    meta = _load_yaml(os.path.join(skill_dir, "skill.yaml"))

    all_layers = {
        "knowledge": ("knowledge.md", "text"),
        "operation": ("operation.yaml", "yaml"),
        "decision": ("decision.json", "json"),
        "quality": ("quality.md", "text"),
        "experience": ("experience.md", "text"),
    }

    requested = all_layers.keys()
    if layers:
        requested = [l.strip() for l in layers.split(",")]

    result = {"name": meta.get("name"), "version": meta.get("version"), "layers": {}}
    for layer_name in requested:
        if layer_name not in all_layers:
            continue
        filename, fmt = all_layers[layer_name]
        filepath = os.path.join(skill_dir, filename)
        if fmt == "yaml":
            result["layers"][layer_name] = _load_yaml(filepath) if os.path.exists(filepath) else {}
        elif fmt == "json":
            result["layers"][layer_name] = _load_json(filepath)
        else:
            result["layers"][layer_name] = _load_text(filepath)

    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def get_workflow(name: str, scenario: str) -> str:
    """
    获取指定 Skill 中某个场景的操作流程（SOP）。
    直接返回可执行的 tool 调用序列，Agent 可按步骤执行。

    Args:
        name: Skill 名称，如 wind_scada
        scenario: 场景名称，如 "版本升级"

    Returns:
        JSON 格式的工作流步骤列表，包含 tool 名称、参数和检查条件
    """
    skill_dir = os.path.join(SKILLS_DIR, name)
    op_file = os.path.join(skill_dir, "operation.yaml")
    if not os.path.exists(op_file):
        return json.dumps({"error": f"No operation.yaml in skill '{name}'"}, ensure_ascii=False)

    operation = _load_yaml(op_file)
    workflows = operation.get("workflows", {})

    if scenario not in workflows:
        available = list(workflows.keys())
        return json.dumps({"error": f"Scenario '{scenario}' not found", "available": available}, ensure_ascii=False)

    return json.dumps(workflows[scenario], ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
# @AI_GENERATED: end
