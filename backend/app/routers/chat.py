from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json
import csv
import io
import os
import uuid

from app.database import get_db
from app.config import settings
from app.models.chat_record import ChatRecord
from app.models.project import Project

router = APIRouter()


class ChatRecordOut(BaseModel):
    id: int
    project_id: int
    sender: str
    content: str
    msg_type: str
    media_path: str
    transcription: str
    timestamp: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_obj(cls, obj: ChatRecord) -> "ChatRecordOut":
        return cls(
            id=obj.id,
            project_id=obj.project_id,
            sender=obj.sender or "",
            content=obj.content or "",
            msg_type=obj.msg_type or "text",
            media_path=obj.media_path or "",
            transcription=obj.transcription or "",
            timestamp=obj.timestamp.isoformat() if obj.timestamp else None,
            created_at=obj.created_at.isoformat() if obj.created_at else "",
        )


class ChatRecordCreate(BaseModel):
    sender: str = ""
    content: str = ""
    msg_type: str = "text"
    timestamp: Optional[str] = None


@router.get("/{project_id}/records")
def list_records(project_id: int, db: Session = Depends(get_db)):
    records = (
        db.query(ChatRecord)
        .filter(ChatRecord.project_id == project_id)
        .order_by(ChatRecord.timestamp.asc(), ChatRecord.id.asc())
        .all()
    )
    return [ChatRecordOut.from_orm_obj(r) for r in records]


@router.post("/{project_id}/records")
def add_record(project_id: int, data: ChatRecordCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    ts = None
    if data.timestamp:
        try:
            ts = datetime.fromisoformat(data.timestamp)
        except ValueError:
            pass
    record = ChatRecord(
        project_id=project_id,
        sender=data.sender,
        content=data.content,
        msg_type=data.msg_type,
        timestamp=ts,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ChatRecordOut.from_orm_obj(record)


@router.post("/{project_id}/import/json")
async def import_json(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    content = await file.read()
    try:
        data = json.loads(content.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="JSON解析失败")
    if not isinstance(data, list):
        data = [data]
    count = 0
    for item in data:
        ts = None
        if item.get("timestamp"):
            try:
                ts = datetime.fromisoformat(str(item["timestamp"]))
            except ValueError:
                pass
        record = ChatRecord(
            project_id=project_id,
            sender=item.get("sender", ""),
            content=item.get("content", ""),
            msg_type=item.get("msg_type", "text"),
            timestamp=ts,
        )
        db.add(record)
        count += 1
    db.commit()
    return {"detail": f"已导入 {count} 条记录"}


@router.post("/{project_id}/import/csv")
async def import_csv(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    count = 0
    for row in reader:
        ts = None
        if row.get("timestamp"):
            try:
                ts = datetime.fromisoformat(row["timestamp"])
            except ValueError:
                pass
        record = ChatRecord(
            project_id=project_id,
            sender=row.get("sender", ""),
            content=row.get("content", ""),
            msg_type=row.get("msg_type", "text"),
            timestamp=ts,
        )
        db.add(record)
        count += 1
    db.commit()
    return {"detail": f"已导入 {count} 条记录"}


@router.post("/{project_id}/import/txt")
async def import_txt(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    content = await file.read()
    lines = content.decode("utf-8").strip().split("\n")
    count = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Try to parse "sender: content" format
        if ": " in line:
            sender, msg = line.split(": ", 1)
        else:
            sender, msg = "", line
        record = ChatRecord(
            project_id=project_id,
            sender=sender,
            content=msg,
            msg_type="text",
        )
        db.add(record)
        count += 1
    db.commit()
    return {"detail": f"已导入 {count} 条记录"}


@router.post("/{project_id}/upload/media")
async def upload_media(
    project_id: int,
    file: UploadFile = File(...),
    sender: str = Form(""),
    msg_type: str = Form("image"),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    ext = os.path.splitext(file.filename or "")[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    original_name = file.filename or "未知文件"
    record = ChatRecord(
        project_id=project_id,
        sender=sender,
        content=original_name,
        msg_type=msg_type,
        media_path=filepath,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ChatRecordOut.from_orm_obj(record)


class PasteImport(BaseModel):
    text: str


def _parse_wechat_text(text: str):
    """Parse WeChat copied/merged text into message list.

    Supports:
    1. Multi-select copy: "sender：content" or "sender：\ncontent" (Chinese colon)
    2. Merged forward: "sender 2024/1/1 10:00\ncontent" blocks
    3. Simple: "sender: content" (English colon)
    4. Plain text lines
    """
    import re
    lines = text.split("\n")
    records = []
    i = 0

    # Detect WeChat merged forward header like "[聊天记录]" or "群聊的聊天记录"
    start = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped in ("", "[聊天记录]") or stripped.endswith("的聊天记录"):
            start = idx + 1
        else:
            break
    lines = lines[start:]

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue

        # Pattern A: WeChat merged format "sender YYYY/M/D HH:MM" or "sender YYYY-M-D HH:MM"
        m = re.match(r'^(.{1,30})\s+\d{4}[/\-]\d{1,2}[/\-]\d{1,2}\s+\d{1,2}:\d{2}', stripped)
        if m:
            sender = m.group(1).strip()
            content_lines = []
            i += 1
            while i < len(lines):
                cl = lines[i].strip()
                if not cl:
                    break
                # Check if next line is another "sender date" header
                if re.match(r'^.{1,30}\s+\d{4}[/\-]\d{1,2}[/\-]\d{1,2}\s+\d{1,2}:\d{2}', cl):
                    break
                content_lines.append(cl)
                i += 1
            if content_lines:
                records.append({"sender": sender, "content": "\n".join(content_lines)})
            continue

        # Pattern B: "sender：content" or "sender：\ncontent" (Chinese full-width colon)
        cm = re.match(r'^(.{1,30})[\uff1a]\s*(.*)', stripped)
        if cm:
            sender = cm.group(1).strip()
            rest = cm.group(2).strip()
            if rest:
                records.append({"sender": sender, "content": rest})
                i += 1
                continue
            else:
                # Content on following lines
                content_lines = []
                i += 1
                while i < len(lines):
                    cl = lines[i].strip()
                    if not cl:
                        break
                    if re.match(r'^.{1,30}[\uff1a]', cl):
                        break
                    if re.match(r'^.{1,30}\s+\d{4}[/\-]\d{1,2}[/\-]\d{1,2}\s+\d{1,2}:\d{2}', cl):
                        break
                    content_lines.append(cl)
                    i += 1
                if content_lines:
                    records.append({"sender": sender, "content": "\n".join(content_lines)})
                continue

        # Pattern C: "sender:\ncontent" (English colon, name-only line)
        if (
            stripped.endswith(":")
            and len(stripped) < 30
            and i + 1 < len(lines)
            and lines[i + 1].strip()
        ):
            sender = stripped[:-1].strip()
            content_lines = []
            i += 1
            while i < len(lines):
                cl = lines[i].strip()
                if not cl:
                    break
                if cl.endswith(":") and len(cl) < 30 and i + 1 < len(lines):
                    break
                if re.match(r'^.{1,30}[\uff1a]', cl):
                    break
                content_lines.append(cl)
                i += 1
            records.append({"sender": sender, "content": "\n".join(content_lines)})
            continue

        # Pattern D: "sender: content" single-line (English colon)
        if ": " in stripped:
            parts = stripped.split(": ", 1)
            if len(parts[0]) < 30:
                records.append({"sender": parts[0].strip(), "content": parts[1].strip()})
                i += 1
                continue

        # Pattern E: plain text
        records.append({"sender": "", "content": stripped})
        i += 1

    return records


@router.post("/{project_id}/import/paste")
def import_paste(project_id: int, data: PasteImport, db: Session = Depends(get_db)):
    """Smart paste import - supports multiple WeChat copy-paste formats."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    text = data.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="内容不能为空")

    records_to_add = _parse_wechat_text(text)

    count = 0
    for item in records_to_add:
        record = ChatRecord(
            project_id=project_id,
            sender=item["sender"],
            content=item["content"],
            msg_type="text",
        )
        db.add(record)
        count += 1
    db.commit()
    return {"detail": f"已导入 {count} 条记录"}


@router.get("/wechat/detect")
def detect_wechat():
    """Check if WeChat window is open and visible."""
    from app.services.wechat_reader import WechatReaderService
    reader = WechatReaderService()
    info = reader.find_wechat_window()
    if not info:
        return {"found": False, "detail": "未找到微信窗口"}
    return {"found": True, "rect": info["rect"]}


class WechatReadRequest(BaseModel):
    project_id: int
    scroll_times: int = 0  # 0=only current view, >0=scroll up N times first


@router.post("/wechat/read")
async def read_wechat(data: WechatReadRequest, db: Session = Depends(get_db)):
    """Capture WeChat window screenshot, use AI to extract messages, import them."""
    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    from app.services.wechat_reader import WechatReaderService
    reader = WechatReaderService()

    result = await reader.scroll_and_read(scroll_times=data.scroll_times)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    messages = result.get("messages", [])
    if not messages:
        raise HTTPException(status_code=400, detail="未能识别出任何消息，请确保微信聊天窗口可见")

    count = 0
    for msg in messages:
        record = ChatRecord(
            project_id=data.project_id,
            sender=msg.get("sender", ""),
            content=msg.get("content", ""),
            msg_type="text",
        )
        db.add(record)
        count += 1
    db.commit()

    return {
        "detail": f"已从微信读取并导入 {count} 条记录",
        "count": count,
        "screenshot": result.get("screenshot", ""),
    }


OCR_PROMPT = """你是一个聊天记录识别专家。请仔细分析这张聊天截图，提取出所有聊天消息。

请以JSON数组格式输出，每条消息包含 sender（发送者昵称）和 content（消息内容）：
```json
[
  {"sender": "张三", "content": "你好"},
  {"sender": "李四", "content": "你好啊"}
]
```

注意：
- 准确识别每条消息的发送者和内容
- 如果无法确定发送者，用"未知"
- 忽略时间戳、头像等非消息内容
- 保持消息的原始顺序
- 输出纯JSON数组，不要添加其他内容"""


@router.post("/{project_id}/import/ocr")
async def import_ocr(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    content = await file.read()
    import base64
    image_b64 = base64.b64encode(content).decode("utf-8")

    from app.services.ai_service import AIService
    ai = AIService()
    try:
        result_text = await ai.chat_vision(OCR_PROMPT, image_b64, temperature=0.2, max_tokens=4096)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI识别失败: {e}")

    result_text = result_text.strip()
    if result_text.startswith("```json"):
        result_text = result_text[7:]
    if result_text.startswith("```"):
        result_text = result_text[3:]
    if result_text.endswith("```"):
        result_text = result_text[:-3]

    try:
        messages = json.loads(result_text.strip())
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"AI返回格式异常，无法解析: {result_text[:200]}")

    if not isinstance(messages, list):
        messages = [messages]

    ext = os.path.splitext(file.filename or "")[1] or ".png"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    count = 0
    for msg in messages:
        record = ChatRecord(
            project_id=project_id,
            sender=msg.get("sender", "未知"),
            content=msg.get("content", ""),
            msg_type="text",
        )
        db.add(record)
        count += 1
    db.commit()

    return {
        "detail": f"截图识别完成，已导入 {count} 条记录",
        "count": count,
        "screenshot": f"uploads/{filename}",
    }


@router.delete("/record/{record_id}")
def delete_single_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(ChatRecord).filter(ChatRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {"detail": "已删除"}


@router.delete("/{project_id}/records")
def clear_records(project_id: int, db: Session = Depends(get_db)):
    db.query(ChatRecord).filter(ChatRecord.project_id == project_id).delete()
    db.commit()
    return {"detail": "已清空"}
