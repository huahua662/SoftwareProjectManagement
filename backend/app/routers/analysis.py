import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.project import Project
from app.models.chat_record import ChatRecord
from app.models.requirement import Requirement
from app.models.task import Task
from app.services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

router = APIRouter()


class AnalyzeRequest(BaseModel):
    project_id: int
    extra_prompt: Optional[str] = ""


@router.post("/analyze")
async def analyze_requirements(data: AnalyzeRequest, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    records = (
        db.query(ChatRecord)
        .filter(ChatRecord.project_id == data.project_id)
        .order_by(ChatRecord.timestamp.asc(), ChatRecord.id.asc())
        .all()
    )
    if not records:
        raise HTTPException(status_code=400, detail="暂无聊天记录，请先导入")

    service = AnalysisService()
    try:
        result = await service.analyze(records, extra_prompt=data.extra_prompt or "")
    except (ValueError, ConnectionError, TimeoutError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Save requirement doc
    req = Requirement(
        project_id=data.project_id,
        title=result.get("title", "需求文档"),
        content=result.get("content", ""),
        version=(
            db.query(Requirement)
            .filter(Requirement.project_id == data.project_id)
            .count()
            + 1
        ),
    )
    db.add(req)
    db.flush()

    # Save tasks
    task_list = result.get("tasks", [])
    for i, t in enumerate(task_list):
        task = Task(
            project_id=data.project_id,
            requirement_id=req.id,
            title=t.get("title", ""),
            description=t.get("description", ""),
            priority=t.get("priority", "中"),
            estimated_hours=t.get("estimated_hours"),
            sort_order=i,
        )
        db.add(task)

    project.status = "需求分析中"
    db.commit()
    db.refresh(req)

    return {
        "requirement_id": req.id,
        "title": req.title,
        "content": req.content,
        "task_count": len(task_list),
    }


@router.post("/analyze/stream")
async def analyze_stream(project_id: int = Query(...), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    records = (
        db.query(ChatRecord)
        .filter(ChatRecord.project_id == project_id)
        .order_by(ChatRecord.timestamp.asc(), ChatRecord.id.asc())
        .all()
    )
    if not records:
        raise HTTPException(status_code=400, detail="暂无聊天记录，请先导入")

    service = AnalysisService()

    async def event_generator():
        final_content = ""
        final_tasks = []
        try:
            async for evt in service.analyze_stream(records):
                if evt.get("final_content"):
                    final_content = evt["final_content"]
                    final_tasks = evt.get("tasks", [])
                yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"

            # Save to DB after streaming completes
            req = Requirement(
                project_id=project_id,
                title="需求分析文档",
                content=final_content,
                version=(
                    db.query(Requirement)
                    .filter(Requirement.project_id == project_id)
                    .count()
                    + 1
                ),
            )
            db.add(req)
            db.flush()

            for i, t in enumerate(final_tasks):
                task = Task(
                    project_id=project_id,
                    requirement_id=req.id,
                    title=t.get("title", ""),
                    description=t.get("description", ""),
                    priority=t.get("priority", "中"),
                    estimated_hours=t.get("estimated_hours"),
                    sort_order=i,
                )
                db.add(task)

            project.status = "需求分析中"
            db.commit()
        except Exception as e:
            logger.error(f"Streaming analysis error: {e}")
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/requirements/{project_id}")
def list_requirements(project_id: int, db: Session = Depends(get_db)):
    reqs = (
        db.query(Requirement)
        .filter(Requirement.project_id == project_id)
        .order_by(Requirement.version.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "project_id": r.project_id,
            "title": r.title,
            "content": r.content,
            "version": r.version,
            "created_at": r.created_at.isoformat() if r.created_at else "",
        }
        for r in reqs
    ]


class RequirementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


@router.put("/requirements/{req_id}")
def update_requirement(req_id: int, data: RequirementUpdate, db: Session = Depends(get_db)):
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="需求文档不存在")
    if data.title is not None:
        req.title = data.title
    if data.content is not None:
        req.content = data.content
    db.commit()
    db.refresh(req)
    return {
        "id": req.id,
        "title": req.title,
        "content": req.content,
        "version": req.version,
    }
