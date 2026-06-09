"""
数据库连接模块
- 使用 PyMySQL 驱动连接 MySQL
- 连接池管理，复用连接减少开销
- 参数化查询防止 SQL 注入
"""

import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager


class DatabaseConfig:
    """数据库配置"""
    HOST = 'localhost'
    PORT = 3306
    USER = 'root'
    PASSWORD = 'root'        # MySQL root 密码
    DATABASE = 'student_db'
    CHARSET = 'utf8mb4'
    # 连接池参数
    POOL_SIZE = 5
    CONNECT_TIMEOUT = 5


class DatabasePool:
    """
    简易连接池
    - 预创建一组连接，用完归还
    - 避免频繁创建/销毁连接的开销
    """

    def __init__(self, config: type[DatabaseConfig]):
        self._config = config
        self._pool: list[pymysql.Connection] = []
        self._in_use: set[pymysql.Connection] = set()

    def _create_connection(self) -> pymysql.Connection:
        """创建新的数据库连接"""
        return pymysql.connect(
            host=self._config.HOST,
            port=self._config.PORT,
            user=self._config.USER,
            password=self._config.PASSWORD,
            database=self._config.DATABASE,      # 指定目标数据库
            charset=self._config.CHARSET,
            connect_timeout=self._config.CONNECT_TIMEOUT,
            cursorclass=DictCursor,  # 返回字典格式，方便使用
        )

    def get(self) -> pymysql.Connection:
        """从池中获取一个连接"""
        # 池中有空闲连接则复用
        while self._pool:
            conn = self._pool.pop()
            try:
                conn.ping(reconnect=True)  # 检查连接是否存活
                self._in_use.add(conn)
                return conn
            except Exception:
                conn.close()

        # 否则创建新连接
        conn = self._create_connection()
        self._in_use.add(conn)
        return conn

    def release(self, conn: pymysql.Connection):
        """归还连接到池中"""
        if conn in self._in_use:
            self._in_use.remove(conn)
            if conn.open:
                self._pool.append(conn)

    def close_all(self):
        """关闭所有连接"""
        for conn in self._pool:
            conn.close()
        self._pool.clear()
        for conn in list(self._in_use):
            conn.close()
            self._in_use.remove(conn)


# 全局连接池实例
_pool: DatabasePool | None = None


def get_pool() -> DatabasePool:
    """获取全局连接池（懒加载）"""
    global _pool
    if _pool is None:
        _pool = DatabasePool(DatabaseConfig)
    return _pool


@contextmanager
def get_connection():
    """
    上下文管理器：自动获取和归还连接
    使用方式:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(...)
    """
    pool = get_pool()
    conn = pool.get()
    try:
        yield conn
    finally:
        pool.release(conn)


def execute_query(sql: str, params: tuple | dict | None = None) -> list[dict]:
    """
    执行查询并返回结果集（使用参数化查询，防止 SQL 注入）
    :param sql:  SQL 语句，使用 %s 作为占位符
    :param params: 查询参数（元组或字典）
    :return: 查询结果列表
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()


def execute_update(sql: str, params: tuple | dict | None = None) -> int:
    """
    执行增/删/改操作，返回影响行数（参数化查询防注入）
    :param sql:  SQL 语句
    :param params: 参数
    :return: 影响的行数
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            rows = cursor.execute(sql, params or ())
            conn.commit()
            return rows


def execute_insert(sql: str, params: tuple | dict | None = None) -> int:
    """
    执行插入操作，返回新生成的自增主键 ID
    :param sql:  INSERT 语句
    :param params: 参数
    :return: 新插入行的自增 ID
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor.lastrowid


def init_database():
    """初始化数据库：创建 student_db 数据库（如果不存在）"""
    conn = pymysql.connect(
        host=DatabaseConfig.HOST,
        port=DatabaseConfig.PORT,
        user=DatabaseConfig.USER,
        password=DatabaseConfig.PASSWORD,
        charset=DatabaseConfig.CHARSET,
        cursorclass=DictCursor,
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DatabaseConfig.DATABASE}` "
                f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
    finally:
        conn.close()
