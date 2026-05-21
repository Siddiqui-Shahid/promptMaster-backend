from datetime import datetime, timedelta

from sqlalchemy import UUID, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.models import Base


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(180), nullable=False)
    generated_prompt = Column(Text, nullable=False)
    business_type = Column(String(140), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=90),
        nullable=False,
    )

    user = relationship("User", back_populates="prompts")
