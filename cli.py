import argparse
import sys
import os
import uuid
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import engine, SessionLocal, Base
from app.models import Task, Project, Category, Status
from app.main import seed_default_data


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def print_table(rows, headers):
    if not rows:
        print("(empty)")
        return
    col_widths = [len(h) for h in headers]
    str_rows = [[str(c) if c is not None else "" for c in r] for r in rows]
    for row in str_rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(val))
    fmt = "  ".join(f"{{:<{w}}}" for w in col_widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in col_widths]))
    for row in str_rows:
        print(fmt.format(*row))


def find_status(db: Session, name: str) -> str:
    s = db.query(Status).filter(Status.name.ilike(name)).first()
    if not s:
        print(f"Error: status '{name}' not found")
        sys.exit(1)
    return s.id


def find_resource(db: Session, model, resource_id: str):
    r = db.query(model).filter(model.id == resource_id).first()
    if not r:
        print(f"Error: {model.__tablename__} '{resource_id}' not found")
        sys.exit(1)
    return r


def find_category(db: Session, name: str) -> str:
    c = db.query(Category).filter(Category.name.ilike(name)).first()
    if not c:
        print(f"Error: category '{name}' not found")
        sys.exit(1)
    return c.id


def find_project(db: Session, name: str) -> str:
    p = db.query(Project).filter(Project.name.ilike(name)).first()
    if not p:
        print(f"Error: project '{name}' not found")
        sys.exit(1)
    return p.id


# ============ TASKS ============

def cmd_tasks_list(args):
    db = SessionLocal()
    try:
        query = db.query(Task)
        if args.pending:
            pending = db.query(Status).filter(Status.name == "pending").first()
            if pending:
                query = query.filter(Task.status_id == pending.id)
            else:
                print("No 'pending' status found")
                return
        if args.status:
            s = db.query(Status).filter(Status.name.ilike(args.status)).first()
            if s:
                query = query.filter(Task.status_id == s.id)
            else:
                print(f"Error: status '{args.status}' not found")
                return
        if args.project:
            pid = find_project(db, args.project)
            query = query.filter(Task.project_id == pid)
        if args.category:
            cid = find_category(db, args.category)
            query = query.filter(Task.category_id == cid)
        field = getattr(Task, args.sort, Task.created_at)
        order = desc(field) if args.order == "desc" else field
        query = query.order_by(order)
        tasks = query.all()
        headers = ["ID", "Title", "Status", "Priority", "Deadline", "Project", "Category"]
        rows = []
        for t in tasks:
            st = t.status.name if t.status else ""
            pr = t.project.name if t.project else ""
            ct = t.category.name if t.category else ""
            dl = t.deadline.strftime("%Y-%m-%d %H:%M") if t.deadline else ""
            rows.append([t.id[:8], t.title, st, t.priority, dl, pr, ct])
        print_table(rows, headers)
    finally:
        db.close()


def cmd_tasks_create(args):
    db = SessionLocal()
    try:
        seed_default_data(db)
        status_id = find_status(db, args.status if args.status else "pending")
        project_id = None
        if args.project:
            project_id = find_project(db, args.project)
        category_id = None
        if args.category:
            category_id = find_category(db, args.category)
        deadline = None
        if args.deadline:
            deadline = datetime.fromisoformat(args.deadline)
        task = Task(
            id=str(uuid.uuid4()),
            title=args.title,
            description=args.desc,
            deadline=deadline,
            priority=args.priority,
            assignees=args.assignees,
            project_id=project_id,
            category_id=category_id,
            status_id=status_id,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        print(f"Created task: {task.title} (id: {task.id})")
    finally:
        db.close()


def cmd_tasks_update(args):
    db = SessionLocal()
    try:
        task = find_resource(db, Task, args.id)
        if args.title:
            task.title = args.title
        if args.desc is not None:
            task.description = args.desc
        if args.priority:
            task.priority = args.priority
        if args.status:
            task.status_id = find_status(db, args.status)
        if args.assignees is not None:
            task.assignees = args.assignees
        if args.deadline:
            task.deadline = datetime.fromisoformat(args.deadline)
        if args.project:
            task.project_id = find_project(db, args.project)
        if args.category:
            task.category_id = find_category(db, args.category)
        db.commit()
        db.refresh(task)
        print(f"Updated task: {task.title}")
    finally:
        db.close()


def cmd_tasks_delete(args):
    db = SessionLocal()
    try:
        task = find_resource(db, Task, args.id)
        db.delete(task)
        db.commit()
        print(f"Deleted task: {task.title}")
    finally:
        db.close()


def cmd_tasks_show(args):
    db = SessionLocal()
    try:
        task = find_resource(db, Task, args.id)
        print(f"  ID:         {task.id}")
        print(f"  Title:      {task.title}")
        print(f"  Description:{task.description}")
        print(f"  Priority:   {task.priority}")
        print(f"  Status:     {task.status.name if task.status else ''}")
        print(f"  Deadline:   {task.deadline.strftime('%Y-%m-%d %H:%M') if task.deadline else 'None'}")
        print(f"  Assignees:  {task.assignees}")
        print(f"  Project:    {task.project.name if task.project else 'None'}")
        print(f"  Category:   {task.category.name if task.category else 'None'}")
        print(f"  Created:    {task.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Updated:    {task.updated_at.strftime('%Y-%m-%d %H:%M') if task.updated_at else ''}")
    finally:
        db.close()


# ============ PROJECTS ============

def cmd_projects_list(args):
    db = SessionLocal()
    try:
        projects = db.query(Project).all()
        headers = ["ID", "Name", "Description", "Tasks"]
        rows = [[p.id[:8], p.name, p.description or "", len(p.tasks)] for p in projects]
        print_table(rows, headers)
    finally:
        db.close()


def cmd_projects_create(args):
    db = SessionLocal()
    try:
        project = Project(id=str(uuid.uuid4()), name=args.name, description=args.desc)
        db.add(project)
        db.commit()
        db.refresh(project)
        print(f"Created project: {project.name} (id: {project.id})")
    finally:
        db.close()


def cmd_projects_update(args):
    db = SessionLocal()
    try:
        project = find_resource(db, Project, args.id)
        if args.name:
            project.name = args.name
        if args.desc is not None:
            project.description = args.desc
        db.commit()
        print(f"Updated project: {project.name}")
    finally:
        db.close()


def cmd_projects_delete(args):
    db = SessionLocal()
    try:
        project = find_resource(db, Project, args.id)
        db.delete(project)
        db.commit()
        print(f"Deleted project: {project.name}")
    finally:
        db.close()


# ============ CATEGORIES ============

def cmd_categories_list(args):
    db = SessionLocal()
    try:
        categories = db.query(Category).all()
        headers = ["ID", "Name", "Tasks"]
        rows = [[c.id[:8], c.name, len(c.tasks)] for c in categories]
        print_table(rows, headers)
    finally:
        db.close()


def cmd_categories_create(args):
    db = SessionLocal()
    try:
        cat = Category(id=str(uuid.uuid4()), name=args.name)
        db.add(cat)
        db.commit()
        db.refresh(cat)
        print(f"Created category: {cat.name} (id: {cat.id})")
    finally:
        db.close()


def cmd_categories_update(args):
    db = SessionLocal()
    try:
        cat = find_resource(db, Category, args.id)
        if args.name:
            cat.name = args.name
        db.commit()
        print(f"Updated category: {cat.name}")
    finally:
        db.close()


def cmd_categories_delete(args):
    db = SessionLocal()
    try:
        cat = find_resource(db, Category, args.id)
        db.delete(cat)
        db.commit()
        print(f"Deleted category: {cat.name}")
    finally:
        db.close()


# ============ STATUS ============

def cmd_status_list(args):
    db = SessionLocal()
    try:
        statuses = db.query(Status).all()
        headers = ["ID", "Name", "Tasks"]
        rows = [[s.id[:8], s.name, len(s.tasks)] for s in statuses]
        print_table(rows, headers)
    finally:
        db.close()


def cmd_status_create(args):
    db = SessionLocal()
    try:
        st = Status(id=str(uuid.uuid4()), name=args.name)
        db.add(st)
        db.commit()
        db.refresh(st)
        print(f"Created status: {st.name} (id: {st.id})")
    finally:
        db.close()


def cmd_status_update(args):
    db = SessionLocal()
    try:
        st = find_resource(db, Status, args.id)
        if args.name:
            st.name = args.name
        db.commit()
        print(f"Updated status: {st.name}")
    finally:
        db.close()


def cmd_status_delete(args):
    db = SessionLocal()
    try:
        st = find_resource(db, Status, args.id)
        db.delete(st)
        db.commit()
        print(f"Deleted status: {st.name}")
    finally:
        db.close()


# ============ CLI SETUP ============

def main():
    parser = argparse.ArgumentParser(
        prog="noteminder",
        description="Noteminder TODO CLI",
    )
    subparsers = parser.add_subparsers(dest="resource", help="Resource to manage")

    # --- tasks ---
    tasks_parser = subparsers.add_parser("tasks", help="Manage tasks")
    tasks_sub = tasks_parser.add_subparsers(dest="action")

    t_list = tasks_sub.add_parser("list", help="List tasks")
    t_list.add_argument("--pending", action="store_true", help="Only pending tasks")
    t_list.add_argument("--status", help="Filter by status name")
    t_list.add_argument("--project", help="Filter by project name")
    t_list.add_argument("--category", help="Filter by category name")
    t_list.add_argument("--sort", default="created_at", choices=["created_at", "priority", "deadline"])
    t_list.add_argument("--order", default="asc", choices=["asc", "desc"])

    t_create = tasks_sub.add_parser("create", help="Create a task")
    t_create.add_argument("--title", required=True, help="Task title")
    t_create.add_argument("--desc", default=None, help="Description")
    t_create.add_argument("--priority", type=int, default=3, help="Priority 1-5 (1=highest)")
    t_create.add_argument("--deadline", default=None, help="Deadline (ISO format)")
    t_create.add_argument("--assignees", default=None, help="Comma-separated names")
    t_create.add_argument("--project", default=None, help="Project name")
    t_create.add_argument("--category", default=None, help="Category name")
    t_create.add_argument("--status", default="pending", help="Status name")

    t_update = tasks_sub.add_parser("update", help="Update a task")
    t_update.add_argument("id", help="Task ID")
    t_update.add_argument("--title", default=None)
    t_update.add_argument("--desc", default=None)
    t_update.add_argument("--priority", type=int, default=None)
    t_update.add_argument("--status", default=None)
    t_update.add_argument("--deadline", default=None)
    t_update.add_argument("--assignees", default=None)
    t_update.add_argument("--project", default=None)
    t_update.add_argument("--category", default=None)

    t_delete = tasks_sub.add_parser("delete", help="Delete a task")
    t_delete.add_argument("id", help="Task ID")

    t_show = tasks_sub.add_parser("show", help="Show task details")
    t_show.add_argument("id", help="Task ID")

    # --- projects ---
    proj_parser = subparsers.add_parser("projects", help="Manage projects")
    proj_sub = proj_parser.add_subparsers(dest="action")

    p_list = proj_sub.add_parser("list", help="List projects")

    p_create = proj_sub.add_parser("create", help="Create a project")
    p_create.add_argument("--name", required=True)
    p_create.add_argument("--desc", default=None)

    p_update = proj_sub.add_parser("update", help="Update a project")
    p_update.add_argument("id", help="Project ID")
    p_update.add_argument("--name", default=None)
    p_update.add_argument("--desc", default=None)

    p_delete = proj_sub.add_parser("delete", help="Delete a project")
    p_delete.add_argument("id", help="Project ID")

    # --- categories ---
    cat_parser = subparsers.add_parser("categories", help="Manage categories")
    cat_sub = cat_parser.add_subparsers(dest="action")

    c_list = cat_sub.add_parser("list", help="List categories")

    c_create = cat_sub.add_parser("create", help="Create a category")
    c_create.add_argument("--name", required=True)

    c_update = cat_sub.add_parser("update", help="Update a category")
    c_update.add_argument("id", help="Category ID")
    c_update.add_argument("--name", default=None)

    c_delete = cat_sub.add_parser("delete", help="Delete a category")
    c_delete.add_argument("id", help="Category ID")

    # --- status ---
    st_parser = subparsers.add_parser("status", help="Manage statuses")
    st_sub = st_parser.add_subparsers(dest="action")

    s_list = st_sub.add_parser("list", help="List statuses")

    s_create = st_sub.add_parser("create", help="Create a status")
    s_create.add_argument("--name", required=True)

    s_update = st_sub.add_parser("update", help="Update a status")
    s_update.add_argument("id", help="Status ID")
    s_update.add_argument("--name", default=None)

    s_delete = st_sub.add_parser("delete", help="Delete a status")
    s_delete.add_argument("id", help="Status ID")

    # Parse and dispatch
    args = parser.parse_args()
    if not args.resource:
        parser.print_help()
        sys.exit(1)

    dispatch = {
        ("tasks", "list"): cmd_tasks_list,
        ("tasks", "create"): cmd_tasks_create,
        ("tasks", "update"): cmd_tasks_update,
        ("tasks", "delete"): cmd_tasks_delete,
        ("tasks", "show"): cmd_tasks_show,
        ("projects", "list"): cmd_projects_list,
        ("projects", "create"): cmd_projects_create,
        ("projects", "update"): cmd_projects_update,
        ("projects", "delete"): cmd_projects_delete,
        ("categories", "list"): cmd_categories_list,
        ("categories", "create"): cmd_categories_create,
        ("categories", "update"): cmd_categories_update,
        ("categories", "delete"): cmd_categories_delete,
        ("status", "list"): cmd_status_list,
        ("status", "create"): cmd_status_create,
        ("status", "update"): cmd_status_update,
        ("status", "delete"): cmd_status_delete,
    }

    key = (args.resource, args.action)
    if key not in dispatch:
        print(f"Error: no action '{args.action}' for '{args.resource}'")
        sys.exit(1)

    dispatch[key](args)


if __name__ == "__main__":
    main()
