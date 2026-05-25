from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# Project schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# Category schemas
class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# Status schemas
class StatusBase(BaseModel):
    name: str


class StatusCreate(StatusBase):
    pass


class StatusResponse(StatusBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# Task schemas

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    deadline: Optional[datetime] = None
    priority: int = Field(3, ge=1, le=5)
    assignees: Optional[str] = Field(None, max_length=255)
    project_id: Optional[str] = None
    category_id: Optional[str] = None
    status_id: str


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Optional[int] = None
    assignees: Optional[str] = None
    project_id: Optional[str] = None
    category_id: Optional[str] = None
    status_id: Optional[str] = None


class TaskResponse(TaskBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Query parameters for pending tasks
class PendingTasksQueryParams(BaseModel):
    order_by: Optional[str] = "created_at"  # deadline, priority, created_at
    order: Optional[str] = "asc"  # asc or desc