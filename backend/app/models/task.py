from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, func
from sqlalchemy.orm import relationship
from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    requirement_id = Column(Integer, ForeignKey("requirements.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default="待开发")  # 待开发 / 开发中 / AI生成中 / 已完成
    priority = Column(String(20), default="中")  # 高 / 中 / 低
    estimated_hours = Column(Float, nullable=True)
    code_content = Column(Text, default="")
    code_path = Column(String(500), default="")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="tasks")
    requirement = relationship("Requirement", back_populates="tasks")
