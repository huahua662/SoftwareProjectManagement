from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.models.task import Task
from app.models.project import Project
from app.models.requirement import Requirement
from app.services.codegen_service import CodegenService
from app.services.export_service import ExportService

router = APIRouter()


class CodegenRequest(BaseModel):
    task_id: int
    tech_stack: Optional[str] = ""
    extra_prompt: Optional[str] = ""


class BatchCodegenRequest(BaseModel):
    project_id: int
    tech_stack: Optional[str] = ""
    extra_prompt: Optional[str] = ""


@router.post("/generate")
async def generate_code(data: CodegenRequest, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == data.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # Get requirement context
    req_content = ""
    if task.requirement_id:
        req = db.query(Requirement).filter(Requirement.id == task.requirement_id).first()
        if req:
            req_content = req.content or ""

    task.status = "AI生成中"
    db.commit()

    service = CodegenService()
    try:
        result = await service.generate(
            task_title=task.title,
            task_description=task.description or "",
            requirement_doc=req_content,
            tech_stack=data.tech_stack or "",
            extra_prompt=data.extra_prompt or "",
        )
    except (ValueError, ConnectionError, TimeoutError, RuntimeError) as e:
        task.status = "待开发"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    task.code_content = result.get("code", "")
    task.code_path = result.get("path", "")
    task.status = "已完成"

    # Update project progress
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if project:
        all_tasks = db.query(Task).filter(Task.project_id == project.id).all()
        done = sum(1 for t in all_tasks if t.status == "已完成")
        project.progress = round(done / len(all_tasks) * 100, 1) if all_tasks else 0
        if project.progress >= 100:
            project.status = "已完成"
        else:
            project.status = "开发中"

    db.commit()
    db.refresh(task)
    return {
        "task_id": task.id,
        "code": task.code_content,
        "path": task.code_path,
        "status": task.status,
    }


@router.post("/generate/batch")
async def batch_generate(data: BatchCodegenRequest, db: Session = Depends(get_db)):
    tasks = (
        db.query(Task)
        .filter(Task.project_id == data.project_id, Task.status.in_(["待开发", "开发中"]))
        .order_by(Task.sort_order.asc())
        .all()
    )
    if not tasks:
        raise HTTPException(status_code=400, detail="没有待生成的任务")

    # Get requirement doc
    req = (
        db.query(Requirement)
        .filter(Requirement.project_id == data.project_id)
        .order_by(Requirement.version.desc())
        .first()
    )
    req_content = req.content if req else ""

    service = CodegenService()
    results = []
    for task in tasks:
        task.status = "AI生成中"
        db.commit()
        result = await service.generate(
            task_title=task.title,
            task_description=task.description or "",
            requirement_doc=req_content,
            tech_stack=data.tech_stack or "",
            extra_prompt=data.extra_prompt or "",
        )
        task.code_content = result.get("code", "")
        task.code_path = result.get("path", "")
        task.status = "已完成"
        db.commit()
        results.append({"task_id": task.id, "path": task.code_path})

    # Update project
    project = db.query(Project).filter(Project.id == data.project_id).first()
    if project:
        all_tasks = db.query(Task).filter(Task.project_id == project.id).all()
        done = sum(1 for t in all_tasks if t.status == "已完成")
        project.progress = round(done / len(all_tasks) * 100, 1) if all_tasks else 0
        if project.progress >= 100:
            project.status = "已完成"
        else:
            project.status = "开发中"
        db.commit()

    return {"detail": f"已生成 {len(results)} 个任务的代码", "results": results}


@router.post("/export/{project_id}")
def export_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    if not tasks:
        raise HTTPException(status_code=400, detail="没有可导出的任务")

    service = ExportService()
    zip_path = service.export_project(project.name, tasks)
    return FileResponse(
        path=zip_path,
        filename=f"{project.name}.zip",
        media_type="application/zip",
    )
