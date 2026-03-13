from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class ChatRecord(Base):
    __tablename__ = "chat_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String(100), default="")
    content = Column(Text, default="")
    msg_type = Column(String(20), default="text")  # text / image / voice / video
    media_path = Column(String(500), default="")
    transcription = Column(Text, default="")
    timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    project = relationship("Project", back_populates="chat_records")
