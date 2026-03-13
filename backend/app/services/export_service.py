import os
import zipfile
from typing import List
from app.config import settings
from app.models.task import Task


class ExportService:
    def export_project(self, project_name: str, tasks: List[Task]) -> str:
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in project_name)
        zip_path = os.path.join(settings.OUTPUT_DIR, f"{safe_name}.zip")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for task in tasks:
                if not task.code_content:
                    continue
                file_path = task.code_path or f"task_{task.id}.py"
                # Normalize path separators
                file_path = file_path.replace("\\", "/")
                if file_path.startswith("/"):
                    file_path = file_path[1:]
                zf.writestr(f"{safe_name}/{file_path}", task.code_content)

            # Add a README
            readme = f"# {project_name}\n\n"
            readme += "## 任务列表\n\n"
            for task in tasks:
                status = "✅" if task.status == "已完成" else "⬜"
                readme += f"- {status} {task.title}\n"
                if task.code_path:
                    readme += f"  - 文件: {task.code_path}\n"
            zf.writestr(f"{safe_name}/README.md", readme)

        return zip_path
