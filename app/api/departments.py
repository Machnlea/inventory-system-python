from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.crud import departments
from app.schemas.schemas import Department, DepartmentCreate, DepartmentUpdate
from app.api.auth import get_current_admin_user, get_current_user

router = APIRouter()

@router.get("/", response_model=List[Department])
def read_departments(skip: int = 0, limit: int = 100,
                    db: Session = Depends(get_db),
                    current_user = Depends(get_current_user)):
    return departments.get_departments(db, skip=skip, limit=limit)

@router.post("/", response_model=Department)
def create_department(department: DepartmentCreate,
                     db: Session = Depends(get_db),
                     current_user = Depends(get_current_admin_user)):
    # 检查部门名称是否已存在
    db_department = departments.get_department_by_name(db, name=department.name)
    if db_department:
        raise HTTPException(status_code=400, detail="Department name already exists")
    
    # 创建部门
    db_department = departments.create_department(db=db, department=department)
    
    # 自动为新创建的部门创建用户账号
    try:
        from app.crud import department_users
        department_users.create_department_user(db, db_department.id)
    except Exception as e:
        # 如果创建用户失败，记录错误但不影响部门创建
        print(f"警告：为部门 {db_department.name} 创建用户账号失败: {e}")
    
    return db_department

@router.get("/with-counts")
def get_departments_with_counts(skip: int = 0, limit: int = 100,
                               db: Session = Depends(get_db),
                               current_user = Depends(get_current_user)):
    return departments.get_department_with_equipment_count(db, skip=skip, limit=limit)

@router.get("/{department_id}", response_model=Department)
def read_department(department_id: int,
                   db: Session = Depends(get_db),
                   current_user = Depends(get_current_user)):
    db_department = departments.get_department(db, department_id=department_id)
    if db_department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return db_department

@router.put("/{department_id}", response_model=Department)
def update_department(department_id: int, department: DepartmentUpdate,
                     db: Session = Depends(get_db),
                     current_user = Depends(get_current_admin_user)):
    db_department = departments.update_department(db, department_id=department_id, department=department)
    if db_department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return db_department

@router.delete("/{department_id}")
def delete_department(department_id: int,
                     db: Session = Depends(get_db),
                     current_user = Depends(get_current_admin_user)):
    success, message = departments.delete_department(db, department_id=department_id)
    if success:
        return {"message": message}
    else:
        raise HTTPException(status_code=400, detail=message)