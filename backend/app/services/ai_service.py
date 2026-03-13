import httpx
import logging
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class AIService:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        raw_url = (base_url or settings.AI_BASE_URL).rstrip("/")
        if not raw_url.endswith("/v1"):
            raw_url = raw_url + "/v1"
        self.base_url = raw_url
        self.api_key = api_key or settings.AI_API_KEY
        self.model = model or settings.AI_MODEL

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        if not self.api_key:
            raise ValueError(
                "AI API Key 未配置。请在 backend/.env 文件中设置 AI_API_KEY"
            )

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        logger.info(f"AI request -> {url}, model={self.model}")

        async with httpx.AsyncClient(timeout=180) as client:
            try:
                resp = await client.post(url, json=payload, headers=headers)
            except httpx.ConnectError as e:
                raise ConnectionError(
                    f"无法连接到 AI API ({self.base_url})，请检查 AI_BASE_URL 配置。错误: {e}"
                )
            except httpx.TimeoutException:
                raise TimeoutError(
                    f"AI API 请求超时，请检查网络或稍后重试"
                )

            # Log response info for debugging
            if resp.status_code != 200:
                body = resp.text[:500]
                logger.error(f"AI API error: status={resp.status_code}, body={body}")
                raise RuntimeError(
                    f"AI API 返回错误 (HTTP {resp.status_code}): {body}"
                )

            raw = resp.text
            if not raw or not raw.strip():
                raise RuntimeError("AI API 返回了空内容，请检查 API 配置")

            try:
                data = resp.json()
            except Exception:
                logger.error(f"AI API response not JSON: {raw[:500]}")
                raise RuntimeError(
                    f"AI API 返回了非 JSON 内容: {raw[:200]}"
                )

        if "choices" not in data or not data["choices"]:
            if "error" in data:
                err_msg = data["error"]
                if isinstance(err_msg, dict):
                    err_msg = err_msg.get("message", str(err_msg))
                raise RuntimeError(f"AI API 错误: {err_msg}")
            raise RuntimeError(f"AI API 返回格式异常: {str(data)[:300]}")

        return data["choices"][0]["message"]["content"]

    async def chat_vision(
        self,
        text_prompt: str,
        image_base64: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """Send an image + text prompt to a vision-capable model."""
        vision_model = settings.AI_VISION_MODEL or self.model
        saved_model = self.model
        self.model = vision_model
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                    },
                ],
            }
        ]
        try:
            return await self.chat(messages, temperature=temperature, max_tokens=max_tokens)
        finally:
            self.model = saved_model

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """Yield content chunks from a streaming chat completion."""
        if not self.api_key:
            raise ValueError("AI API Key 未配置。请在 backend/.env 文件中设置 AI_API_KEY")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=180) as client:
            try:
                async with client.stream("POST", url, json=payload, headers=headers) as resp:
                    if resp.status_code != 200:
                        body = ""
                        async for chunk in resp.aiter_text():
                            body += chunk
                            if len(body) > 500:
                                break
                        raise RuntimeError(f"AI API 返回错误 (HTTP {resp.status_code}): {body[:500]}")

                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            import json
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except Exception:
                            continue
            except httpx.ConnectError as e:
                raise ConnectionError(
                    f"无法连接到 AI API ({self.base_url})，请检查 AI_BASE_URL 配置。错误: {e}"
                )
            except httpx.TimeoutException:
                raise TimeoutError("AI API 请求超时，请检查网络或稍后重试")

    async def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        import json
        content = await self.chat(messages, temperature, max_tokens)
        # Try to extract JSON from the response
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI JSON response: {content[:500]}")
            raise RuntimeError(
                f"AI 返回的内容无法解析为 JSON。原始内容: {content[:200]}"
            )
