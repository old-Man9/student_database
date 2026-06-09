"""
学生信息管理系统 - Web 可视化界面
基于 Flask + Bootstrap 5
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import date

from db import init_database
from services import (
    init_table, add_student, delete_student, batch_delete,
    update_student, get_student_by_id, get_all_students,
    get_students_page, fuzzy_search, multi_filter, get_statistics,
)
from models import Student

app = Flask(__name__)
app.secret_key = 'student-management-secret-key-2024'

# 初始化数据库
init_database()
init_table()


# ═══════════════════════════════════════════════════
# 页面路由
# ═══════════════════════════════════════════════════

@app.route('/')
def index():
    """首页 - 仪表盘"""
    stats = get_statistics()
    students, total = get_students_page(1, 8)
    return render_template('index.html',
                           stats=stats,
                           students=students,
                           total=total)


@app.route('/students')
def list_students():
    """学生列表（支持搜索和分页）"""
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('search', '').strip()
    page_size = 10

    if keyword:
        students = fuzzy_search(keyword)
        total = len(students)
        # 手动分页
        start = (page - 1) * page_size
        students = students[start:start + page_size]
    else:
        students, total = get_students_page(page, page_size)

    total_pages = max(1, (total + page_size - 1) // page_size)

    # 如果请求是 AJAX，返回 JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'students': [_student_to_dict(s) for s in students],
            'total': total,
            'page': page,
            'total_pages': total_pages,
        })

    return render_template('list.html',
                           students=students,
                           total=total,
                           page=page,
                           total_pages=total_pages,
                           keyword=keyword)


@app.route('/students/add', methods=['GET', 'POST'])
def add():
    """添加学生"""
    if request.method == 'POST':
        try:
            data = {
                'name': request.form['name'].strip(),
                'gender': request.form.get('gender', '男'),
                'age': int(request.form.get('age', 0)),
                'grade': request.form['grade'].strip(),
                'major': request.form['major'].strip(),
                'phone': request.form.get('phone', '').strip(),
                'email': request.form.get('email', '').strip(),
                'address': request.form.get('address', '').strip(),
            }
            enroll_str = request.form.get('enrollment', '').strip()
            if enroll_str:
                parts = enroll_str.split('-')
                data['enrollment'] = date(int(parts[0]), int(parts[1]), int(parts[2]))

            s = Student(**data)
            s.validate()
            new_id = add_student(s)
            flash(f'✅ 学生 [{new_id}] {s.name} 添加成功！', 'success')
            return redirect(url_for('list_students'))
        except ValueError as e:
            flash(f'❌ 数据错误: {e}', 'danger')
        except Exception as e:
            flash(f'❌ 系统错误: {e}', 'danger')

    return render_template('add.html')


@app.route('/students/<int:sid>')
def detail(sid):
    """学生详情"""
    s = get_student_by_id(sid)
    if not s:
        flash('学生不存在', 'warning')
        return redirect(url_for('list_students'))
    return render_template('detail.html', student=s)


@app.route('/students/<int:sid>/edit', methods=['GET', 'POST'])
def edit(sid):
    """编辑学生"""
    s = get_student_by_id(sid)
    if not s:
        flash('学生不存在', 'warning')
        return redirect(url_for('list_students'))

    if request.method == 'POST':
        try:
            # 只收集有变化的字段
            data = {}
            for field in ['name', 'gender', 'grade', 'major', 'phone', 'email', 'address']:
                val = request.form.get(field, '').strip()
                if val and val != str(getattr(s, field, '')):
                    data[field] = val

            age_str = request.form.get('age', '').strip()
            if age_str and int(age_str) != s.age:
                data['age'] = int(age_str)

            enroll_str = request.form.get('enrollment', '').strip()
            if enroll_str:
                parts = enroll_str.split('-')
                d = date(int(parts[0]), int(parts[1]), int(parts[2]))
                if d != s.enrollment:
                    data['enrollment'] = d

            if data:
                update_student(sid, data)
                flash(f'✅ 学生 [{sid}] 信息已更新', 'success')
            else:
                flash('未做任何修改', 'info')
            return redirect(url_for('list_students'))
        except ValueError as e:
            flash(f'❌ 数据错误: {e}', 'danger')
        except Exception as e:
            flash(f'❌ 系统错误: {e}', 'danger')

    return render_template('edit.html', student=s)


@app.route('/students/<int:sid>/delete', methods=['POST'])
def delete(sid):
    """删除学生"""
    s = get_student_by_id(sid)
    if s:
        delete_student(sid)
        flash(f'✅ 已删除学生 [{sid}] {s.name}', 'success')
    else:
        flash('学生不存在', 'warning')
    return redirect(url_for('list_students'))


@app.route('/students/batch-delete', methods=['POST'])
def delete_batch():
    """批量删除"""
    ids_str = request.form.get('ids', '')
    if not ids_str:
        flash('请选择要删除的学生', 'warning')
        return redirect(url_for('list_students'))

    try:
        ids = [int(x.strip()) for x in ids_str.split(',') if x.strip()]
        deleted = batch_delete(ids)
        flash(f'✅ 成功删除 {deleted} 条记录', 'success')
    except Exception as e:
        flash(f'❌ 删除失败: {e}', 'danger')

    return redirect(url_for('list_students'))


@app.route('/search')
def search():
    """高级搜索"""
    filters = {}
    name = request.args.get('name', '').strip()
    grade = request.args.get('grade', '').strip()
    major = request.args.get('major', '').strip()
    gender = request.args.get('gender', '').strip()
    age_min = request.args.get('age_min', '').strip()
    age_max = request.args.get('age_max', '').strip()

    if name:
        filters['name_like'] = name
    if grade:
        filters['grade'] = grade
    if major:
        filters['major_like'] = major
    if gender:
        filters['gender'] = gender
    if age_min:
        filters['age_min'] = int(age_min)
    if age_max:
        filters['age_max'] = int(age_max)

    results = multi_filter(filters) if filters else get_all_students()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'students': [_student_to_dict(s) for s in results], 'total': len(results)})

    return render_template('search.html', results=results, total=len(results),
                           name=name, grade=grade, major=major, gender=gender,
                           age_min=age_min, age_max=age_max)


@app.route('/stats')
def stats():
    """统计页面"""
    stats = get_statistics()
    return render_template('stats.html', stats=stats)


# ═══════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════

def _student_to_dict(s):
    """Student 对象转为字典（JSON 序列化）"""
    d = s.to_dict(exclude_id=False)
    d['id'] = s.id
    if d.get('enrollment') and hasattr(d['enrollment'], 'strftime'):
        d['enrollment'] = d['enrollment'].strftime('%Y-%m-%d')
    return d


# 注册模板函数
app.jinja_env.globals.update(
    strftime=lambda d: d.strftime('%Y-%m-%d') if d else '',
    field_labels={
        'id': '学号', 'name': '姓名', 'gender': '性别', 'age': '年龄',
        'grade': '年级', 'major': '专业', 'phone': '电话', 'email': '邮箱',
        'address': '地址', 'enrollment': '入学日期',
        'created_at': '创建时间', 'updated_at': '更新时间',
    }
)


# ═══════════════════════════════════════════════════
# 启动
# ═══════════════════════════════════════════════════

if __name__ == '__main__':
    print('** Student Management System - Web UI **')
    print('   URL: http://localhost:5000')
    print('   Press Ctrl+C to quit\n')
    app.run(debug=True, host='0.0.0.0', port=5000)
