# @AI_GENERATED: Kiro v1.0
"""
MySQL MCP Server - 支持 SSL 配置的 MySQL 查询工具
"""
import os
import json
import pymysql
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mysql")

def get_connection():
    ssl_mode = os.environ.get("MYSQL_SSL", "").upper()
    conn_kwargs = {
        "host": os.environ.get("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.environ.get("MYSQL_PORT", "3306")),
        "user": os.environ.get("MYSQL_USER", "root"),
        "password": os.environ.get("MYSQL_PASSWORD", ""),
        "database": os.environ.get("MYSQL_DATABASE", ""),
        "charset": os.environ.get("MYSQL_CHARSET", "utf8mb4"),
    }
    if ssl_mode == "DISABLED":
        conn_kwargs["ssl_disabled"] = True
    return pymysql.connect(**conn_kwargs)

@mcp.tool()
def execute_sql(query: str) -> str:
    """Execute an SQL query on the MySQL server"""
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query)
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    result = [dict(zip(columns, row)) for row in rows]
                    return json.dumps(result, default=str, ensure_ascii=False)
                else:
                    conn.commit()
                    return json.dumps({"affected_rows": cursor.rowcount}, ensure_ascii=False)
        finally:
            conn.close()
    except Exception as e:
        return f"Error executing query: {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
# @AI_GENERATED: end
