# @AI_GENERATED: Kiro v1.0
"""扫描 docs/ 目录，自动生成 mkdocs.yml 的 nav 和 docs/index.md，
然后清理 site/、重新构建并启动 mkdocs serve。

脚本位于 mkdocs/scripts/ 子目录，运行时自动切换到 mkdocs/ 目录。
"""

import os
import shutil
import signal
import subprocess
import sys
import time

# 切换工作目录到 mkdocs/ 目录（脚本所在目录的上一级）
MKDOCS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(MKDOCS_ROOT)

DOCS_DIR = "docs"
MKDOCS_YML = "mkdocs.yml"
INDEX_MD = os.path.join(DOCS_DIR, "index.md")
SITE_DIR = "site"
MKDOCS_PID_FILE = ".mkdocs_serve.pid"


def get_title_from_md(filepath: str) -> str:
    """从 Markdown 文件的第一个 # 标题提取标题，否则用文件名。"""
    try:
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("# "):
                    return line[2:].strip()
    except Exception:
        pass
    name = os.path.splitext(os.path.basename(filepath))[0]
    return name.replace("-", " ").replace("_", " ").title()


def scan_docs() -> list[dict]:
    """扫描 docs/ 下所有 .md 文件（排除 index.md），返回 nav 条目列表。"""
    entries = []
    for fname in sorted(os.listdir(DOCS_DIR)):
        if not fname.endswith(".md") or fname == "index.md":
            continue
        filepath = os.path.join(DOCS_DIR, fname)
        title = get_title_from_md(filepath)
        entries.append({"title": title, "file": fname})
    return entries


def generate_mkdocs_yml(entries: list[dict]) -> None:
    """生成 mkdocs.yml，包含 Mermaid 渲染支持。"""
    nav_lines = []
    nav_lines.append("- 首页: index.md")
    for e in entries:
        nav_lines.append(f"- {e['title']}: {e['file']}")

    content = f"""site_name: SCADA 项目文档
docs_dir: docs
site_dir: site
theme:
  name: material
  language: zh
markdown_extensions:
  - tables
  - attr_list
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.tabbed
nav:
{chr(10).join('  ' + line for line in nav_lines)}
"""

    with open(MKDOCS_YML, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"已更新 {MKDOCS_YML}，共 {len(entries)} 篇文档")


def generate_index_md(entries: list[dict]) -> None:
    """生成 docs/index.md 目录索引。"""
    lines = ["# SCADA 项目文档\n", "", "欢迎访问 SCADA 系统技术文档。\n", "", "## 文档列表\n", ""]
    for e in entries:
        lines.append(f"- [{e['title']}]({e['file']})")
    lines.append("")

    with open(INDEX_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"已更新 {INDEX_MD}")


def clean_site() -> None:
    """清理 site/ 构建产物目录。"""
    if os.path.isdir(SITE_DIR):
        shutil.rmtree(SITE_DIR)
        print(f"已清理 {SITE_DIR}/")
    else:
        print(f"{SITE_DIR}/ 不存在，跳过清理")


def build_site() -> bool:
    """运行 mkdocs build 构建站点，返回是否成功。"""
    print("正在构建 mkdocs 站点...")
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--clean",
         "--config-file", os.path.join(MKDOCS_ROOT, MKDOCS_YML)],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("mkdocs build 成功")
        return True
    else:
        print(f"mkdocs build 失败:\n{result.stderr}")
        return False


def _kill_pid(pid: int) -> None:
    """尝试终止指定 PID 的进程。"""
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                           capture_output=True)
        else:
            os.kill(pid, signal.SIGTERM)
    except (ProcessLookupError, OSError):
        pass


def _kill_by_port(port: int) -> None:
    """Windows 上按端口查找并终止占用该端口的进程（兜底清理）。"""
    if sys.platform != "win32":
        return
    try:
        result = subprocess.run(
            ["netstat", "-ano", "-p", "TCP"],
            capture_output=True, text=True,
        )
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                pid = int(parts[-1])
                if pid > 0:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                                   capture_output=True)
                    print(f"已按端口清理残留进程 (PID: {pid}, 端口: {port})")
    except Exception:
        pass


def stop_mkdocs_serve(port: int = 8000) -> None:
    """停止之前启动的 mkdocs serve 进程。

    先按 PID 文件终止，再按端口兜底清理残留进程，确保端口释放。
    """
    # 1. 按 PID 文件终止
    if os.path.isfile(MKDOCS_PID_FILE):
        try:
            with open(MKDOCS_PID_FILE, "r") as f:
                pid = int(f.read().strip())
            _kill_pid(pid)
            print(f"已停止旧的 mkdocs serve 进程 (PID: {pid})")
        except (ValueError, OSError):
            pass
        finally:
            os.remove(MKDOCS_PID_FILE)

    # 2. 按端口兜底清理（防止 detached 进程残留）
    _kill_by_port(port)

    # 3. 等待端口释放
    time.sleep(1)


def start_mkdocs_serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    """后台启动 mkdocs serve 并记录 PID。

    使用 --dirty 关闭（默认即 clean 模式），确保 serve 启动时
    重新加载所有文档，不使用任何缓存。--livereload 保证浏览器
    自动刷新页面。
    """
    stop_mkdocs_serve(port)

    cmd = [sys.executable, "-m", "mkdocs", "serve",
           "--config-file", os.path.join(MKDOCS_ROOT, MKDOCS_YML),
           "--dev-addr", f"{host}:{port}",
           "--livereload"]

    if sys.platform == "win32":
        proc = subprocess.Popen(
            cmd,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.DETACHED_PROCESS,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    with open(MKDOCS_PID_FILE, "w") as f:
        f.write(str(proc.pid))

    print(f"mkdocs serve 已启动 (PID: {proc.pid})，访问 http://{host}:{port}")


def main():
    if not os.path.isdir(DOCS_DIR):
        os.makedirs(DOCS_DIR)
        print(f"已创建 {DOCS_DIR}/ 目录")

    # 1. 同步导航和索引
    entries = scan_docs()
    generate_mkdocs_yml(entries)
    generate_index_md(entries)

    # 2. 清理旧构建
    clean_site()

    # 3. 重新构建
    if not build_site():
        sys.exit(1)

    # 4. 重启 mkdocs serve
    start_mkdocs_serve()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
