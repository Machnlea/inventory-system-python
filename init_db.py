from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.models import models
from app.crud import users, departments, categories
from app.schemas.schemas import UserCreate, DepartmentCreate, EquipmentCategoryCreate
from app.core.config import settings

def init_db():
    # 创建数据库表
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 创建默认管理员用户
        admin_user = users.get_user_by_username(db, settings.ADMIN_USERNAME)
        if not admin_user:
            admin_user_data = UserCreate(
                username=settings.ADMIN_USERNAME,
                password=settings.ADMIN_PASSWORD,
                is_admin=True
            )
            users.create_user(db, admin_user_data)
            print(f"创建默认管理员用户: {settings.ADMIN_USERNAME}")
        
        # 创建默认部门
        default_departments = [
            {"name": "树脂车间（高温）", "description": "高温树脂生产车间"},
            {"name": "树脂车间（低温）", "description": "低温树脂生产车间"},
            {"name": "工业漆车间", "description": "工业漆生产车间"},
            {"name": "防腐车间", "description": "防腐产品生产车间"},
            {"name": "汽摩车间", "description": "汽摩产品生产车间"},
            {"name": "通用漆车间", "description": "通用漆生产车间"},
            {"name": "安环部", "description": "安全环保部门"},
            {"name": "物管部", "description": "物资管理部门"}
        ]
        
        for dept_data in default_departments:
            existing_dept = departments.get_department_by_name(db, dept_data["name"])
            if not existing_dept:
                dept_create = DepartmentCreate(**dept_data)
                departments.create_department(db, dept_create)
                print(f"创建部门: {dept_data['name']}")
        
        # 创建默认设备类别
        default_categories = [
            {"name": "铂热电阻", "description": "铂热电阻温度计"},
            {"name": "玻璃量器", "description": "玻璃量杯、量筒等"},
            {"name": "电子天平", "description": "精密电子天平"},
            {"name": "压力表", "description": "各类压力测量仪表"},
            {"name": "流量计", "description": "流量测量设备"},
            {"name": "液位计", "description": "液位测量设备"}
        ]
        
        for cat_data in default_categories:
            existing_cat = categories.get_category_by_name(db, cat_data["name"])
            if not existing_cat:
                cat_create = EquipmentCategoryCreate(**cat_data)
                categories.create_category(db, cat_create)
                print(f"创建设备类别: {cat_data['name']}")
        
        print("数据库初始化完成")
        
    finally:
        db.close()

if __name__ == "__main__":
    init_db()