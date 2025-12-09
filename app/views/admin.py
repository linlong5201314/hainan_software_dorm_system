from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.models import User, Student, Dormitory, Repair, Visitor, DormManager, DormChangeRequest, UtilityBill, Payment
from werkzeug.security import generate_password_hash
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    # 统计数据
    total_students = Student.query.count()
    total_dorms = Dormitory.query.count()
    total_repairs = Repair.query.count()
    pending_repairs = Repair.query.filter_by(status='pending').count()
    
    # 获取最新活动
    latest_repairs = Repair.query.order_by(Repair.created_at.desc()).limit(5).all()
    latest_visitors = Visitor.query.order_by(Visitor.visit_date.desc()).limit(5).all()
    
    # 准备活动数据
    activities = []
    
    # 添加报修活动
    for repair in latest_repairs:
        activities.append({
            'type': 'repair',
            'title': f'新报修：{repair.title}',
            'description': f'学生 {repair.student.name if repair.student else "未知"} 提交了报修申请',
            'time': repair.created_at,
            'status': repair.status
        })
    
    # 添加访客活动
    for visitor in latest_visitors:
        activities.append({
            'type': 'visitor',
            'title': f'访客登记：{visitor.name}',
            'description': f'访客 {visitor.name} 访问了宿舍 {visitor.dorm_number}',
            'time': visitor.visit_date,
            'status': visitor.status
        })
    
    # 按时间排序
    activities.sort(key=lambda x: x['time'], reverse=True)
    
    return render_template('admin/dashboard.html', 
                         total_students=total_students,
                         total_dorms=total_dorms,
                         total_repairs=total_repairs,
                         pending_repairs=pending_repairs,
                         activities=activities[:8])

# 学生管理
@admin_bp.route('/students')
@login_required
def students():
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    students = Student.query.filter_by(is_deleted=False).all()  # 只显示未删除的学生
    return render_template('admin/students.html', students=students)

@admin_bp.route('/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    dormitories = Dormitory.query.all()
    
    if request.method == 'POST':
        # 获取表单数据
        student_id = request.form['student_id']
        name = request.form['name']
        gender = request.form['gender']
        major = request.form['major']
        grade = request.form['grade']
        dorm_id = request.form['dorm_id']
        phone = request.form['phone']
        
        # 创建用户账户
        username = student_id  # 使用学号作为用户名
        password = generate_password_hash('123456')  # 默认密码
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('学号已被使用！', 'danger')
            return redirect(url_for('admin.add_student'))
        
        # 创建用户
        user = User(
            username=username,
            password=password,
            role='student'
        )
        db.session.add(user)
        db.session.flush()  # 获取用户ID
        
        # 创建学生信息
        student = Student(
            user_id=user.id,
            student_id=student_id,
            name=name,
            gender=gender,
            major=major,
            grade=grade,
            dorm_id=dorm_id if dorm_id else None,
            phone=phone
        )
        
        db.session.add(student)
        db.session.commit()
        
        flash('学生添加成功！', 'success')
        return redirect(url_for('admin.students'))
    
    return render_template('admin/add_student.html', dormitories=dormitories)

@admin_bp.route('/students/delete/<int:student_id>')
@login_required
def delete_student(student_id):
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    student = Student.query.get_or_404(student_id)
    student.is_deleted = True  # 软删除
    student.user.is_deleted = True  # 同时软删除关联的用户
    db.session.commit()
    
    flash('学生删除成功！', 'success')
    return redirect(url_for('admin.students'))

@admin_bp.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    student = Student.query.get_or_404(student_id)
    dormitories = Dormitory.query.all()
    
    if request.method == 'POST':
        student.name = request.form['name']
        student.gender = request.form['gender']
        student.major = request.form['major']
        student.grade = request.form['grade']
        student.dorm_id = request.form['dorm_id'] if request.form['dorm_id'] else None
        student.phone = request.form['phone']
        
        db.session.commit()
        
        flash('学生信息更新成功！', 'success')
        return redirect(url_for('admin.students'))
    
    return render_template('admin/edit_student.html', student=student, dormitories=dormitories)

# 宿管管理
@admin_bp.route('/dorm_managers')
@login_required
def dorm_managers():
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    dorm_managers = DormManager.query.filter_by(is_deleted=False).all()  # 只显示未删除的宿管
    return render_template('admin/dorm_managers.html', dorm_managers=dorm_managers)

@admin_bp.route('/dorm_managers/add', methods=['GET', 'POST'])
@login_required
def add_dorm_manager():
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        phone = request.form['phone']
        responsible_building = request.form['responsible_building']
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在！', 'danger')
            return redirect(url_for('admin.add_dorm_manager'))
        
        # 创建用户
        user = User(
            username=username,
            password=generate_password_hash('123456'),  # 默认密码
            role='dorm_manager'
        )
        db.session.add(user)
        db.session.flush()  # 获取用户ID
        
        # 创建宿管信息
        dorm_manager = DormManager(
            user_id=user.id,
            name=name,
            phone=phone,
            responsible_building=responsible_building
        )
        db.session.add(dorm_manager)
        db.session.commit()
        
        flash('宿管添加成功！', 'success')
        return redirect(url_for('admin.dorm_managers'))
    
    return render_template('admin/add_dorm_manager.html')

@admin_bp.route('/dorm_managers/edit/<int:manager_id>', methods=['GET', 'POST'])
@login_required
def edit_dorm_manager(manager_id):
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    dorm_manager = DormManager.query.get_or_404(manager_id)
    
    if request.method == 'POST':
        dorm_manager.name = request.form['name']
        dorm_manager.phone = request.form['phone']
        dorm_manager.responsible_building = request.form['responsible_building']
        
        db.session.commit()
        
        flash('宿管信息更新成功！', 'success')
        return redirect(url_for('admin.dorm_managers'))
    
    return render_template('admin/edit_dorm_manager.html', dorm_manager=dorm_manager)

@admin_bp.route('/dorm_managers/delete/<int:manager_id>')
@login_required
def delete_dorm_manager(manager_id):
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    dorm_manager = DormManager.query.get_or_404(manager_id)
    dorm_manager.is_deleted = True  # 软删除
    dorm_manager.user.is_deleted = True  # 同时软删除关联的用户
    db.session.commit()
    
    flash('宿管删除成功！', 'success')
    return redirect(url_for('admin.dorm_managers'))

# 宿舍管理
@admin_bp.route('/dormitories')
@login_required
def dormitories():
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    dormitories = Dormitory.query.all()
    return render_template('admin/dormitories.html', dormitories=dormitories)

@admin_bp.route('/get_dorm_students/<int:dorm_id>')
@login_required
def get_dorm_students(dorm_id):
    if current_user.role != 'admin':
        return {'success': False, 'message': '无权访问！'}
    
    dormitory = Dormitory.query.get(dorm_id)
    if not dormitory:
        return {'success': False, 'message': '宿舍不存在！'}
    
    # 获取宿舍的所有学生
    students = dormitory.students
    
    # 转换为JSON格式
    student_list = []
    for student in students:
        student_list.append({
            'student_id': student.student_id,
            'name': student.name,
            'gender': student.gender,
            'major': student.major,
            'grade': student.grade,
            'phone': student.phone
        })
    
    return {
        'success': True,
        'dorm_number': dormitory.dorm_number,
        'students': student_list
    }

@admin_bp.route('/dormitories/add', methods=['GET', 'POST'])
@login_required
def add_dormitory():
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        dorm_number = request.form['dorm_number']
        building = request.form['building']
        floor = request.form['floor']
        gender = request.form['gender']
        capacity = request.form['capacity']
        
        # 检查宿舍号是否已存在
        if Dormitory.query.filter_by(dorm_number=dorm_number).first():
            flash('宿舍号已存在！', 'danger')
            return redirect(url_for('admin.add_dormitory'))
        
        # 创建宿舍
        dormitory = Dormitory(
            dorm_number=dorm_number,
            building=building,
            floor=floor,
            gender=gender,
            capacity=capacity,
            current_occupancy=0
        )
        
        db.session.add(dormitory)
        db.session.commit()
        
        flash('宿舍添加成功！', 'success')
        return redirect(url_for('admin.dormitories'))
    
    return render_template('admin/add_dormitory.html')

@admin_bp.route('/dormitories/edit/<int:dorm_id>', methods=['GET', 'POST'])
@login_required
def edit_dormitory(dorm_id):
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    dormitory = Dormitory.query.get_or_404(dorm_id)
    
    if request.method == 'POST':
        dormitory.dorm_number = request.form['dorm_number']
        dormitory.building = request.form['building']
        dormitory.floor = request.form['floor']
        dormitory.gender = request.form['gender']
        dormitory.capacity = request.form['capacity']
        
        db.session.commit()
        
        flash('宿舍信息更新成功！', 'success')
        return redirect(url_for('admin.dormitories'))
    
    return render_template('admin/edit_dormitory.html', dormitory=dormitory)

# 智能宿舍分配
@admin_bp.route('/smart_allocate_dorm', methods=['GET', 'POST'])
@login_required
def smart_allocate_dorm():
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        # 获取需要分配宿舍的学生列表（未分配宿舍的学生）
        unallocated_students = Student.query.filter_by(dorm_id=None).all()
        
        allocated_count = 0
        
        for student in unallocated_students:
            # 查找合适的宿舍：同性别、未满员、优先同专业同年级、其次同专业、再次同年级
            
            # 1. 优先查找同专业同年级、同性别、未满员的宿舍
            suitable_dorms = Dormitory.query.filter(
                Dormitory.gender == student.gender,
                Dormitory.current_occupancy < Dormitory.capacity
            ).join(Student).filter(
                Student.major == student.major,
                Student.grade == student.grade
            ).all()
            
            # 2. 如果没有同专业同年级的合适宿舍，查找同专业、同性别、未满员的宿舍
            if not suitable_dorms:
                suitable_dorms = Dormitory.query.filter(
                    Dormitory.gender == student.gender,
                    Dormitory.current_occupancy < Dormitory.capacity
                ).join(Student).filter(
                    Student.major == student.major
                ).all()
            
            # 3. 如果没有同专业的合适宿舍，查找同年级、同性别、未满员的宿舍
            if not suitable_dorms:
                suitable_dorms = Dormitory.query.filter(
                    Dormitory.gender == student.gender,
                    Dormitory.current_occupancy < Dormitory.capacity
                ).join(Student).filter(
                    Student.grade == student.grade
                ).all()
            
            # 4. 如果没有同年级的合适宿舍，查找同性别、未满员的宿舍
            if not suitable_dorms:
                suitable_dorms = Dormitory.query.filter(
                    Dormitory.gender == student.gender,
                    Dormitory.current_occupancy < Dormitory.capacity
                ).all()
            
            # 如果找到合适的宿舍，进行分配
            if suitable_dorms:
                # 选择人数最多的宿舍（优先填满宿舍）
                suitable_dorms.sort(key=lambda x: x.current_occupancy, reverse=True)
                selected_dorm = suitable_dorms[0]
                
                # 分配宿舍
                student.dorm_id = selected_dorm.id
                selected_dorm.current_occupancy += 1
                allocated_count += 1
        
        db.session.commit()
        
        flash(f'已完成 {allocated_count} 名学生的宿舍分配！', 'success')
        return redirect(url_for('admin.students'))
    
    # 统计未分配宿舍的学生数量
    unallocated_count = Student.query.filter_by(dorm_id=None).count()
    
    return render_template('admin/smart_allocate_dorm.html', unallocated_count=unallocated_count)

# 水电费管理
@admin_bp.route('/utility_bills')
@login_required
def utility_bills():
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    # 获取所有水电费账单
    bills = UtilityBill.query.order_by(UtilityBill.month.desc(), UtilityBill.dorm_id).all()
    
    return render_template('admin/utility_bills.html', bills=bills)

@admin_bp.route('/utility_bills/add', methods=['GET', 'POST'])
@login_required
def add_utility_bill():
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        dorm_id = request.form['dorm_id']
        month = request.form['month']
        electricity = float(request.form['electricity'])
        water = float(request.form['water'])
        
        # 计算费用（这里假设电费1元/度，水费2元/吨，实际可根据学校规定调整）
        electricity_cost = round(electricity * 1.0, 2)
        water_cost = round(water * 2.0, 2)
        total_cost = round(electricity_cost + water_cost, 2)
        
        # 检查是否已存在该宿舍该月份的账单
        existing_bill = UtilityBill.query.filter_by(dorm_id=dorm_id, month=month).first()
        if existing_bill:
            flash(f'该宿舍{month}月份的账单已存在！', 'danger')
            return redirect(url_for('admin.add_utility_bill'))
        
        # 创建水电费账单
        utility_bill = UtilityBill(
            dorm_id=dorm_id,
            month=month,
            electricity=electricity,
            water=water,
            electricity_cost=electricity_cost,
            water_cost=water_cost,
            total_cost=total_cost,
            due_date=datetime.strptime(f'{month}-28', '%Y-%m-%d')  # 假设每月28号到期
        )
        
        db.session.add(utility_bill)
        db.session.commit()
        
        flash('水电费账单添加成功！', 'success')
        return redirect(url_for('admin.utility_bills'))
    
    # 获取所有宿舍列表
    dormitories = Dormitory.query.order_by(Dormitory.building, Dormitory.dorm_number).all()
    
    return render_template('admin/add_utility_bill.html', dormitories=dormitories)

@admin_bp.route('/utility_bills/edit/<int:bill_id>', methods=['GET', 'POST'])
@login_required
def edit_utility_bill(bill_id):
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    bill = UtilityBill.query.get_or_404(bill_id)
    
    if request.method == 'POST':
        bill.dorm_id = request.form['dorm_id']
        bill.month = request.form['month']
        bill.electricity = float(request.form['electricity'])
        bill.water = float(request.form['water'])
        
        # 重新计算费用
        bill.electricity_cost = round(bill.electricity * 1.0, 2)
        bill.water_cost = round(bill.water * 2.0, 2)
        bill.total_cost = round(bill.electricity_cost + bill.water_cost, 2)
        
        db.session.commit()
        
        flash('水电费账单更新成功！', 'success')
        return redirect(url_for('admin.utility_bills'))
    
    # 获取所有宿舍列表
    dormitories = Dormitory.query.order_by(Dormitory.building, Dormitory.dorm_number).all()
    
    return render_template('admin/edit_utility_bill.html', bill=bill, dormitories=dormitories)

@admin_bp.route('/utility_bills/delete/<int:bill_id>')
@login_required
def delete_utility_bill(bill_id):
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    bill = UtilityBill.query.get_or_404(bill_id)
    
    db.session.delete(bill)
    db.session.commit()
    
    flash('水电费账单删除成功！', 'success')
    return redirect(url_for('admin.utility_bills'))

@admin_bp.route('/utility_bills/statistics')
@login_required
def utility_bills_statistics():
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    # 统计数据
    from collections import defaultdict
    
    # 获取所有账单
    bills = UtilityBill.query.all()
    
    # 计算总费用
    total_electricity = sum(bill.electricity for bill in bills)
    total_water = sum(bill.water for bill in bills)
    total_electricity_cost = sum(bill.electricity_cost for bill in bills)
    total_water_cost = sum(bill.water_cost for bill in bills)
    total_cost = sum(bill.total_cost for bill in bills)
    
    # 按楼栋统计
    building_stats = defaultdict(lambda: {
        'electricity': 0,
        'water': 0,
        'electricity_cost': 0,
        'water_cost': 0,
        'total_cost': 0
    })
    
    for bill in bills:
        building = bill.dormitory.building
        building_stats[building]['electricity'] += bill.electricity
        building_stats[building]['water'] += bill.water
        building_stats[building]['electricity_cost'] += bill.electricity_cost
        building_stats[building]['water_cost'] += bill.water_cost
        building_stats[building]['total_cost'] += bill.total_cost
    
    # 按月份统计
    monthly_stats = defaultdict(lambda: {
        'electricity': 0,
        'water': 0,
        'electricity_cost': 0,
        'water_cost': 0,
        'total_cost': 0
    })
    
    for bill in bills:
        monthly_stats[bill.month]['electricity'] += bill.electricity
        monthly_stats[bill.month]['water'] += bill.water
        monthly_stats[bill.month]['electricity_cost'] += bill.electricity_cost
        monthly_stats[bill.month]['water_cost'] += bill.water_cost
        monthly_stats[bill.month]['total_cost'] += bill.total_cost
    
    return render_template('admin/utility_bills_statistics.html',
                         total_electricity=total_electricity,
                         total_water=total_water,
                         total_electricity_cost=total_electricity_cost,
                         total_water_cost=total_water_cost,
                         total_cost=total_cost,
                         building_stats=building_stats,
                         monthly_stats=monthly_stats)

@admin_bp.route('/payments')
@login_required
def payments():
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    # 获取所有缴费记录
    payments = Payment.query.order_by(Payment.payment_date.desc()).all()
    
    return render_template('admin/payments.html', payments=payments)

# 报修管理
@admin_bp.route('/repairs')
@login_required
def repairs():
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    repairs = Repair.query.filter_by(is_deleted=False).all()  # 只显示未删除的报修
    return render_template('admin/repairs.html', repairs=repairs)

@admin_bp.route('/get_repair_details/<int:repair_id>')
@login_required
def get_repair_details(repair_id):
    if current_user.role != 'admin':
        return {'success': False, 'message': '无权访问！'}
    
    repair = Repair.query.get(repair_id)
    if not repair:
        return {'success': False, 'message': '保修记录不存在！'}
    
    # 获取相关信息
    student_name = repair.student.name if repair.student else '未知'
    dorm_number = repair.dormitory.dorm_number if repair.dormitory else '未知'
    
    # 状态文本映射
    status_map = {
        'pending': '待处理',
        'processing': '处理中',
        'completed': '已完成'
    }
    
    # 位置类型映射
    location_type_map = {
        'dorm': '宿舍',
        'training': '实训楼',
        'teaching': '教学楼',
        'other': '其他'
    }
    
    # 报修类型映射
    repair_type_map = {
        'water': '水管',
        'air_conditioner': '空调',
        'furniture': '家具',
        'network': '网络',
        'other': '其他'
    }
    
    # 紧急程度映射
    urgent_level_map = {
        'normal': '普通',
        'urgent': '紧急',
        'very_urgent': '非常紧急'
    }
    
    repair_data = {
        'title': repair.title,
        'student_name': student_name,
        'contact_phone': repair.contact_phone,
        'dorm_number': dorm_number,
        'location_type': location_type_map.get(repair.location_type, repair.location_type),
        'repair_type': repair_type_map.get(repair.repair_type, repair.repair_type),
        'location_detail': repair.location_detail,
        'urgent_level': urgent_level_map.get(repair.urgent_level, repair.urgent_level),
        'status': repair.status,
        'status_text': status_map.get(repair.status, repair.status),
        'created_at': repair.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': repair.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        'content': repair.content
    }
    
    return {'success': True, 'repair': repair_data}

@admin_bp.route('/process_repair', methods=['POST'])
@login_required
def process_repair():
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    repair_id = request.form['repair_id']
    status = request.form['status']
    
    repair = Repair.query.get(repair_id)
    if not repair:
        flash('保修记录不存在！', 'danger')
        return redirect(url_for('admin.repairs'))
    
    # 更新状态
    repair.status = status
    db.session.commit()
    
    flash('保修状态更新成功！', 'success')
    return redirect(url_for('admin.repairs'))

# 访客管理
@admin_bp.route('/visitors')
@login_required
def visitors():
    if current_user.role != 'admin':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    visitors = Visitor.query.filter_by(is_deleted=False).all()  # 只显示未删除的访客
    return render_template('admin/visitors.html', visitors=visitors)

@admin_bp.route('/get_visitor_details/<int:visitor_id>')
@login_required
def get_visitor_details(visitor_id):
    if current_user.role != 'admin':
        return {'success': False, 'message': '无权访问！'}
    
    visitor = Visitor.query.get(visitor_id)
    if not visitor:
        return {'success': False, 'message': '访客记录不存在！'}
    
    # 状态文本映射
    status_map = {
        'in': '在访',
        'out': '已离开'
    }
    
    visitor_data = {
        'name': visitor.name,
        'id_card': visitor.id_card,
        'phone': visitor.phone,
        'visit_date': visitor.visit_date.strftime('%Y-%m-%d %H:%M:%S'),
        'leave_date': visitor.leave_date.strftime('%Y-%m-%d %H:%M:%S') if visitor.leave_date else '未离开',
        'purpose': visitor.purpose,
        'dorm_number': visitor.dorm_number,
        'student_name': visitor.student_name,
        'status': visitor.status,
        'status_text': status_map.get(visitor.status, visitor.status)
    }
    
    return {'success': True, 'visitor': visitor_data}

@admin_bp.route('/mark_visitor_leave/<int:visitor_id>', methods=['POST'])
@login_required
def mark_visitor_leave(visitor_id):
    if current_user.role != 'admin':
        return {'success': False, 'message': '无权访问！'}
    
    visitor = Visitor.query.get(visitor_id)
    if not visitor:
        return {'success': False, 'message': '访客记录不存在！'}
    
    # 更新访客状态为已离开，并记录离开时间
    visitor.status = 'out'
    visitor.leave_date = datetime.utcnow()
    db.session.commit()
    
    return {'success': True, 'message': '标记成功！'}