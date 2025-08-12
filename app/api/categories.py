from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.crud import categories
from app.schemas.schemas import EquipmentCategory, EquipmentCategoryCreate
from app.api.auth import get_current_admin_user, get_current_user

router = APIRouter()

@router.get("/", response_model=List[EquipmentCategory])
def read_categories(skip: int = 0, limit: int = 100,
                   db: Session = Depends(get_db),
                   current_user = Depends(get_current_user)):
    return categories.get_categories(db, skip=skip, limit=limit)

@router.post("/", response_model=EquipmentCategory)
def create_category(category: EquipmentCategoryCreate,
                   db: Session = Depends(get_db),
                   current_user = Depends(get_current_admin_user)):
    db_category = categories.get_category_by_name(db, name=category.name)
    if db_category:
        raise HTTPException(status_code=400, detail="Category name already exists")
    return categories.create_category(db=db, category=category)

@router.get("/with-counts")
def get_categories_with_counts(skip: int = 0, limit: int = 100,
                              db: Session = Depends(get_db),
                              current_user = Depends(get_current_user)):
    return categories.get_category_with_equipment_count(db, skip=skip, limit=limit)

@router.get("/{category_id}", response_model=EquipmentCategory)
def read_category(category_id: int,
                 db: Session = Depends(get_db),
                 current_user = Depends(get_current_user)):
    db_category = categories.get_category(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category

@router.put("/{category_id}", response_model=EquipmentCategory)
def update_category(category_id: int, category: EquipmentCategoryCreate,
                   db: Session = Depends(get_db),
                   current_user = Depends(get_current_admin_user)):
    db_category = categories.update_category(db, category_id=category_id, category=category)
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category

@router.delete("/{category_id}")
def delete_category(category_id: int,
                   db: Session = Depends(get_db),
                   current_user = Depends(get_current_admin_user)):
    success, message = categories.delete_category(db, category_id=category_id)
    if success:
        return {"message": message}
    else:
        raise HTTPException(status_code=400, detail=message)