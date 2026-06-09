"""
services 模块 - 业务逻辑层

提供 StudentService 的全部 CRUD、搜索、统计功能。
"""

from .student_service import (
    init_table,
    add_student,
    delete_student,
    batch_delete,
    update_student,
    get_student_by_id,
    get_all_students,
    get_students_page,
    fuzzy_search,
    multi_filter,
    get_statistics,
)
