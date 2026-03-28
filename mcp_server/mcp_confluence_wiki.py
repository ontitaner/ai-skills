#!/usr/bin/env python3
# @AI_GENERATED: Kiro v1.0
"""
Confluence MCP Server - 适配自建 Confluence Server (7.x)
支持：读取、创建、更新、搜索 Wiki 页面
扩展：下载页面为Markdown(含图片)、上传Markdown至Wiki页面
使用 Basic Auth 认证
"""

import json
import os
import re
import html as html_module
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urlparse
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("confluence-wiki")

CONFLUENCE_URL = os.environ.get("CONFLUENCE_URL", "").rstrip("/")
CONFLUENCE_USERNAME = os.environ.get("CONFLUENCE_USERNAME", "")
CONFLUENCE_PASSWORD = os.environ.get("CONFLUENCE_PASSWORD", "")


def _auth():
    return HTTPBasicAuth(CONFLUENCE_USERNAME, CONFLUENCE_PASSWORD)


def _headers():
    return {"Content-Type": "application/json", "Accept": "application/json"}


def _strip_html(html: str) -> str:
    text = re.sub(r'<[^>]+>', '', html)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ============================================================
# 原有基础 Tools
# ============================================================

@mcp.tool()
def get_page(page_id: str | int) -> str:
    """
    读取 Confluence 页面内容。
    参数: page_id - 页面ID
    返回: 页面标题、内容（纯文本）、空间信息等
    """
    page_id = str(page_id)
    url = f"{CONFLUENCE_URL}/rest/api/content/{page_id}"
    params = {"expand": "body.storage,space,version"}
    resp = requests.get(url, auth=_auth(), headers=_headers(), params=params, verify=False)
    if resp.status_code != 200:
        return f"Error: {resp.status_code} - {resp.text}"
    data = resp.json()
    html_content = data.get("body", {}).get("storage", {}).get("value", "")
    result = {
        "id": data["id"], "title": data["title"],
        "space": data.get("space", {}).get("key", ""),
        "version": data.get("version", {}).get("number", 0),
        "content": _strip_html(html_content),
        "content_html": html_content[:2000] + "..." if len(html_content) > 2000 else html_content,
    }
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def create_page(space_key: str, title: str, content: str, parent_id: str = "") -> str:
    """
    在 Confluence 中创建新页面。
    参数: space_key - 空间标识, title - 页面标题, content - HTML内容, parent_id - 父页面ID(可选)
    """
    url = f"{CONFLUENCE_URL}/rest/api/content"
    payload = {
        "type": "page", "title": title, "space": {"key": space_key},
        "body": {"storage": {"value": content, "representation": "storage"}}
    }
    if parent_id:
        payload["ancestors"] = [{"id": parent_id}]
    resp = requests.post(url, auth=_auth(), headers=_headers(), json=payload, verify=False)
    if resp.status_code not in (200, 201):
        return f"Error: {resp.status_code} - {resp.text}"
    data = resp.json()
    return json.dumps({
        "id": data["id"], "title": data["title"],
        "url": f"{CONFLUENCE_URL}/pages/viewpage.action?pageId={data['id']}",
        "message": "页面创建成功"
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def update_page(page_id: str | int, title: str, content: str) -> str:
    """
    更新 Confluence 页面内容。
    参数: page_id - 页面ID, title - 页面标题, content - 新HTML内容
    """
    page_id = str(page_id)
    get_url = f"{CONFLUENCE_URL}/rest/api/content/{page_id}"
    get_resp = requests.get(get_url, auth=_auth(), headers=_headers(),
                            params={"expand": "version"}, verify=False)
    if get_resp.status_code != 200:
        return f"Error getting page: {get_resp.status_code} - {get_resp.text}"
    current_version = get_resp.json()["version"]["number"]
    payload = {
        "id": page_id, "type": "page", "title": title,
        "version": {"number": current_version + 1},
        "body": {"storage": {"value": content, "representation": "storage"}}
    }
    resp = requests.put(get_url, auth=_auth(), headers=_headers(), json=payload, verify=False)
    if resp.status_code != 200:
        return f"Error: {resp.status_code} - {resp.text}"
    data = resp.json()
    return json.dumps({
        "id": data["id"], "title": data["title"],
        "version": data["version"]["number"], "message": "页面更新成功"
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def search_pages(query: str, space_key: str = "", limit: int = 10) -> str:
    """
    搜索 Confluence 页面。
    参数: query - 搜索关键词, space_key - 空间(可选), limit - 数量(默认10)
    """
    cql = f'text ~ "{query}"'
    if space_key:
        cql += f' AND space = "{space_key}"'
    url = f"{CONFLUENCE_URL}/rest/api/content/search"
    params = {"cql": cql, "limit": limit}
    resp = requests.get(url, auth=_auth(), headers=_headers(), params=params, verify=False)
    if resp.status_code != 200:
        return f"Error: {resp.status_code} - {resp.text}"
    data = resp.json()
    results = [{"id": item["id"], "title": item["title"], "type": item["type"],
                "url": f"{CONFLUENCE_URL}/pages/viewpage.action?pageId={item['id']}"}
               for item in data.get("results", [])]
    return json.dumps({"total": data.get("totalSize", len(results)), "results": results},
                      ensure_ascii=False, indent=2)


# ============================================================
# 扩展 Skill: 下载页面为 Markdown（含图片）
# ============================================================

def _fetch_attachments(page_id: str) -> dict:
    """获取页面附件列表，返回 filename->download_url 映射。"""
    url = f"{CONFLUENCE_URL}/rest/api/content/{page_id}/child/attachment"
    resp = requests.get(url, auth=_auth(), headers=_headers(),
                        params={"limit": 200}, verify=False)
    if resp.status_code != 200:
        return {}
    attachments = {}
    for item in resp.json().get("results", []):
        dl = item.get("_links", {}).get("download", "")
        if dl:
            attachments[item["title"]] = CONFLUENCE_URL + dl
    return attachments


def _download_image(img_url: str, save_path: str) -> bool:
    """下载图片到本地。"""
    try:
        resp = requests.get(img_url, auth=_auth(), verify=False, stream=True)
        if resp.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
            return True
    except Exception:
        pass
    return False


def _html_to_markdown(html_str: str, attachments: dict, img_dir: str, img_rel_dir: str) -> str:
    """将 Confluence storage HTML 转换为 Markdown，同时下载图片。"""
    text = html_str
    img_counter = [0]

    # Confluence ac:image 宏
    def replace_ac_image(m):
        fn_match = re.search(r'ri:filename="([^"]+)"', m.group(0))
        if fn_match:
            filename = fn_match.group(1)
            if filename in attachments:
                img_counter[0] += 1
                ext = os.path.splitext(filename)[1] or ".png"
                local_name = f"img_{img_counter[0]:03d}{ext}"
                local_path = os.path.join(img_dir, local_name)
                if _download_image(attachments[filename], local_path):
                    return f"\n![{filename}]({img_rel_dir}/{local_name})\n"
            return f"\n![{filename}]()\n"
        return "\n[图片]\n"
    text = re.sub(r'<ac:image[^>]*>.*?</ac:image>', replace_ac_image, text, flags=re.DOTALL)

    # 标准 <img> 标签
    def replace_img_tag(m):
        src = re.search(r'src="([^"]+)"', m.group(0))
        if src:
            img_url = src.group(1)
            if not img_url.startswith("http"):
                img_url = CONFLUENCE_URL + img_url
            img_counter[0] += 1
            ext = os.path.splitext(urlparse(img_url).path)[1] or ".png"
            local_name = f"img_{img_counter[0]:03d}{ext}"
            local_path = os.path.join(img_dir, local_name)
            if _download_image(img_url, local_path):
                alt = re.search(r'alt="([^"]*)"', m.group(0))
                return f"\n![{alt.group(1) if alt else local_name}]({img_rel_dir}/{local_name})\n"
        return "\n[图片]\n"
    text = re.sub(r'<img[^>]*/?>', replace_img_tag, text, flags=re.DOTALL)

    # 代码块宏
    def replace_code_macro(m):
        lang_m = re.search(r'<ac:parameter ac:name="language">([^<]+)</ac:parameter>', m.group(0), re.DOTALL)
        lang = lang_m.group(1).strip() if lang_m else ""
        cdata_m = re.search(r'<!\[CDATA\[(.*?)\]\]>', m.group(0), re.DOTALL)
        code = cdata_m.group(1) if cdata_m else ""
        return f"\n```{lang}\n{code}\n```\n"
    text = re.sub(r'<ac:structured-macro[^>]*ac:name="code"[^>]*>.*?</ac:structured-macro>',
                  replace_code_macro, text, flags=re.DOTALL)

    # 面板宏 (info/note/warning/tip)
    def replace_panel(m):
        ptype_m = re.search(r'ac:name="(\w+)"', m.group(0))
        ptype = ptype_m.group(1) if ptype_m else "note"
        body_m = re.search(r'<ac:rich-text-body>(.*?)</ac:rich-text-body>', m.group(0), re.DOTALL)
        body = body_m.group(1) if body_m else ""
        return f"\n> **[{ptype.upper()}]** {body}\n"
    text = re.sub(r'<ac:structured-macro[^>]*ac:name="(?:info|note|warning|tip|panel)"[^>]*>.*?</ac:structured-macro>',
                  replace_panel, text, flags=re.DOTALL)

    # 清理剩余 Confluence 宏
    text = re.sub(r'<ac:rich-text-body>(.*?)</ac:rich-text-body>', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'<ac:structured-macro[^>]*>.*?</ac:structured-macro>', '', text, flags=re.DOTALL)
    text = re.sub(r'</?ac:[^>]*>', '', text)
    text = re.sub(r'</?ri:[^>]*>', '', text)

    # 标题
    for i in range(6, 0, -1):
        text = re.sub(rf'<h{i}[^>]*>(.*?)</h{i}>',
                      lambda m, lv=i: '\n' + '#' * lv + ' ' + m.group(1).strip() + '\n',
                      text, flags=re.DOTALL)

    # 表格
    def convert_table(m):
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', m.group(0), re.DOTALL)
        if not rows:
            return ""
        md_rows = []
        for idx, row in enumerate(rows):
            cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.DOTALL)
            cells_text = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
            md_rows.append("| " + " | ".join(cells_text) + " |")
            if idx == 0:
                md_rows.append("| " + " | ".join(["---"] * len(cells_text)) + " |")
        return "\n" + "\n".join(md_rows) + "\n"
    text = re.sub(r'<table[^>]*>.*?</table>', convert_table, text, flags=re.DOTALL)

    # 内联格式
    text = re.sub(r'<(?:strong|b)[^>]*>(.*?)</(?:strong|b)>', r'**\1**', text, flags=re.DOTALL)
    text = re.sub(r'<(?:em|i)[^>]*>(.*?)</(?:em|i)>', r'*\1*', text, flags=re.DOTALL)
    text = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', text, flags=re.DOTALL)
    text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.DOTALL)

    # 列表
    def convert_ol(m):
        items = re.findall(r'<li[^>]*>(.*?)</li>', m.group(0), re.DOTALL)
        return "\n" + "\n".join(f"{i}. {re.sub(r'<[^>]+>', '', t).strip()}" for i, t in enumerate(items, 1)) + "\n"
    def convert_ul(m):
        items = re.findall(r'<li[^>]*>(.*?)</li>', m.group(0), re.DOTALL)
        return "\n" + "\n".join(f"- {re.sub(r'<[^>]+>', '', t).strip()}" for t in items) + "\n"
    text = re.sub(r'<ol[^>]*>(.*?)</ol>', convert_ol, text, flags=re.DOTALL)
    text = re.sub(r'<ul[^>]*>(.*?)</ul>', convert_ul, text, flags=re.DOTALL)

    # 段落/换行
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n', text, flags=re.DOTALL)
    text = re.sub(r'<div[^>]*>(.*?)</div>', r'\n\1\n', text, flags=re.DOTALL)
    text = re.sub(r'<hr\s*/?>', '\n---\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = html_module.unescape(text)
    text = re.sub(r'[ \t]+\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


@mcp.tool()
def download_page_as_markdown(page_id: str | int, output_dir: str = "wiki_pages") -> str:
    """
    下载 Confluence 页面为 Markdown 文件（含图片）。
    参数:
      page_id - 页面ID
      output_dir - 输出目录（默认 wiki_pages）
    返回: 保存的文件路径、图片数量等信息
    """
    page_id = str(page_id)
    url = f"{CONFLUENCE_URL}/rest/api/content/{page_id}"
    resp = requests.get(url, auth=_auth(), headers=_headers(),
                        params={"expand": "body.storage,space,version"}, verify=False)
    if resp.status_code != 200:
        return f"Error: {resp.status_code} - {resp.text}"

    data = resp.json()
    title = data["title"]
    html_content = data.get("body", {}).get("storage", {}).get("value", "")
    space_key = data.get("space", {}).get("key", "")
    version = data.get("version", {}).get("number", 0)

    safe_title = re.sub(r'[\\/*?:"<>|]', '_', title)
    img_dir = os.path.join(output_dir, f"{safe_title}_images")
    img_rel_dir = f"{safe_title}_images"

    os.makedirs(output_dir, exist_ok=True)
    attachments = _fetch_attachments(page_id)
    md_content = _html_to_markdown(html_content, attachments, img_dir, img_rel_dir)

    filepath = os.path.join(output_dir, f"{safe_title}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"> Page ID: {page_id} | Space: {space_key} | Version: {version}\n\n")
        f.write(md_content + "\n")

    img_count = len(os.listdir(img_dir)) if os.path.isdir(img_dir) else 0
    return json.dumps({
        "page_id": page_id, "title": title, "filepath": filepath,
        "images_downloaded": img_count, "attachments_found": len(attachments),
        "message": f"页面已保存至 {filepath}"
    }, ensure_ascii=False, indent=2)


# ============================================================
# 扩展 Skill: 上传 Markdown 至 Wiki 页面（含图片）
# ============================================================

def _xml_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _escape_raw_angles(text: str) -> str:
    """转义非HTML标签的尖括号。"""
    valid_tag = re.compile(
        r'</?(?:p|strong|em|code|a|ul|ol|li|table|tr|th|td|hr|br|h[1-6]|'
        r'ac:[a-z-]+|ri:[a-z-]+)[^>]*/?>',
        re.IGNORECASE
    )
    result, last_end = [], 0
    for m in valid_tag.finditer(text):
        gap = text[last_end:m.start()].replace("<", "&lt;").replace(">", "&gt;")
        result.append(gap)
        result.append(m.group(0))
        last_end = m.end()
    result.append(text[last_end:].replace("<", "&lt;").replace(">", "&gt;"))
    return "".join(result)


def _md_inline_format(text: str, uploaded_images: set) -> str:
    """Markdown 行内格式转 Confluence HTML。"""
    def replace_img(m):
        alt, src = m.group(1), m.group(2)
        fn = os.path.basename(src)
        if fn in uploaded_images:
            return (f'<ac:image ac:alt="{_xml_escape(alt)}">'
                    f'<ri:attachment ri:filename="{fn}"/></ac:image>')
        return f'[图片: {alt}]'
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_img, text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    def replace_code(m):
        return f'<code>{_xml_escape(m.group(1))}</code>'
    text = re.sub(r'`([^`]+)`', replace_code, text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    return text


def _split_table_cells(line: str) -> list:
    """分割表格行，正确处理反引号内的管道符。"""
    line = line.strip().strip("|")
    cells, current, in_bt = [], "", False
    for i, ch in enumerate(line):
        if ch == '`':
            in_bt = not in_bt
            current += ch
        elif ch == '\\' and i + 1 < len(line) and line[i + 1] == '|':
            current += '|'
        elif ch == '|' and not in_bt:
            cells.append(current.strip())
            current = ""
        else:
            current += ch
    cells.append(current.strip())
    return cells


def _flush_table(rows: list, uploaded_images: set) -> str:
    """表格行转 Confluence HTML table。"""
    if not rows:
        return ""
    num_cols = max(len(r) for r in rows)
    html = '<table><colgroup>' + '<col/>' * num_cols + '</colgroup><tbody>'
    for idx, row in enumerate(rows):
        html += '<tr>'
        tag = 'th' if idx == 0 else 'td'
        while len(row) < num_cols:
            row.append("")
        for cell in row:
            fmt = _escape_raw_angles(_md_inline_format(cell, uploaded_images))
            html += f'<{tag}><p>{fmt}</p></{tag}>'
        html += '</tr>'
    html += '</tbody></table>'
    return html


def _md_to_confluence_html(md_text: str, uploaded_images: set) -> str:
    """Markdown 全文转 Confluence storage HTML。"""
    lines = md_text.split("\n")
    parts = []
    i = 0
    in_code, code_lang, code_lines = False, "", []
    in_table, table_rows = False, []

    while i < len(lines):
        line = lines[i]

        if line.startswith("> Page ID:"):
            i += 1; continue

        # 代码块
        if line.strip().startswith("```") and not in_code:
            if in_table:
                parts.append(_flush_table(table_rows, uploaded_images)); in_table = False; table_rows = []
            in_code = True; code_lang = line.strip()[3:].strip(); code_lines = []; i += 1; continue
        if line.strip().startswith("```") and in_code:
            in_code = False
            lp = f'<ac:parameter ac:name="language">{code_lang}</ac:parameter>' if code_lang else ''
            parts.append(f'<ac:structured-macro ac:name="code">{lp}'
                         f'<ac:plain-text-body><![CDATA[{chr(10).join(code_lines)}]]></ac:plain-text-body>'
                         f'</ac:structured-macro>')
            i += 1; continue
        if in_code:
            code_lines.append(line); i += 1; continue

        # 水平线
        if line.strip() == "---":
            if in_table:
                parts.append(_flush_table(table_rows, uploaded_images)); in_table = False; table_rows = []
            parts.append("<hr/>"); i += 1; continue

        # 表格
        if line.strip().startswith("|") and line.strip().endswith("|"):
            cells = _split_table_cells(line)
            if all(re.match(r'^[-:]+$', c.strip()) for c in cells if c.strip()):
                i += 1; continue
            if not in_table:
                in_table = True; table_rows = []
            table_rows.append(cells); i += 1; continue
        else:
            if in_table:
                parts.append(_flush_table(table_rows, uploaded_images)); in_table = False; table_rows = []

        if line.strip() == "":
            i += 1; continue

        # 标题
        hm = re.match(r'^(#{1,6})\s+(.+)$', line)
        if hm:
            lv = len(hm.group(1))
            t = _escape_raw_angles(_md_inline_format(hm.group(2), uploaded_images))
            parts.append(f"<h{lv}>{t}</h{lv}>"); i += 1; continue

        # 图片（独立行，支持连续多张）
        if re.match(r'^!\[([^\]]*)\]\(([^)]+)\)\s*$', line):
            while i < len(lines) and re.match(r'^!\[([^\]]*)\]\(([^)]+)\)\s*$', lines[i]):
                m = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)', lines[i])
                alt, src = m.group(1), m.group(2)
                fn = os.path.basename(src)
                if fn in uploaded_images:
                    parts.append(f'<p><ac:image ac:alt="{_xml_escape(alt)}">'
                                 f'<ri:attachment ri:filename="{fn}"/></ac:image></p>')
                else:
                    parts.append(f'<p>[图片: {alt}]</p>')
                i += 1
            continue

        # 无序列表
        if re.match(r'^[-*]\s+', line):
            items = []
            while i < len(lines) and re.match(r'^[-*]\s+', lines[i]):
                t = re.sub(r'^[-*]\s+', '', lines[i])
                items.append(_escape_raw_angles(_md_inline_format(t, uploaded_images)))
                i += 1
            parts.append("<ul>" + "".join(f"<li>{it}</li>" for it in items) + "</ul>"); continue

        # 有序列表
        if re.match(r'^\d+[.)]\s+', line):
            items = []
            while i < len(lines) and re.match(r'^\d+[.)]\s+', lines[i]):
                t = re.sub(r'^\d+[.)]\s+', '', lines[i])
                items.append(_escape_raw_angles(_md_inline_format(t, uploaded_images)))
                i += 1
            parts.append("<ol>" + "".join(f"<li>{it}</li>" for it in items) + "</ol>"); continue

        # 引用
        if line.startswith("> "):
            qt = _escape_raw_angles(_md_inline_format(line[2:], uploaded_images))
            parts.append(f'<ac:structured-macro ac:name="info">'
                         f'<ac:rich-text-body><p>{qt}</p></ac:rich-text-body></ac:structured-macro>')
            i += 1; continue

        # 普通段落
        pt = _escape_raw_angles(_md_inline_format(line, uploaded_images))
        parts.append(f"<p>{pt}</p>"); i += 1

    if in_table:
        parts.append(_flush_table(table_rows, uploaded_images))
    return "\n".join(parts)


def _upload_attachment(page_id: str, filepath: str) -> str | None:
    """上传图片附件到 Confluence 页面。"""
    filename = os.path.basename(filepath)
    url = f"{CONFLUENCE_URL}/rest/api/content/{page_id}/child/attachment"
    check = requests.get(url, auth=_auth(), params={"filename": filename},
                         headers={"Accept": "application/json"}, verify=False)
    existing = check.json().get("results", []) if check.status_code == 200 else []
    with open(filepath, "rb") as f:
        data = f.read()
    upload_url = f"{url}/{existing[0]['id']}/data" if existing else url
    resp = requests.post(upload_url, auth=_auth(),
                         headers={"X-Atlassian-Token": "nocheck"},
                         files={"file": (filename, data, "image/png")}, verify=False)
    return filename if resp.status_code in (200, 201) else None


@mcp.tool()
def upload_markdown_to_page(page_id: str | int, md_file: str, img_dir: str = "") -> str:
    """
    将本地 Markdown 文件上传更新至 Confluence 页面（含图片）。
    参数:
      page_id - 目标页面ID
      md_file - 本地 Markdown 文件路径
      img_dir - 图片目录路径（可选，默认自动推断为 <md文件名>_images）
    返回: 更新结果信息
    """
    page_id = str(page_id)

    if not os.path.isfile(md_file):
        return json.dumps({"error": f"文件不存在: {md_file}"}, ensure_ascii=False)

    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    # 获取页面当前标题
    info_url = f"{CONFLUENCE_URL}/rest/api/content/{page_id}"
    info_resp = requests.get(info_url, auth=_auth(), headers=_headers(),
                             params={"expand": "version"}, verify=False)
    if info_resp.status_code != 200:
        return f"Error: {info_resp.status_code} - {info_resp.text}"
    page_data = info_resp.json()
    title = page_data["title"]
    current_version = page_data["version"]["number"]

    # 自动推断图片目录
    if not img_dir:
        base = os.path.splitext(md_file)[0]
        img_dir = base + "_images"

    # 上传图片
    uploaded_images = set()
    if os.path.isdir(img_dir):
        for img_file in sorted(os.listdir(img_dir)):
            img_path = os.path.join(img_dir, img_file)
            if os.path.isfile(img_path):
                result = _upload_attachment(page_id, img_path)
                if result:
                    uploaded_images.add(result)

    # 跳过标题行
    content_lines = md_content.split("\n")
    start_idx = 0
    for idx, line in enumerate(content_lines):
        if line.startswith("# "):
            start_idx = idx + 1
            break
    body_md = "\n".join(content_lines[start_idx:])

    # 转换并更新
    html_content = _md_to_confluence_html(body_md, uploaded_images)
    payload = {
        "id": page_id, "type": "page", "title": title,
        "version": {"number": current_version + 1},
        "body": {"storage": {"value": html_content, "representation": "storage"}}
    }
    resp = requests.put(info_url, auth=_auth(), headers=_headers(), json=payload, verify=False)
    if resp.status_code != 200:
        return json.dumps({"error": f"更新失败: {resp.status_code}", "detail": resp.text[:500]},
                          ensure_ascii=False)

    new_ver = resp.json()["version"]["number"]
    return json.dumps({
        "page_id": page_id, "title": title,
        "version": f"{current_version} -> {new_ver}",
        "images_uploaded": len(uploaded_images),
        "message": "页面更新成功"
    }, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
# @AI_GENERATED: end
