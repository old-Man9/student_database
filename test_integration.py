# -*- coding: utf-8 -*-
"""Integration tests for Student Management System"""

import sys
sys.path.insert(0, 'd:/Git_student库')

from db import init_database, execute_update
from services import (init_table, add_student, delete_student, batch_delete,
                      update_student, get_student_by_id, get_all_students,
                      get_students_page, fuzzy_search, multi_filter, get_statistics)
from models import Student

p = 0
f = 0

def check(name, ok, detail=''):
    global p, f
    if ok:
        p += 1
        print('  PASS  ' + name)
    else:
        f += 1
        print('  FAIL  ' + name + ' | ' + str(detail))


# ===== Phase 1: DB Init =====
print('\n[Phase 1] Database Init')
try:
    init_database()
    check('init_database', True)
except Exception as e:
    check('init_database', False, str(e))

try:
    # Drop and recreate with new schema (VARCHAR gender)
    execute_update('DROP TABLE IF EXISTS students')
    init_table()
    check('init_table', True)
except Exception as e:
    check('init_table', False, str(e))


# ===== Phase 2: Create =====
print('\n[Phase 2] Create Students')

s1 = Student(name='ZhangSan', gender='M', age=20, grade='2024', major='CS', phone='13800138001')
try:
    s1.validate()
    check('validate s1', True)
    sid1 = add_student(s1)
    s1._id = sid1
    check('add s1 (OOP)', sid1 > 0, 'id=' + str(sid1))
except Exception as e:
    check('add s1', False, str(e))
    sid1 = None

sid2 = add_student({'name':'LiSi','gender':'F','age':19,'grade':'2024','major':'SE'})
check('add s2 (dict)', sid2 > 0, 'id=' + str(sid2))

sid3 = add_student({'name':'WangWu','gender':'M','age':22,'grade':'2023','major':'DS'})
check('add s3', sid3 > 0)

sid4 = add_student({'name':'ZhaoLiu','gender':'F','age':21,'grade':'2023','major':'AI'})
sid5 = add_student({'name':'SunQi','gender':'M','age':23,'grade':'2022','major':'CS','phone':'13805'})
sid6 = add_student({'name':'ZhouBa','gender':'F','age':20,'grade':'2024','major':'SE'})
check('add s4-s6', sid4 > 0 and sid5 > 0 and sid6 > 0)

# Validation rejection
try:
    add_student({'name':'X'})
    check('reject missing fields', False, 'should raise ValueError')
except (ValueError, TypeError) as e:
    check('reject missing fields', True)

try:
    sb = Student(name='X', gender='?', age=200, grade='', major='')
    sb.validate()
    check('reject invalid data', False)
except ValueError:
    check('reject invalid data', True)


# ===== Phase 3: Read =====
print('\n[Phase 3] Read Students')

r = get_student_by_id(s1.id)
check('get by id', r is not None, r.name if r else 'None')

r = get_student_by_id(99999)
check('get non-existent returns None', r is None)

rows, total = get_students_page(1, 3)
check('pagination page 1', len(rows) >= 1, 'rows=' + str(len(rows)) + ' total=' + str(total))

all_students = get_all_students()
check('get all', len(all_students) == 6, 'count=' + str(len(all_students)))


# ===== Phase 4: Update =====
print('\n[Phase 4] Update Students')

update_student(s1.id, {'age': 21, 'phone': '139'})
su = get_student_by_id(s1.id)
check('update age+phone', su.age == 21 and su.phone == '139',
      'age=' + str(su.age) + ' phone=' + str(su.phone))

update_student(sid2, {'major': 'Network'})
su2 = get_student_by_id(sid2)
check('update major (dict)', su2.major == 'Network', 'major=' + str(su2.major))


# ===== Phase 5: Fuzzy Search =====
print('\n[Phase 5] Fuzzy Search')

r = fuzzy_search('Li')
check('search Li', len(r) >= 1, 'found ' + str(len(r)) + ': ' + str([s.name for s in r]))

r = fuzzy_search('CS')
check('search CS', len(r) >= 1, 'found ' + str(len(r)))

r = fuzzy_search('xyzNOTEXIST')
check('search no result', len(r) == 0)


# ===== Phase 6: Multi-filter =====
print('\n[Phase 6] Multi-filter')

r = multi_filter({'grade': '2024', 'gender': 'M'})
check('combo grade+gender', len(r) >= 1,
      'found ' + str(len(r)) + ': ' + str([s.name for s in r]))

r = multi_filter({'age_min': 20, 'age_max': 22})
check('range filter', len(r) >= 1, 'found ' + str(len(r)))

r = multi_filter({'name_like': 'Zhang', 'grade': '2024'})
check('fuzzy+exact combo', len(r) >= 1, 'found ' + str(len(r)))

r = multi_filter({})
check('empty filter = all', len(r) == 6, 'total=' + str(len(r)))


# ===== Phase 7: Statistics =====
print('\n[Phase 7] Statistics')

stats = get_statistics()
check('total count', stats['total'] >= 5, str(stats['total']))
check('gender distribution', len(stats['gender_dist']) >= 2, str(stats['gender_dist']))
check('grade distribution', len(stats['grade_dist']) >= 2, str(stats['grade_dist']))
check('age stats', stats['age_range'][0]['avg_age'] is not None, str(stats['age_range'][0]))


# ===== Phase 8: Delete =====
print('\n[Phase 8] Delete')

r = delete_student(s1.id)
check('delete by id', r == 1)

r2 = get_student_by_id(s1.id)
check('verify deleted', r2 is None)

r = batch_delete([sid2, sid3])
check('batch delete', r >= 1, 'deleted=' + str(r))

remaining = get_all_students()
check('remaining count', len(remaining) == 3,
      'len=' + str(len(remaining)) + ' names=' + str([s.name for s in remaining]))


# ===== Summary =====
print('\n' + '=' * 60)
print('  Results: PASS=' + str(p) + '  FAIL=' + str(f) + '  (Total ' + str(p+f) + ')')
print('=' * 60)
if f == 0:
    print('  ALL TESTS PASSED!')
else:
    print('  SOME TESTS FAILED!')
    sys.exit(1)
