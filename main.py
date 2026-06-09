"""
学生信息管理系统 - 命令行交互主程序

基于 Python 面向对象编程 + MySQL 实现

功能菜单:
  1. 添加学生      2. 删除学生      3. 修改学生
  4. 查询学生      5. 查看全部      6. 模糊搜索
  7. 多条件筛选    8. 数据统计      0. 退出

技术栈: Python + MySQL + PyMySQL + OOP
安全: 参数化查询 防 SQL 注入 | 白名单校验 | 连接池管理
"""

import sys
from datetime import date

from db import init_database, DatabaseConfig
from services import (
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
from models import Student, FIELD_LABELS, SEARCHABLE_FIELDS


# ═══════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════

def print_separator(char: str = '─', length: int = 60):
    print(char * length)


def print_title(text: str):
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}")


def input_field(prompt: str, default: str = '') -> str:
    """输入字段值，回车跳过"""
    val = input(f"  {prompt}").strip()
    return val if val else default


def format_date(val: str) -> date | None:
    """将 YYYY-MM-DD 字符串转为 date，空字符串返回 None"""
    if not val.strip():
        return None
    try:
        parts = val.strip().split('-')
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except Exception:
        print(f"  ⚠ 日期格式不正确: '{val}'，应为 YYYY-MM-DD")
        return None


# ═══════════════════════════════════════════════════
# 菜单功能
# ═══════════════════════════════════════════════════

def menu_add():
    """添加学生 (OOP 方式)"""
    print_title("添加学生")

    name = input_field("姓名（必填）: ")
    if not name:
        print("  ⚠ 姓名为必填项，添加取消")
        return

    # 使用 Student 对象收集数据
    try:
        age_str = input_field("年龄（必填，默认 20）: ", '20')
        age = int(age_str)
    except ValueError:
        print("  ❌ 年龄必须为整数")
        return

    grade = input_field("年级（必填，如 2024级）: ")
    major = input_field("专业（必填）: ")

    student = Student(
        name=name,
        gender=input_field("性别（男/女，默认男）: ", '男'),
        age=age,
        grade=grade,
        major=major,
        phone=input_field("电话: "),
        email=input_field("邮箱: "),
        address=input_field("地址: "),
        enrollment=format_date(input_field("入学日期（YYYY-MM-DD）: ")),
    )

    try:
        new_id = add_student(student)
        print(f"\n  ✅ 添加成功！学号: {new_id}")
        print(f"     {student.format_row()}")
    except ValueError as e:
        print(f"\n  ❌ 数据错误: {e}")
    except Exception as e:
        print(f"\n  ❌ 系统错误: {e}")


def menu_delete():
    """删除学生"""
    print_title("删除学生")

    val = input_field("请输入要删除的学号（多个用逗号分隔）: ")
    if not val:
        return

    try:
        ids = [int(x.strip()) for x in val.split(',') if x.strip()]
    except ValueError:
        print("  ❌ 请输入有效的数字学号")
        return

    # 先显示要删除的学生
    found_any = False
    for sid in ids:
        s = get_student_by_id(sid)
        if s:
            found_any = True
            print(f"  → 将删除: {s.format_row()}")
        else:
            print(f"  → 学号 {sid} 不存在，跳过")

    if not found_any:
        print("  ⚠ 没有找到可删除的学生")
        return

    confirm = input_field("\n确认删除？(y/n): ")
    if confirm.lower() != 'y':
        print("  已取消")
        return

    if len(ids) == 1:
        deleted = delete_student(ids[0])
    else:
        deleted = batch_delete(ids)
    print(f"  ✅ 成功删除 {deleted} 条记录")


def menu_update():
    """修改学生"""
    print_title("修改学生信息")

    try:
        sid = int(input_field("请输入要修改的学号: "))
    except ValueError:
        print("  ❌ 请输入有效学号")
        return

    student = get_student_by_id(sid)
    if not student:
        print(f"  ❌ 学号 {sid} 不存在")
        return

    print(f"\n  当前信息 → {student}")
    print(student.format_detail())
    print("  （直接回车保留原值，输入新值则更新）\n")

    # 收集更新数据
    updates = {}
    name = input_field(f"姓名 [{student.name}]: ")
    if name:
        updates['name'] = name

    gender = input_field(f"性别 [{student.gender}]: ")
    if gender:
        updates['gender'] = gender

    age = input_field(f"年龄 [{student.age}]: ")
    if age:
        try:
            updates['age'] = int(age)
        except ValueError:
            print("  ❌ 年龄必须为整数")
            return

    grade = input_field(f"年级 [{student.grade}]: ")
    if grade:
        updates['grade'] = grade

    major = input_field(f"专业 [{student.major}]: ")
    if major:
        updates['major'] = major

    phone = input_field(f"电话 [{student.phone or '无'}]: ")
    if phone:
        updates['phone'] = phone

    email = input_field(f"邮箱 [{student.email or '无'}]: ")
    if email:
        updates['email'] = email

    address = input_field(f"地址 [{student.address or '无'}]: ")
    if address:
        updates['address'] = address

    enroll = input_field(f"入学日期 [{student.enrollment or '无'}]: ")
    if enroll:
        d = format_date(enroll)
        if d:
            updates['enrollment'] = d

    if not updates:
        print("  无修改，已取消")
        return

    try:
        update_student(sid, updates)
        print(f"\n  ✅ 学号 {sid} 信息已更新")
    except ValueError as e:
        print(f"\n  ❌ 数据错误: {e}")
    except Exception as e:
        print(f"\n  ❌ 系统错误: {e}")


def menu_query():
    """按 ID 查询学生"""
    print_title("查询学生")

    try:
        sid = int(input_field("请输入学号: "))
    except ValueError:
        print("  ❌ 请输入有效学号")
        return

    s = get_student_by_id(sid)
    if s:
        print(s.format_detail())
    else:
        print(f"  ❌ 学号 {sid} 不存在")


def menu_list():
    """分页查看全部学生"""
    print_title("学生列表")
    page_size = 10
    page = 1

    while True:
        students, total = get_students_page(page, page_size)
        total_pages = max(1, (total + page_size - 1) // page_size)

        print(f"\n  📋 第 {page}/{total_pages} 页（共 {total} 人）\n")

        if not students:
            print("  (暂无数据)")
        else:
            for s in students:
                print(s.format_row())

        print(f"\n  [n] 下一页  [p] 上一页  [q] 返回")
        cmd = input_field("  > ").lower()

        if cmd == 'n' and page < total_pages:
            page += 1
        elif cmd == 'p' and page > 1:
            page -= 1
        elif cmd == 'q':
            break
        else:
            print("  ⚠ 无效操作")


def menu_search():
    """模糊搜索"""
    print_title("模糊搜索")
    print(f"  搜索范围: {', '.join(SEARCHABLE_FIELDS)}\n")

    keyword = input_field("请输入关键词: ")
    if not keyword:
        return

    results = fuzzy_search(keyword)
    if results:
        print(f"\n  🔍 找到 {len(results)} 条结果:\n")
        for s in results:
            print(s.format_row())
    else:
        print("  📭 未找到匹配结果")


def menu_filter():
    """多条件组合查询"""
    print_title("多条件组合查询")
    print("  输入条件进行筛选（直接回车跳过该项）\n")

    filters = {}

    name = input_field("姓名关键词: ")
    if name:
        filters['name_like'] = name

    grade = input_field("年级（精确匹配）: ")
    if grade:
        filters['grade'] = grade

    major = input_field("专业关键词: ")
    if major:
        filters['major_like'] = major

    gender = input_field("性别（男/女）: ")
    if gender:
        filters['gender'] = gender

    age_min = input_field("最小年龄: ")
    if age_min:
        try:
            filters['age_min'] = int(age_min)
        except ValueError:
            print("  ⚠ 年龄必须为整数，已跳过")

    age_max = input_field("最大年龄: ")
    if age_max:
        try:
            filters['age_max'] = int(age_max)
        except ValueError:
            print("  ⚠ 年龄必须为整数，已跳过")

    results = multi_filter(filters)
    if results:
        print(f"\n  🔍 找到 {len(results)} 条结果:\n")
        for s in results:
            print(s.format_row())
    else:
        print("  📭 无匹配结果")


def menu_stats():
    """数据统计汇总"""
    print_title("数据统计汇总")

    stats = get_statistics()

    print(f"\n  📊 学生总数: {stats['total']} 人")

    # 性别分布
    print(f"\n  {'─' * 40}")
    print(f"  【性别分布】")
    for row in stats['gender_dist']:
        bar = '█' * row['cnt']
        print(f"    {row['gender']}: {row['cnt']}人  {bar}")

    # 年级分布
    print(f"\n  {'─' * 40}")
    print(f"  【年级分布】")
    for row in stats['grade_dist']:
        print(f"    {row['grade']}: {row['cnt']}人")

    # 专业分布 Top 5
    print(f"\n  {'─' * 40}")
    print(f"  【专业分布 (Top 5)】")
    for row in stats['major_dist'][:5]:
        print(f"    {row['major']}: {row['cnt']}人")

    # 年龄统计
    if stats['age_range']:
        ar = stats['age_range'][0]
        print(f"\n  {'─' * 40}")
        print(f"  【年龄统计】")
        print(f"    最小年龄: {ar['min_age']}岁")
        print(f"    最大年龄: {ar['max_age']}岁")
        print(f"    平均年龄: {ar['avg_age']}岁")

    # 最近入学日期
    if stats['latest_enrollment'] and stats['latest_enrollment'][0]['latest']:
        print(f"\n  【最近入学日期】: {stats['latest_enrollment'][0]['latest']}")

    print()


# ═══════════════════════════════════════════════════
# 主菜单
# ═══════════════════════════════════════════════════

MENU = [
    ('1', '添加学生',   menu_add),
    ('2', '删除学生',   menu_delete),
    ('3', '修改信息',   menu_update),
    ('4', '按学号查询', menu_query),
    ('5', '查看全部',   menu_list),
    ('6', '模糊搜索',   menu_search),
    ('7', '多条件筛选', menu_filter),
    ('8', '数据统计',   menu_stats),
    ('0', '退出系统',   None),
]


def show_menu():
    print(f"\n{'═' * 40}")
    print(f"  🎓 学生信息管理系统")
    print(f"{'═' * 40}")
    for key, name, _ in MENU:
        print(f"  [{key}]  {name}")
    print(f"{'═' * 40}")


def main():
    """程序入口"""
    # 1. 初始化数据库
    print("⏳ 正在初始化数据库...")
    try:
        init_database()
        init_table()
        print("✅ 数据库初始化完成\n")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("   请确保 MySQL 服务已启动")
        print(f"   配置: root@{DatabaseConfig.HOST}:{DatabaseConfig.PORT}")
        sys.exit(1)

    # 2. 主循环
    while True:
        show_menu()
        try:
            choice = input("  请选择 [0-8]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  👋 再见！")
            break

        if choice == '0':
            print("\n  👋 再见！")
            break

        for key, _, handler in MENU:
            if choice == key and handler:
                try:
                    handler()
                except KeyboardInterrupt:
                    print("\n  操作已取消")
                except Exception as e:
                    print(f"\n  ❌ 出错: {e}")
                break
        else:
            print(f"\n  ⚠ 无效选项 [{choice}]，请重新输入")


if __name__ == '__main__':
    main()
