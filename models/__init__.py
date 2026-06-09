"""
models 模块 - 数据模型定义

包含:
- Student 实体类（OOP 封装）
- 学生表结构、字段标签、校验规则
"""

from .student import (
    Student,
    TABLE_SCHEMA,
    FIELD_LABELS,
    REQUIRED_FIELDS,
    ALLOWED_FIELDS,
    SEARCHABLE_FIELDS,
)
