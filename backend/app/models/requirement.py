from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(300), default="")
    content = Column(Text, default="")  # Markdown content
    version = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())

    project = relationship("Project", back_populates="requirements")
    tasks = relationship("Task", back_populates="requirement")
