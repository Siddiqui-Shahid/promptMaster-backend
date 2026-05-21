from __future__ import annotations

import uuid
from datetime import datetime

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import DateTime, UUID, Column, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base, SQLAlchemyBaseUserTableUUID):
    __tablename__ = "users"

    posts = relationship("Post", back_populates="user")
    prompts = relationship("Prompt", back_populates="user", cascade="all, delete-orphan")


class Post(Base):
    __tablename__ = "posts"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    user = relationship("User", back_populates="posts")

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    caption = Column(Text)
    url = Column(String, nullable=False)
    fileType = Column(String, nullable=False)
    fileName = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "caption": self.caption,
            "url": self.url,
            "fileType": self.fileType,
            "fileName": self.fileName,
            "created_at": self.created_at.isoformat(),
        }
