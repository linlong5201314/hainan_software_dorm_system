from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.models import User, DormManager, Student, Dormitory, Repair, Visitor, DormChangeRequest
from werkzeug.security import generate_password_hash
from datetime import datetime

dorm_manager_bp = Blueprint('dorm_manager', __name__)

@dorm_manager_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'dorm_manager':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    dorm_manager = DormManager.query.filter_by(user_id=current_user.id).first()
    
    # 统计数据
    # 本楼栋学生数量
    total_students = Student.query.join(Dormitory).filter(
        Dormitory.building == dorm_manager.responsible_building
    ).count()
    
    # 本楼栋宿舍数量
    total_dorms = Dormitory.query.filter_by(building=dorm_manager.responsible_building).count()
    
    # 本楼栋待处理报修数量
    pending_repairs = Repair.query.join(Dormitory).filter(
        Dormitory.building == dorm_manager.responsible_building,
        Repair.status == 'pending'
    ).count()
    
    # 本楼栋在访访客数量
    current_visitors = Visitor.query.filter_by(
        dorm_number=Dormitory.dorm_number,
        status='in'
    ).join(Dormitory).filter(
        Dormitory.building == dorm_manager.responsible_building
    ).count()
    
    # 获取最新活动
    latest_repairs = Repair.query.join(Dormitory).filter(
        Dormitory.building == dorm_manager.responsible_building
    ).order_by(Repair.created_at.desc()).limit(5).all()
    
    latest_visitors = Visitor.query.join(Dormitory).filter(
        Dormitory.building == dorm_manager.responsible_building
    ).order_by(Visitor.visit_date.desc()).limit(5).all()
    
    latest_dorm_changes = DormChangeRequest.query.join(Student).join(Dormitory).filter(
        Dormitory.building == dorm_manager.responsible_building
    ).order_by(DormChangeRequest.created_at.desc()).limit(5).all()
    
    return render_template('dorm_manager/dashboard.html', 
                         dorm_manager=dorm_manager,
                         total_students=total_students,
                         total_dorms=total_dorms,
                         pending_repairs=pending_repairs,
                         current_visitors=current_visitors,
                         latest_repairs=latest_repairs,
                         latest_visitors=latest_visitors,
                         latest_dorm_changes=latest_dorm_changes)

# 学生管理
@dorm_manager_bp.route('/students')
@login_required
def students():
    if current_user.role != 'dorm_manager':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    dorm_manager = DormManager.query.filter_by(user_id=current_user.id).first()
    
    # 获取本楼栋的所有学生
    students = Student.query.join(Dormitory).filter(
        Dormitory.building == dorm_manager.responsible_building,
        Student.is_deleted == False
    ).all()
    
    return render_template('dorm_manager/students.html', students=students, dorm_manager=dorm_manager)

# 宿舍管理
@dorm_manager_bp.route('/dormitories')
@login_required
def dormitories():
    if current_user.role != 'dorm_manager':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    dorm_manager = DormManager.query.filter_by(user_id=current_user.id).first()
    
    # 获取本楼栋的所有宿舍
    dormitories = Dormitory.query.filter_by(building=dorm_manager.responsible_building).all()
    
    return render_template('dorm_manager/dormitories.html', dormitories=dormitories, dorm_manager=dorm_manager)

@dorm_manager_bp.route('/get_dorm_students/<int:dorm_id>')
@login_required
def get_dorm_students(dorm_id):
    if current_user.role != 'dorm_manager':
        return {'success': False, 'message': '无权访问！'}
    
    dorm_manager = DormManager.query.filter_by(user_id=current_user.id).first()
    dormitory = Dormitory.query.get(dorm_id)
    
    # 检查宿舍是否属于当前宿管负责的楼栋
    if not dormitory or dormitory.building != dorm_manager.responsible_building:
        return {'success': False, 'message': '宿舍不存在或无权访问！'}
    
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

# 报修管理
@dorm_manager_bp.route('/repairs')
@login_required
def repairs():
    if current_user.role != 'dorm_manager':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    dorm_manager = DormManager.query.filter_by(user_id=current_user.id).first()
    
    # 获取本楼栋的所有报修
    repairs = Repair.query.join(Dormitory).filter(
        Dormitory.building == dorm_manager.responsible_building,
        Repair.is_deleted == False
    ).all()
    
    return render_template('dorm_manager/repairs.html', repairs=repairs, dorm_manager=dorm_manager)

@dorm_manager_bp.route('/process_repair', methods=['POST'])
@login_required
def process_repair():
    if current_user.role != 'dorm_manager':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    repair_id = request.form['repair_id']
    status = request.form['status']
    
    repair = Repair.query.get(repair_id)
    if not repair:
        flash('保修记录不存在！', 'danger')
        return redirect(url_for('dorm_manager.repairs'))
    
    # 更新状态
    repair.status = status
    db.session.commit()
    
    flash('保修状态更新成功！', 'success')
    return redirect(url_for('dorm_manager.repairs'))

# 访客管理
@dorm_manager_bp.route('/visitors')
@login_required
def visitors():
    if current_user.role != 'dorm_manager':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    dorm_manager = DormManager.query.filter_by(user_id=current_user.id).first()
    
    # 获取本楼栋的所有访客
    visitors = Visitor.query.join(Dormitory).filter(
        Dormitory.building == dorm_manager.responsible_building,
        Visitor.is_deleted == False
    ).all()
    
    return render_template('dorm_manager/visitors.html', visitors=visitors, dorm_manager=dorm_manager)

@dorm_manager_bp.route('/mark_visitor_leave/<int:visitor_id>', methods=['POST'])
@login_required
def mark_visitor_leave(visitor_id):
    if current_user.role != 'dorm_manager':
        return {'success': False, 'message': '无权访问！'}
    
    visitor = Visitor.query.get(visitor_id)
    if not visitor:
        return {'success': False, 'message': '访客记录不存在！'}
    
    # 更新访客状态为已离开，并记录离开时间
    visitor.status = 'out'
    visitor.leave_date = datetime.utcnow()
    db.session.commit()
    
    return {'success': True, 'message': '标记成功！'}

# 宿舍调换申请管理
@dorm_manager_bp.route('/dorm_change_requests')
@login_required
def dorm_change_requests():
    if current_user.role != 'dorm_manager':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    dorm_manager = DormManager.query.filter_by(user_id=current_user.id).first()
    
    # 获取本楼栋的所有宿舍调换申请
    requests = DormChangeRequest.query.join(Student).join(Dormitory).filter(
        Dormitory.building == dorm_manager.responsible_building
    ).all()
    
    return render_template('dorm_manager/dorm_change_requests.html', requests=requests, dorm_manager=dorm_manager)

@dorm_manager_bp.route('/approve_dorm_change/<int:request_id>', methods=['POST'])
@login_required
def approve_dorm_change(request_id):
    if current_user.role != 'dorm_manager':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    dorm_change_request = DormChangeRequest.query.get(request_id)
    if not dorm_change_request:
        flash('申请不存在！', 'danger')
        return redirect(url_for('dorm_manager.dorm_change_requests'))
    
    # 更新申请状态
    dorm_change_request.status = 'approved'
    dorm_change_request.approved_by = current_user.id
    dorm_change_request.updated_at = datetime.utcnow()
    
    # 执行宿舍调换
    student = dorm_change_request.student
    old_dorm = dorm_change_request.current_dorm
    new_dorm = dorm_change_request.target_dorm
    
    if old_dorm:
        old_dorm.current_occupancy -= 1
    
    if new_dorm:
        new_dorm.current_occupancy += 1
        student.dorm_id = new_dorm.id
    
    db.session.commit()
    
    flash('宿舍调换申请已批准！', 'success')
    return redirect(url_for('dorm_manager.dorm_change_requests'))

@dorm_manager_bp.route('/reject_dorm_change/<int:request_id>', methods=['POST'])
@login_required
def reject_dorm_change(request_id):
    if current_user.role != 'dorm_manager':
        flash('无权访问！', 'danger')
        return redirect(url_for('main.login'))
    
    dorm_change_request = DormChangeRequest.query.get(request_id)
    if not dorm_change_request:
        flash('申请不存在！', 'danger')
        return redirect(url_for('dorm_manager.dorm_change_requests'))
    
    # 更新申请状态
    dorm_change_request.status = 'rejected'
    dorm_change_request.approved_by = current_user.id
    dorm_change_request.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('宿舍调换申请已拒绝！', 'success')
    return redirect(url_for('dorm_manager.dorm_change_requests'))
