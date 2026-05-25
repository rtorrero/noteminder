from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
import uuid

import os
from . import models, schemas, database

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

APP_TITLE = os.getenv("APP_TITLE", "Noteminder TODO API")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

app = FastAPI(title=APP_TITLE, version=APP_VERSION)


# Dependency (imported from app/database.py)
get_db = database.get_db


# Helper function to get or create default status
def get_pending_status_id(db: Session) -> str:
    pending = db.query(models.Status).filter(models.Status.name == "pending").first()
    if not pending:
        # Seed default statuses if not exists
        seed_default_data(db)
        pending = db.query(models.Status).filter(models.Status.name == "pending").first()
    return pending.id


def seed_default_data(db: Session):
    """Seed database with default categories and statuses."""
    # Default statuses
    default_statuses = ["pending", "in_progress", "completed", "blocked"]
    for status_name in default_statuses:
        existing = db.query(models.Status).filter(models.Status.name == status_name).first()
        if not existing:
            status = models.Status(id=str(uuid.uuid4()), name=status_name)
            db.add(status)

    # Default categories
    default_categories = ["home", "personal", "learning", "shopping", "work"]
    for cat_name in default_categories:
        existing = db.query(models.Category).filter(models.Category.name == cat_name).first()
        if not existing:
            category = models.Category(id=str(uuid.uuid4()), name=cat_name)
            db.add(category)

    db.commit()


# Initialize default data
@app.on_event("startup")
def on_startup():
    db = database.SessionLocal()
    try:
        seed_default_data(db)
    finally:
        db.close()


# ============ PROJECT ENDPOINTS ============

@app.post("/projects", response_model=schemas.ProjectResponse, status_code=201)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    db_project = models.Project(
        id=str(uuid.uuid4()),
        name=project.name,
        description=project.description
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@app.get("/projects", response_model=List[schemas.ProjectResponse])
def read_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()


@app.get("/projects/{project_id}", response_model=schemas.ProjectResponse)
def read_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.put("/projects/{project_id}", response_model=schemas.ProjectResponse)
def update_project(project_id: str, project: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)

    db.commit()
    db.refresh(db_project)
    return db_project


@app.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(db_project)
    db.commit()
    return None


# ============ CATEGORY ENDPOINTS ============

@app.post("/categories", response_model=schemas.CategoryResponse, status_code=201)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    db_category = models.Category(
        id=str(uuid.uuid4()),
        name=category.name
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@app.get("/categories", response_model=List[schemas.CategoryResponse])
def read_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()


@app.get("/categories/{category_id}", response_model=schemas.CategoryResponse)
def read_category(category_id: str, db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@app.put("/categories/{category_id}", response_model=schemas.CategoryResponse)
def update_category(category_id: str, category: schemas.CategoryUpdate, db: Session = Depends(get_db)):
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = category.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)

    db.commit()
    db.refresh(db_category)
    return db_category


@app.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: str, db: Session = Depends(get_db)):
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(db_category)
    db.commit()
    return None


# ============ STATUS ENDPOINTS ============

@app.post("/status", response_model=schemas.StatusResponse, status_code=201)
def create_status(status: schemas.StatusCreate, db: Session = Depends(get_db)):
    db_status = models.Status(
        id=str(uuid.uuid4()),
        name=status.name
    )
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status


@app.get("/status", response_model=List[schemas.StatusResponse])
def read_statuses(db: Session = Depends(get_db)):
    return db.query(models.Status).all()


@app.get("/status/{status_id}", response_model=schemas.StatusResponse)
def read_status(status_id: str, db: Session = Depends(get_db)):
    status = db.query(models.Status).filter(models.Status.id == status_id).first()
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")
    return status


@app.put("/status/{status_id}", response_model=schemas.StatusResponse)
def update_status(status_id: str, status: schemas.StatusCreate, db: Session = Depends(get_db)):
    db_status = db.query(models.Status).filter(models.Status.id == status_id).first()
    if not db_status:
        raise HTTPException(status_code=404, detail="Status not found")

    db_status.name = status.name
    db.commit()
    db.refresh(db_status)
    return db_status


# ============ TASK ENDPOINTS ============

@app.post("/tasks", response_model=schemas.TaskResponse, status_code=201)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    # Validate project_id if provided
    if task.project_id:
        project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    # Validate category_id if provided
    if task.category_id:
        category = db.query(models.Category).filter(models.Category.id == task.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    # Validate status_id
    status = db.query(models.Status).filter(models.Status.id == task.status_id).first()
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")

    db_task = models.Task(
        id=str(uuid.uuid4()),
        title=task.title,
        description=task.description,
        deadline=task.deadline,
        priority=task.priority,
        assignees=task.assignees,
        project_id=task.project_id,
        category_id=task.category_id,
        status_id=task.status_id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


# ============ PENDING TASKS ENDPOINT ============

@app.get("/tasks/pending", response_model=List[schemas.TaskResponse])
def read_pending_tasks(
    order_by: str = Query("created_at", description="Field to order by: deadline, priority, or created_at"),
    order: str = Query("asc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db)
):
    # Get pending status
    pending_status = db.query(models.Status).filter(models.Status.name == "pending").first()
    if not pending_status:
        return []

    query = db.query(models.Task).filter(models.Task.status_id == pending_status.id)

    # Validate order_by
    valid_order_fields = ["deadline", "priority", "created_at"]
    if order_by not in valid_order_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid order_by field. Must be one of: {', '.join(valid_order_fields)}"
        )

    # Validate order
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid order. Must be 'asc' or 'desc'")

    # Apply ordering
    order_column = getattr(models.Task, order_by)
    if order == "desc":
        query = query.order_by(desc(order_column))
    else:
        query = query.order_by(order_column)

    return query.all()


@app.get("/tasks", response_model=List[schemas.TaskResponse])
def read_tasks(db: Session = Depends(get_db)):
    return db.query(models.Task).all()


@app.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
def read_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id: str, task: schemas.TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task.model_dump(exclude_unset=True)

    # Validate project_id if being updated
    if "project_id" in update_data and update_data["project_id"]:
        project = db.query(models.Project).filter(models.Project.id == update_data["project_id"]).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    # Validate category_id if being updated
    if "category_id" in update_data and update_data["category_id"]:
        category = db.query(models.Category).filter(models.Category.id == update_data["category_id"]).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    # Validate status_id if being updated
    if "status_id" in update_data:
        status = db.query(models.Status).filter(models.Status.id == update_data["status_id"]).first()
        if not status:
            raise HTTPException(status_code=404, detail="Status not found")

    for field, value in update_data.items():
        setattr(db_task, field, value)

    db.commit()
    db.refresh(db_task)
    return db_task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(db_task)
    db.commit()
    return None
