from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import logging

from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class SettingsOut(BaseModel):
    ai_base_url: str
    ai_api_key: str
    ai_model: str
    ai_vision_model: str
    pywxdump_path: str


class SettingsUpdate(BaseModel):
    ai_base_url: Optional[str] = None
    ai_api_key: Optional[str] = None
    ai_model: Optional[str] = None
    ai_vision_model: Optional[str] = None
    pywxdump_path: Optional[str] = None


def _mask_key(key: str) -> str:
    if not key or len(key) <= 8:
        return key
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


@router.get("")
def get_settings():
    return SettingsOut(
        ai_base_url=settings.AI_BASE_URL,
        ai_api_key=_mask_key(settings.AI_API_KEY),
        ai_model=settings.AI_MODEL,
        ai_vision_model=settings.AI_VISION_MODEL,
        pywxdump_path=settings.PYWXDUMP_PATH,
    )


@router.put("")
def update_settings(data: SettingsUpdate):
    real_key = data.ai_api_key
    if real_key and "*" in real_key:
        real_key = None

    settings.update_ai_settings(
        ai_base_url=data.ai_base_url,
        ai_api_key=real_key,
        ai_model=data.ai_model,
        ai_vision_model=data.ai_vision_model,
        pywxdump_path=data.pywxdump_path,
    )
    settings.save_to_env()
    return {"detail": "设置已保存并生效"}


@router.post("/test-ai")
async def test_ai_connection():
    if not settings.AI_API_KEY:
        raise HTTPException(status_code=400, detail="API Key 未配置")

    base = settings.AI_BASE_URL.rstrip("/")
    if not base.endswith("/v1"):
        base = base + "/v1"
    url = f"{base}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.AI_API_KEY}",
    }
    payload = {
        "model": settings.AI_MODEL,
        "messages": [{"role": "user", "content": "say ok"}],
        "max_tokens": 5,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=headers)

        if resp.status_code == 200:
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            model = data.get("model", settings.AI_MODEL)
            return {"ok": True, "detail": f"连接成功，模型: {model}，回复: {content}"}

        body = resp.text[:300]
        return {"ok": False, "detail": f"API 返回 HTTP {resp.status_code}: {body}"}
    except httpx.ConnectError:
        return {"ok": False, "detail": f"无法连接到 {base}，请检查 API Base URL"}
    except httpx.TimeoutException:
        return {"ok": False, "detail": "连接超时，请检查网络"}
    except Exception as e:
        return {"ok": False, "detail": str(e)}
