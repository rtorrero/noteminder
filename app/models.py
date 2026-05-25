from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("Task", back_populates="category", cascade="all, delete-orphan")


class Status(Base):
    __tablename__ = "statuses"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("Task", back_populates="status", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    deadline = Column(DateTime, nullable=True)
    priority = Column(Integer, default=3)  # 1=highest, 5=lowest. Should be validated in schema.
    assignees = Column(Text, nullable=True)  # comma-separated names
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=True)
    status_id = Column(String(36), ForeignKey("statuses.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="tasks")
    category = relationship("Category", back_populates="tasks")
    status = relationship("Status", back_populates="tasks")