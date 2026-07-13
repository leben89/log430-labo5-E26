"""User type model."""

from sqlalchemy import Column, Integer, String
from orders.models.base import Base


class UserType(Base):
    __tablename__ = "user_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
