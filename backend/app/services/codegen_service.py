from typing import Dict, Any
from app.services.ai_service import AIService
from app.utils.prompt_templates import CODEGEN_PROMPT


class CodegenService:
    def __init__(self):
        self.ai = AIService()

    async def generate(
        self,
        task_title: str,
        task_description: str,
        requirement_doc: str = "",
        tech_stack: str = "",
        extra_prompt: str = "",
    ) -> Dict[str, Any]:
        context_parts = [f"## 任务标题\n{task_title}", f"## 任务描述\n{task_description}"]
        if requirement_doc:
            context_parts.append(f"## 需求文档\n{requirement_doc}")
        if tech_stack:
            context_parts.append(f"## 技术栈要求\n{tech_stack}")
        if extra_prompt:
            context_parts.append(f"## 补充说明\n{extra_prompt}")

        messages = [
            {"role": "system", "content": CODEGEN_PROMPT},
            {"role": "user", "content": "\n\n".join(context_parts)},
        ]
        result = await self.ai.chat_json(messages, temperature=0.3, max_tokens=8192)
        return {
            "code": result.get("code", ""),
            "path": result.get("path", f"{task_title}.py"),
        }
