from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.models.task import Task
from app.models.project import Project

router = APIRouter()


class TaskOut(BaseModel):
    id: int
    project_id: int
    requirement_id: Optional[int] = None
    title: str
    description: str
    status: str
    priority: str
    estimated_hours: Optional[float] = None
    code_content: str
    code_path: str
    sort_order: int
    created_at: str
    updated_at: str

    @classmethod
    def from_orm_obj(cls, obj: Task) -> "TaskOut":
        return cls(
            id=obj.id,
            project_id=obj.project_id,
            requirement_id=obj.requirement_id,
            title=obj.title,
            description=obj.description or "",
            status=obj.status or "待开发",
            priority=obj.priority or "中",
            estimated_hours=obj.estimated_hours,
            code_content=obj.code_content or "",
            code_path=obj.code_path or "",
            sort_order=obj.sort_order or 0,
            created_at=obj.created_at.isoformat() if obj.created_at else "",
            updated_at=obj.updated_at.isoformat() if obj.updated_at else "",
        )


class TaskCreate(BaseModel):
    project_id: int
    title: str
    description: Optional[str] = ""
    priority: Optional[str] = "中"
    estimated_hours: Optional[float] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    estimated_hours: Optional[float] = None
    sort_order: Optional[int] = None
    code_content: Optional[str] = None
    code_path: Optional[str] = None


def _update_project_progress(project_id: int, db: Session):
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    if not tasks:
        return
    done = sum(1 for t in tasks if t.status == "已完成")
    progress = round(done / len(tasks) * 100, 1)
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.progress = progress
        if progress >= 100:
            project.status = "已完成"
        elif done > 0:
            project.status = "开发中"


@router.get("/{project_id}")
def list_tasks(project_id: int, db: Session = Depends(get_db)):
    tasks = (
        db.query(Task)
        .filter(Task.project_id == project_id)
        .order_by(Task.sort_order.asc(), Task.id.asc())
        .all()
    )
    return [TaskOut.from_orm_obj(t) for t in tasks]


@router.post("")
def create_task(data: TaskCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    max_order = db.query(Task).filter(Task.project_id == data.project_id).count()
    task = Task(
        project_id=data.project_id,
        title=data.title,
        description=data.description,
        priority=data.priority,
        estimated_hours=data.estimated_hours,
        sort_order=max_order,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskOut.from_orm_obj(task)


@router.put("/{task_id}")
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(task, field, value)
    _update_project_progress(task.project_id, db)
    db.commit()
    db.refresh(task)
    return TaskOut.from_orm_obj(task)


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    pid = task.project_id
    db.delete(task)
    _update_project_progress(pid, db)
    db.commit()
    return {"detail": "已删除"}


class BatchStatusUpdate(BaseModel):
    task_ids: List[int]
    status: str


@router.put("/batch/status")
def batch_update_status(data: BatchStatusUpdate, db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.id.in_(data.task_ids)).all()
    pids = set()
    for t in tasks:
        t.status = data.status
        pids.add(t.project_id)
    for pid in pids:
        _update_project_progress(pid, db)
    db.commit()
    return {"detail": f"已更新 {len(tasks)} 个任务"}
