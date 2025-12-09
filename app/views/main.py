from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.models import User
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return redirect(url_for('main.login'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['userType']
        
        user = User.query.filter_by(username=username, role=user_type).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('登录成功！', 'success')
            
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'dorm_manager':
                return redirect(url_for('dorm_manager.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        else:
            flash('用户名、密码或用户类型错误！', 'danger')
    
    return render_template('login.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录！', 'success')
    return redirect(url_for('main.login'))

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        user_type = request.form['userType']
        phone = request.form['phone']
        
        # 验证密码
        if password != confirm_password:
            flash('两次输入的密码不一致！', 'danger')
        else:
            # 检查用户名是否已存在
            if User.query.filter_by(username=username).first():
                flash('用户名已存在！', 'danger')
            else:
                # 创建用户
                user = User(
                    username=username,
                    password=generate_password_hash(password),
                    role=user_type
                )
                
                db.session.add(user)
                db.session.flush()  # 获取用户ID
                
                # 根据用户类型创建对应的信息
                if user_type == 'student':
                    from app.models.models import Student
                    student = Student(
                        user_id=user.id,
                        student_id=username,  # 使用用户名作为学号
                        name=name,
                        gender='男',  # 默认值，后续可以修改
                        major='未分配',  # 默认值
                        grade='未分配',  # 默认值
                        phone=phone
                    )
                    db.session.add(student)
                elif user_type == 'dorm_manager':
                    from app.models.models import DormManager
                    dorm_manager = DormManager(
                        user_id=user.id,
                        name=name,
                        phone=phone,
                        responsible_building='未分配'  # 默认值，后续可以修改
                    )
                    db.session.add(dorm_manager)
                
                db.session.commit()
                
                flash('注册成功！请登录', 'success')
                return redirect(url_for('main.login'))
    
    return render_template('login.html')

@main_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        
        # 这里简化处理，实际项目中应该发送重置链接到邮箱
        flash('密码重置链接已发送到您的邮箱，请查收！', 'success')
        return redirect(url_for('main.login'))
    
    return redirect(url_for('main.login'))