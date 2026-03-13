from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.project import Project

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    budget: Optional[float] = 0.0


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None


class ProjectOut(BaseModel):
    id: int
    name: str
    description: str
    status: str
    budget: float
    progress: float
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_obj(cls, obj: Project) -> "ProjectOut":
        return cls(
            id=obj.id,
            name=obj.name,
            description=obj.description or "",
            status=obj.status or "",
            budget=obj.budget or 0.0,
            progress=obj.progress or 0.0,
            created_at=obj.created_at.isoformat() if obj.created_at else "",
            updated_at=obj.updated_at.isoformat() if obj.updated_at else "",
        )


@router.get("")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return [ProjectOut.from_orm_obj(p) for p in projects]


@router.post("")
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(name=data.name, description=data.description, budget=data.budget or 0.0)
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectOut.from_orm_obj(project)


@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return ProjectOut.from_orm_obj(project)


@router.put("/{project_id}")
def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    if data.status is not None:
        project.status = data.status
    if data.budget is not None:
        project.budget = data.budget
    db.commit()
    db.refresh(project)
    return ProjectOut.from_orm_obj(project)


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    db.delete(project)
    db.commit()
    return {"detail": "已删除"}
