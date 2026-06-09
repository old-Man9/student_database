"""
db 模块 - 数据库连接管理

提供:
- get_connection()  : 上下文管理器，自动获取/归还连接
- execute_query()   : 执行查询，返回结果集
- execute_update()  : 增/删/改，返回影响行数
- execute_insert()  : 插入，返回自增 ID
- init_database()   : 初始化数据库
"""

from .connection import (
    get_connection,
    execute_query,
    execute_update,
    execute_insert,
    init_database,
    DatabaseConfig,
)
