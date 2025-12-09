# 配置文件
import os
import tempfile

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    # 使用SQLite数据库，适合云部署
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), '../instance/database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 模板和静态文件配置
    TEMPLATES_AUTO_RELOAD = True
    STATIC_FOLDER = 'static'
    TEMPLATE_FOLDER = 'templates'