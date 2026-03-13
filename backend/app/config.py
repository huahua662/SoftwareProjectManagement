from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "root"
    DB_NAME: str = "ccswitch"
    DATABASE_URL: Optional[str] = None

    # AI API
    AI_BASE_URL: str = "https://api.openai.com/v1"
    AI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o"
    AI_VISION_MODEL: str = ""

    # PyWxDump
    PYWXDUMP_PATH: str = ""

    # Paths
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def db_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            "?charset=utf8mb4"
        )

    def update_ai_settings(self, ai_base_url: str = None, ai_api_key: str = None,
                           ai_model: str = None, ai_vision_model: str = None,
                           pywxdump_path: str = None):
        if ai_base_url is not None:
            object.__setattr__(self, "AI_BASE_URL", ai_base_url)
        if ai_api_key is not None:
            object.__setattr__(self, "AI_API_KEY", ai_api_key)
        if ai_model is not None:
            object.__setattr__(self, "AI_MODEL", ai_model)
        if ai_vision_model is not None:
            object.__setattr__(self, "AI_VISION_MODEL", ai_vision_model)
        if pywxdump_path is not None:
            object.__setattr__(self, "PYWXDUMP_PATH", pywxdump_path)

    def save_to_env(self):
        lines = []
        if ENV_PATH.exists():
            lines = ENV_PATH.read_text(encoding="utf-8").splitlines()

        keys_to_save = {
            "DB_HOST": self.DB_HOST,
            "DB_PORT": str(self.DB_PORT),
            "DB_USER": self.DB_USER,
            "DB_PASSWORD": self.DB_PASSWORD,
            "DB_NAME": self.DB_NAME,
            "AI_BASE_URL": self.AI_BASE_URL,
            "AI_API_KEY": self.AI_API_KEY,
            "AI_MODEL": self.AI_MODEL,
            "AI_VISION_MODEL": self.AI_VISION_MODEL,
            "PYWXDUMP_PATH": self.PYWXDUMP_PATH,
        }

        written_keys = set()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                new_lines.append(line)
                continue
            key = stripped.split("=", 1)[0].strip()
            if key in keys_to_save:
                new_lines.append(f"{key}={keys_to_save[key]}")
                written_keys.add(key)
            else:
                new_lines.append(line)

        for key, val in keys_to_save.items():
            if key not in written_keys:
                new_lines.append(f"{key}={val}")

        ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


settings = Settings()
