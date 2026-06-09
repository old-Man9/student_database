"""
学生信息管理服务层（面向对象设计）

提供的功能:
- 增删改查（CRUD）：使用 Student 对象操作
- 模糊搜索：在多个字段中 LIKE 搜索关键词
- 多条件组合查询：支持精确匹配、模糊匹配、范围查询
- 数据统计汇总：性别/年级/专业分布，年龄统计

安全特性:
- 参数化查询（%s 占位符）防止 SQL 注入
- 白名单字段校验
- 连接池管理，自动获取/归还连接
"""

from typing import Union

from db import execute_query, execute_update, execute_insert
from models.student import (
    Student, TABLE_SCHEMA,
    ALLOWED_FIELDS, SEARCHABLE_FIELDS, REQUIRED_FIELDS, FIELD_LABELS,
)


# ═══════════════════════════════════════════════════
# 初始化
# ═══════════════════════════════════════════════════

def init_table():
    """创建学生表（如果不存在）"""
    execute_update(TABLE_SCHEMA)
    return True


# ═══════════════════════════════════════════════════
# 增 (Create)
# ═══════════════════════════════════════════════════

def add_student(data: Union[Student, dict]) -> int:
    """
    添加学生

    支持两种传参方式:
        # OOP 方式
        >>> s = Student(name='张三', age=20, grade='2024级', major='计算机科学')
        >>> s.validate()
        >>> new_id = add_student(s)

        # 字典方式（向后兼容）
        >>> new_id = add_student({'name': '张三', 'age': 20, ...})

    :param data: Student 对象 或 dict
    :return: 新学生的 ID
    :raises ValueError: 数据校验不通过
    :raises pymysql.Error: 数据库错误
    """
    # 统一转为字典
    if isinstance(data, Student):
        try:
            data.validate()
        except ValueError as e:
            raise ValueError(f"数据校验失败: {e}")
        record = data.to_dict(exclude_id=True)
    elif isinstance(data, dict):
        # 字典模式：手动校验必填字段
        for field in REQUIRED_FIELDS:
            if not data.get(field):
                raise ValueError(f"'{FIELD_LABELS.get(field, field)}' 为必填项")
        # 白名单过滤
        record = {k: v for k, v in data.items() if k in ALLOWED_FIELDS and k != 'id'}
        # 使用 Student 类进行校验
        try:
            s = Student.from_dict(record)
            s.validate()
        except ValueError as e:
            raise ValueError(f"数据校验失败: {e}")
    else:
        raise TypeError(f"data 参数必须是 Student 对象或 dict，收到: {type(data)}")

    if not record:
        raise ValueError("没有可插入的有效数据")

    # 构建参数化 SQL（防注入）
    columns = ', '.join(f'`{k}`' for k in record)
    placeholders = ', '.join(['%s'] * len(record))
    values = list(record.values())

    sql = f"INSERT INTO students ({columns}) VALUES ({placeholders})"
    return execute_insert(sql, tuple(values))


# ═══════════════════════════════════════════════════
# 删 (Delete)
# ═══════════════════════════════════════════════════

def delete_student(student_id: int) -> int:
    """
    按 ID 删除学生
    :param student_id: 学号
    :return: 影响行数（0 表示不存在，1 表示删除成功）
    """
    return execute_update(
        "DELETE FROM students WHERE id = %s",
        (student_id,),
    )


def batch_delete(ids: list[int]) -> int:
    """
    批量删除学生
    :param ids: 学号列表
    :return: 成功删除的行数
    """
    if not ids:
        return 0
    # 参数化查询防注入
    placeholders = ', '.join(['%s'] * len(ids))
    sql = f"DELETE FROM students WHERE id IN ({placeholders})"
    return execute_update(sql, tuple(ids))


# ═══════════════════════════════════════════════════
# 改 (Update)
# ═══════════════════════════════════════════════════

def update_student(student_id: int, data: Union[Student, dict]) -> int:
    """
    更新学生信息

    支持两种方式:
        # OOP 方式
        >>> s = Student(name='张三', age=21, ...)
        >>> update_student(1001, s)

        # 字典方式（只传需要更新的字段）
        >>> update_student(1001, {'age': 21, 'grade': '2025级'})

    :param student_id: 学号
    :param data: Student 对象 或 字段 dict
    :return: 影响行数
    :raises ValueError: 数据校验不通过
    """
    # 统一转为字段字典
    if isinstance(data, Student):
        data.validate()
        filtered = data.to_dict(exclude_id=True)
    elif isinstance(data, dict):
        # 白名单过滤（排除系统维护字段）
        filtered = {k: v for k, v in data.items()
                    if k in ALLOWED_FIELDS and k not in ('id', 'created_at', 'updated_at')}
        if not filtered:
            return 0
        # 仅校验本次更新的字段（不校验未传入的字段）
        for field, value in filtered.items():
            if field == 'name' and value and len(str(value).strip()) < 2:
                raise ValueError(f"'{FIELD_LABELS.get(field, field)}' 长度需 >= 2")
            if field == 'gender' and value and value not in ('男', '女', 'M', 'F', 'Male', 'Female', 'm', 'f'):
                raise ValueError(f"'{FIELD_LABELS.get(field, field)}' 值无效: {value}")
            if field == 'age':
                try:
                    a = int(value)
                    if not (1 <= a <= 120):
                        raise ValueError(f"年龄需在 1-120 之间: {a}")
                except (TypeError, ValueError):
                    raise ValueError(f"年龄必须是整数: {value}")
            if field == 'grade' and value and len(str(value).strip()) < 2:
                raise ValueError(f"'{FIELD_LABELS.get(field, field)}' 长度需 >= 2")
            if field == 'major' and value and len(str(value).strip()) < 2:
                raise ValueError(f"'{FIELD_LABELS.get(field, field)}' 长度需 >= 2")
            if field == 'phone' and value and len(str(value)) > 20:
                raise ValueError(f"'{FIELD_LABELS.get(field, field)}' 长度需 <= 20")
            if field == 'email' and value and '@' not in str(value):
                raise ValueError(f"'{FIELD_LABELS.get(field, field)}' 格式不正确: {value}")
    else:
        raise TypeError(f"data 参数必须是 Student 对象或 dict，收到: {type(data)}")

    # 过滤空值
    filtered = {k: v for k, v in filtered.items() if v is not None}
    if not filtered:
        return 0

    # 构建参数化 UPDATE
    set_clause = ', '.join(f'`{k}` = %s' for k in filtered)
    values = list(filtered.values())
    values.append(student_id)

    sql = f"UPDATE students SET {set_clause} WHERE id = %s"
    return execute_update(sql, tuple(values))


# ═══════════════════════════════════════════════════
# 查 (Read)
# ═══════════════════════════════════════════════════

def get_student_by_id(student_id: int) -> Student | None:
    """
    按 ID 查询单个学生
    :return: Student 对象，不存在则返回 None
    """
    rows = execute_query(
        "SELECT * FROM students WHERE id = %s",
        (student_id,),
    )
    return Student.from_dict(rows[0]) if rows else None


def get_all_students() -> list[Student]:
    """获取全部学生，按 ID 降序"""
    rows = execute_query("SELECT * FROM students ORDER BY id DESC")
    return [Student.from_dict(r) for r in rows]


def get_students_page(page: int = 1, page_size: int = 20) -> tuple[list[Student], int]:
    """
    分页查询

    :param page: 页码（从 1 开始）
    :param page_size: 每页条数
    :return: (Student 对象列表, 总条数)
    """
    total_row = execute_query("SELECT COUNT(*) AS cnt FROM students")
    total = total_row[0]['cnt'] if total_row else 0
    offset = (page - 1) * page_size
    rows = execute_query(
        "SELECT * FROM students ORDER BY id DESC LIMIT %s OFFSET %s",
        (page_size, offset),
    )
    return [Student.from_dict(r) for r in rows], total


# ═══════════════════════════════════════════════════
# 模糊搜索
# ═══════════════════════════════════════════════════

def fuzzy_search(keyword: str) -> list[Student]:
    """
    模糊搜索：在姓名、专业、年级等字段中搜索关键词

    使用参数化查询 LIKE，防止 SQL 注入：
    - ❌ 不安全: f"SELECT * FROM students WHERE name LIKE '%{keyword}%'"
    - ✅ 安全:   execute_query(sql, (f'%{keyword}%',))

    :param keyword: 搜索关键词
    :return: 匹配的 Student 对象列表
    """
    if not keyword.strip():
        return []

    like_pattern = f'%{keyword.strip()}%'
    # 动态构建 LIKE 条件
    conditions = ' OR '.join(f'`{f}` LIKE %s' for f in SEARCHABLE_FIELDS)
    params = [like_pattern] * len(SEARCHABLE_FIELDS)

    sql = f"SELECT * FROM students WHERE {conditions} ORDER BY id DESC"
    rows = execute_query(sql, tuple(params))
    return [Student.from_dict(r) for r in rows]


# ═══════════════════════════════════════════════════
# 多条件组合查询
# ═══════════════════════════════════════════════════

def multi_filter(filters: dict[str, any]) -> list[Student]:
    """
    多条件组合查询

    支持的过滤类型:
        - 精确匹配:     {'grade': '2024级', 'gender': '男'}
        - 模糊匹配:     {'name_like': '张', 'major_like': '计算机'}
        - 范围查询:     {'age_min': 18, 'age_max': 25}

    :param filters: 过滤条件字典
    :return: 匹配的 Student 对象列表
    """
    conditions: list[str] = []
    params: list = []

    for key, value in filters.items():
        if value is None or value == '':
            continue

        # 模糊匹配：字段名_like
        if key.endswith('_like'):
            field = key[:-5]
            if field in SEARCHABLE_FIELDS:
                conditions.append(f'`{field}` LIKE %s')
                params.append(f'%{value}%')

        # 范围匹配：_min / _max
        elif key.endswith('_min'):
            field = key[:-4]
            if field in ALLOWED_FIELDS:
                conditions.append(f'`{field}` >= %s')
                params.append(value)
        elif key.endswith('_max'):
            field = key[:-4]
            if field in ALLOWED_FIELDS:
                conditions.append(f'`{field}` <= %s')
                params.append(value)

        # 精确匹配
        elif key in ALLOWED_FIELDS:
            conditions.append(f'`{key}` = %s')
            params.append(value)

    if not conditions:
        return get_all_students()

    sql = f"SELECT * FROM students WHERE {' AND '.join(conditions)} ORDER BY id DESC"
    rows = execute_query(sql, tuple(params))
    return [Student.from_dict(r) for r in rows]


# ═══════════════════════════════════════════════════
# 数据统计汇总
# ═══════════════════════════════════════════════════

def get_statistics() -> dict:
    """
    数据统计汇总

    :return: {
        'total':          总人数,
        'gender_dist':    性别分布 [{gender, cnt}, ...],
        'grade_dist':     年级分布 [{grade, cnt}, ...],
        'major_dist':     专业分布 [{major, cnt}, ...] (按人数降序),
        'age_range':      年龄统计 [{min_age, max_age, avg_age}],
        'latest_enrollment': 最近入学日期,
    }
    """
    stats = {}

    # 总人数
    stats['total'] = execute_query(
        "SELECT COUNT(*) AS cnt FROM students"
    )[0]['cnt']

    # 按性别统计
    stats['gender_dist'] = execute_query(
        "SELECT gender, COUNT(*) AS cnt FROM students GROUP BY gender"
    )

    # 按年级统计
    stats['grade_dist'] = execute_query(
        "SELECT grade, COUNT(*) AS cnt FROM students GROUP BY grade ORDER BY cnt DESC"
    )

    # 按专业统计
    stats['major_dist'] = execute_query(
        "SELECT major, COUNT(*) AS cnt FROM students GROUP BY major ORDER BY cnt DESC"
    )

    # 年龄分布（min, max, avg）
    stats['age_range'] = execute_query(
        "SELECT MIN(age) AS min_age, MAX(age) AS max_age, "
        "ROUND(AVG(age), 1) AS avg_age FROM students"
    )

    # 最近入学日期
    stats['latest_enrollment'] = execute_query(
        "SELECT MAX(enrollment) AS latest FROM students WHERE enrollment IS NOT NULL"
    )

    return stats
