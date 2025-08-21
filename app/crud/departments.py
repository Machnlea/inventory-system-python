from sqlalchemy.orm import Session
from app.models.models import Department
from app.schemas.schemas import DepartmentCreate
from typing import List

def get_departments(db: Session, skip: int = 0, limit: int = 100):
    departments = db.query(Department).offset(skip).limit(limit).all()
    
    # 转换为字典并确保包含所有字段
    result = []
    for department in departments:
        department_dict = {
            "id": department.id,
            "name": department.name,
            "code": department.code,
            "description": department.description,
            "created_at": department.created_at
        }
        result.append(department_dict)
    
    return result

def get_department(db: Session, department_id: int):
    return db.query(Department).filter(Department.id == department_id).first()

def get_department_by_name(db: Session, name: str):
    return db.query(Department).filter(Department.name == name).first()

def create_department(db: Session, department: DepartmentCreate):
    db_department = Department(**department.dict())
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department

def update_department(db: Session, department_id: int, department: DepartmentCreate):
    db_department = db.query(Department).filter(Department.id == department_id).first()
    if db_department:
        for field, value in department.dict().items():
            setattr(db_department, field, value)
        db.commit()
        db.refresh(db_department)
    return db_department

def delete_department(db: Session, department_id: int):
    from app.models.models import Equipment
    
    try:
        # 检查该部门下是否有设备
        equipment_exists = db.query(Equipment).filter(Equipment.department_id == department_id).first()
        
        if equipment_exists:
            return False, "无法删除该部门，该部门下还有设备"
        
        db_department = db.query(Department).filter(Department.id == department_id).first()
        if db_department:
            db.delete(db_department)
            db.commit()
            return True, "部门删除成功"
        return False, "部门不存在"
    except Exception as e:
        db.rollback()
        return False, f"删除部门时发生错误: {str(e)}"

def get_department_with_equipment_count(db: Session, skip: int = 0, limit: int = 100):
    """获取部门及其设备数量"""
    from app.models.models import Equipment
    from sqlalchemy import func
    
    result = db.query(
        Department,
        func.count(Equipment.id).label('equipment_count')
    ).outerjoin(Equipment).group_by(Department.id).offset(skip).limit(limit).all()
    
    departments_with_count = []
    for department, count in result:
        department_dict = {
            "id": department.id,
            "name": department.name,
            "code": department.code,  # 添加部门编号字段
            "description": department.description,
            "created_at": department.created_at,
            "equipment_count": count
        }
        departments_with_count.append(department_dict)
    
    return departments_with_count