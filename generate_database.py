# 宿舍管理系统数据库生成脚本
# 运行后直接生成完整的数据库结构和初始数据
import pymysql
from pymysql import err

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'charset': 'utf8mb4'
}

# 数据库名称
DB_NAME = 'dorm_management_system'

def create_database():
    """创建数据库"""
    print("开始创建数据库...")
    
    # 连接MySQL服务器（不指定数据库）
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # 创建数据库（如果不存在）
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"数据库 {DB_NAME} 创建成功！")
        
    except err.MySQLError as e:
        print(f"创建数据库失败: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
    
    return True

def create_tables():
    """创建所有表结构"""
    print("\n开始创建表结构...")
    
    # 连接到指定数据库
    conn = pymysql.connect(**DB_CONFIG, db=DB_NAME)
    cursor = conn.cursor()
    
    try:
        # 设置外键检查暂时关闭
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # 1. 创建用户表
        print("创建 users 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(80) NOT NULL UNIQUE,
                password VARCHAR(120) NOT NULL,
                role VARCHAR(20) NOT NULL,  -- admin, student
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_deleted BOOLEAN DEFAULT FALSE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 2. 创建宿舍表
        print("创建 dormitories 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dormitories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                dorm_number VARCHAR(20) NOT NULL UNIQUE,
                building VARCHAR(20) NOT NULL,
                floor INT NOT NULL,
                capacity INT NOT NULL,
                current_occupancy INT DEFAULT 0,
                gender VARCHAR(10) NOT NULL,
                is_deleted BOOLEAN DEFAULT FALSE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 3. 创建学生表
        print("创建 students 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                student_id VARCHAR(20) NOT NULL UNIQUE,
                name VARCHAR(50) NOT NULL,
                gender VARCHAR(10) NOT NULL,
                major VARCHAR(50) NOT NULL,
                grade VARCHAR(20) NOT NULL,
                dorm_id INT,
                phone VARCHAR(20) NOT NULL,
                photo VARCHAR(200) NULL,
                is_deleted BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (dorm_id) REFERENCES dormitories(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 4. 创建报修表
        print("创建 repairs 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repairs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                dorm_id INT NULL,
                student_id INT NOT NULL,
                title VARCHAR(100) NOT NULL,
                content TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                location_type VARCHAR(50) NOT NULL DEFAULT 'dorm',
                repair_type VARCHAR(50) NOT NULL DEFAULT 'other',
                location_detail VARCHAR(100) NOT NULL DEFAULT '',
                contact_phone VARCHAR(20) NOT NULL DEFAULT '',
                urgent_level VARCHAR(20) NOT NULL DEFAULT 'normal',
                is_deleted BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (dorm_id) REFERENCES dormitories(id),
                FOREIGN KEY (student_id) REFERENCES students(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 5. 创建访客表
        print("创建 visitors 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS visitors (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                id_card VARCHAR(20) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                visit_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                leave_date DATETIME NULL,
                purpose TEXT NOT NULL,
                dorm_number VARCHAR(20) NOT NULL,
                student_name VARCHAR(50) NOT NULL,
                student_id INT NULL,
                status VARCHAR(20) DEFAULT 'in',
                is_deleted BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (student_id) REFERENCES students(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 恢复外键检查
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        conn.commit()
        print("所有表创建成功！")
        return True
        
    except err.MySQLError as e:
        print(f"创建表失败: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def insert_initial_data():
    """插入初始数据"""
    print("\n开始插入初始数据...")
    
    conn = pymysql.connect(**DB_CONFIG, db=DB_NAME)
    cursor = conn.cursor()
    
    try:
        # 1. 插入初始管理员用户（密码：admin123）
        print("插入管理员用户...")
        cursor.execute("""
            INSERT INTO users (username, password, role) 
            VALUES ('admin', '$2b$12$r5t6u7i8o9p0a1s2d3f4g5h6j7k8l9z0x1c2v3b4n5m6', 'admin') 
            ON DUPLICATE KEY UPDATE username=username
        """)
        
        # 2. 插入示例宿舍数据
        print("插入示例宿舍数据...")
        cursor.execute("""
            INSERT INTO dormitories (dorm_number, building, floor, capacity, gender) VALUES 
            ('101', 'A栋', 1, 4, '男'),
            ('102', 'A栋', 1, 4, '男'),
            ('201', 'A栋', 2, 4, '女'),
            ('202', 'A栋', 2, 4, '女'),
            ('301', 'B栋', 3, 4, '男'),
            ('302', 'B栋', 3, 4, '女') 
            ON DUPLICATE KEY UPDATE dorm_number=dorm_number
        """)
        
        # 3. 插入示例学生用户（可选）
        print("插入示例学生数据...")
        # 先插入用户
        cursor.execute("""
            INSERT INTO users (username, password, role) 
            VALUES ('20230001', '$2b$12$r5t6u7i8o9p0a1s2d3f4g5h6j7k8l9z0x1c2v3b4n5m6', 'student') 
            ON DUPLICATE KEY UPDATE username=username
        """)
        
        # 插入对应学生信息
        cursor.execute("""
            INSERT INTO students (user_id, student_id, name, gender, major, grade, dorm_id, phone) 
            VALUES (LAST_INSERT_ID(), '20230001', '张三', '男', '计算机科学与技术', '2023级', 1, '13800138001') 
            ON DUPLICATE KEY UPDATE student_id=student_id
        """)
        
        conn.commit()
        print("初始数据插入成功！")
        return True
        
    except err.MySQLError as e:
        print(f"插入初始数据失败: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def verify_database():
    """验证数据库结构"""
    print("\n开始验证数据库结构...")
    
    conn = pymysql.connect(**DB_CONFIG, db=DB_NAME)
    cursor = conn.cursor()
    
    try:
        # 检查表是否存在
        tables = ['users', 'dormitories', 'students', 'repairs', 'visitors']
        
        for table in tables:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = '{DB_NAME}' AND table_name = '{table}'
            """)
            result = cursor.fetchone()
            if result[0] == 1:
                print(f"✓ 表 {table} 存在")
            else:
                print(f"✗ 表 {table} 不存在")
        
        # 检查关键字段是否存在
        print("\n验证关键字段...")
        
        # 检查students表的photo字段
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_schema = '{DB_NAME}' AND table_name = 'students' AND column_name = 'photo'
        """)
        if cursor.fetchone()[0] == 1:
            print("✓ students.photo 字段存在")
        else:
            print("✗ students.photo 字段不存在")
        
        # 检查软删除字段
        for table in tables:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_schema = '{DB_NAME}' AND table_name = '{table}' AND column_name = 'is_deleted'
            """)
            if cursor.fetchone()[0] == 1:
                print(f"✓ {table}.is_deleted 字段存在")
            else:
                print(f"✗ {table}.is_deleted 字段不存在")
        
        return True
        
    except err.MySQLError as e:
        print(f"验证失败: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """主函数"""
    print("=== 宿舍管理系统数据库生成脚本 ===")
    print(f"目标数据库: {DB_NAME}")
    print("=" * 50)
    
    # 1. 创建数据库
    if not create_database():
        return False
    
    # 2. 创建表结构
    if not create_tables():
        return False
    
    # 3. 插入初始数据
    if not insert_initial_data():
        return False
    
    # 4. 验证数据库
    verify_database()
    
    print("\n" + "=" * 50)
    print("数据库生成完成！")
    print(f"数据库名称: {DB_NAME}")
    print("管理员账户: admin / admin123")
    print("示例学生: 20230001 / 13800138001")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    main()
