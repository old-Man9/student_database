"""
学生数据模型
- Student 实体类（OOP 封装）
- 数据校验规则
- 数据库表结构定义
"""

from datetime import date
from typing import Any, Optional


# ═══════════════════════════════════════════════════
# 数据库表结构
# ═══════════════════════════════════════════════════

# 学生表结构定义（第 3 范式：每列原子化，无冗余，无传递依赖）
TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id          INT AUTO_INCREMENT PRIMARY KEY COMMENT '学号（主键，自增）',
    name        VARCHAR(50)  NOT NULL COMMENT '姓名',
    gender      VARCHAR(10) NOT NULL DEFAULT '男' COMMENT '性别（男/女 或 M/F）',
    age         TINYINT UNSIGNED NOT NULL COMMENT '年龄',
    grade       VARCHAR(20)  NOT NULL COMMENT '年级',
    major       VARCHAR(100) NOT NULL COMMENT '专业',
    phone       VARCHAR(20)  DEFAULT '' COMMENT '联系电话',
    email       VARCHAR(100) DEFAULT '' COMMENT '电子邮箱',
    address     VARCHAR(200) DEFAULT '' COMMENT '家庭地址',
    enrollment  DATE         DEFAULT NULL COMMENT '入学日期',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    COMMENT='学生信息表';
"""

# 字段中文名映射
FIELD_LABELS = {
    'id': '学号',
    'name': '姓名',
    'gender': '性别',
    'age': '年龄',
    'grade': '年级',
    'major': '专业',
    'phone': '电话',
    'email': '邮箱',
    'address': '地址',
    'enrollment': '入学日期',
    'created_at': '创建时间',
    'updated_at': '更新时间',
}

# 必填字段
REQUIRED_FIELDS = ['name', 'age', 'grade', 'major']

# 允许的字段（白名单，防注入）
ALLOWED_FIELDS = set(FIELD_LABELS.keys())

# 搜索时可用字段
SEARCHABLE_FIELDS = ['name', 'grade', 'major', 'phone', 'email', 'address']


# ═══════════════════════════════════════════════════
# Student 实体类（面向对象封装）
# ═══════════════════════════════════════════════════

class Student:
    """
    学生实体类

    封装学生信息的所有字段，提供：
    - 属性访问控制
    - 数据校验
    - 序列化/反序列化（to_dict / from_dict）
    - 格式化输出

    使用示例:
        >>> s = Student(name='张三', gender='男', age=20, grade='2024级', major='计算机科学')
        >>> s.validate()                           # 数据校验
        >>> data = s.to_dict()                     # 转为字典（排除 id）
        >>> s2 = Student.from_dict(db_record)      # 从数据库记录创建
        >>> print(s)                               # 格式化输出
    """

    def __init__(
        self,
        name: str,
        gender: str = '男',
        age: int = 20,
        grade: str = '',
        major: str = '',
        phone: str = '',
        email: str = '',
        address: str = '',
        enrollment: Optional[date] = None,
    ):
        self._id: Optional[int] = None
        self.name = name
        self.gender = gender
        self.age = age
        self.grade = grade
        self.major = major
        self.phone = phone
        self.email = email
        self.address = address
        self.enrollment = enrollment
        self._created_at: Optional[date] = None
        self._updated_at: Optional[date] = None

    # ── 属性访问器 ─────────────────────────────

    @property
    def id(self) -> Optional[int]:
        """学号（数据库自增主键，创建前为 None）"""
        return self._id

    @id.setter
    def id(self, value: int):
        if value is not None and (not isinstance(value, int) or value <= 0):
            raise ValueError(f"学号必须为正整数: {value}")
        self._id = value

    # ── 数据校验 ───────────────────────────────

    def validate(self) -> None:
        """
        校验所有字段的合法性
        :raises ValueError: 校验不通过时抛出
        """
        errors = []

        # 姓名：2-50 字符
        if not self.name or not (2 <= len(self.name.strip()) <= 50):
            errors.append(f"姓名长度需在 2-50 字符之间（当前: '{self.name}'）")

        # 性别：允许中英文
        if self.gender not in ('男', '女', 'M', 'F', 'Male', 'Female', 'm', 'f'):
            errors.append(f"性别必须是'男'/'女' 或 'M'/'F'（当前: '{self.gender}'）")

        # 年龄：1-120
        try:
            age = int(self.age)
            if not (1 <= age <= 120):
                errors.append(f"年龄需在 1-120 之间（当前: {age}）")
        except (TypeError, ValueError):
            errors.append(f"年龄必须是整数（当前: '{self.age}'）")

        # 年级：至少 2 字符
        if not self.grade or len(self.grade.strip()) < 2:
            errors.append(f"年级至少需要 2 个字符（当前: '{self.grade}'）")

        # 专业：至少 2 字符
        if not self.major or len(self.major.strip()) < 2:
            errors.append(f"专业至少需要 2 个字符（当前: '{self.major}'）")

        # 电话：不超过 20 字符
        if self.phone and len(self.phone) > 20:
            errors.append(f"电话长度不能超过 20 字符（当前: {len(self.phone)}）")

        # 邮箱：包含 @ 符号
        if self.email and '@' not in self.email:
            errors.append(f"邮箱格式不正确（缺少 @ 符号）: '{self.email}'")

        # 地址：不超过 200 字符
        if self.address and len(self.address) > 200:
            errors.append(f"地址长度不能超过 200 字符（当前: {len(self.address)}）")

        # 入学日期：合理范围
        if self.enrollment is not None:
            if not isinstance(self.enrollment, date):
                errors.append(f"入学日期格式不正确: '{self.enrollment}'")
            elif self.enrollment < date(2000, 1, 1):
                errors.append(f"入学日期不能早于 2000-01-01: {self.enrollment}")
            elif self.enrollment > date(2099, 12, 31):
                errors.append(f"入学日期不能晚于 2099-12-31: {self.enrollment}")

        if errors:
            raise ValueError('; '.join(errors))

    # ── 序列化 ─────────────────────────────────

    def to_dict(self, exclude_id: bool = True) -> dict:
        """
        转为字典，用于数据库操作
        :param exclude_id: 是否排除 id（插入时需要排除）
        """
        data = {
            'name': self.name,
            'gender': self.gender,
            'age': self.age,
            'grade': self.grade,
            'major': self.major,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'enrollment': self.enrollment,
        }
        if not exclude_id and self._id is not None:
            data['id'] = self._id
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Student':
        """
        从字典创建 Student 对象（通常来自数据库查询结果）
        """
        s = cls(
            name=data.get('name', ''),
            gender=data.get('gender', '男'),
            age=data.get('age', 20),
            grade=data.get('grade', ''),
            major=data.get('major', ''),
            phone=data.get('phone', '') or '',
            email=data.get('email', '') or '',
            address=data.get('address', '') or '',
            enrollment=data.get('enrollment'),
        )
        if 'id' in data and data['id'] is not None:
            s._id = data['id']
        if 'created_at' in data:
            s._created_at = data['created_at']
        if 'updated_at' in data:
            s._updated_at = data['updated_at']
        return s

    # ── 格式化输出 ─────────────────────────────

    def format_row(self) -> str:
        """单行简要信息"""
        pid = str(self._id or '--').rjust(4)
        return (f"  [{pid}] {self.name:<6} "
                f"{self.gender}  {str(self.age):>3}岁  "
                f"{self.grade:<10} {self.major:<12} "
                f"电话:{self.phone or '无'}")

    def format_detail(self) -> str:
        """详细信息（多行）"""
        lines = []
        lines.append('─' * 50)
        for field, label in FIELD_LABELS.items():
            val = getattr(self, field, None)
            if val is None or val == '':
                val = '无'
            elif field == 'enrollment' and hasattr(val, 'strftime'):
                val = val.strftime('%Y-%m-%d')
            elif isinstance(val, date):
                val = val.strftime('%Y-%m-%d')
            lines.append(f"  {label:<10}: {val}")
        lines.append('─' * 50)
        return '\n'.join(lines)

    def __str__(self) -> str:
        """默认字符串表示"""
        return f"Student(id={self._id}, name='{self.name}', grade='{self.grade}', major='{self.major}')"

    def __repr__(self) -> str:
        return self.__str__()

    # ── 比较 ───────────────────────────────────

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Student):
            return False
        if self._id is not None and other._id is not None:
            return self._id == other._id
        return self.name == other.name and self.grade == other.grade

    def __hash__(self) -> int:
        return hash(self._id) if self._id else hash((self.name, self.grade))
