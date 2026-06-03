import time
from sqlalchemy import (
    BigInteger, Column, ForeignKey, Integer,
    Numeric, String, Text, TIMESTAMP
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String)
    created_at = Column(TIMESTAMP, default=time.time)

    tasks = relationship("Task", back_populates="user")
    schedules = relationship("MessageSchedule", back_populates="user")
    receipts = relationship("Receipt", back_populates="user")
    spendings = relationship("Spending", back_populates="user")
    history = relationship("ConversationHistory", back_populates="user")


class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    task_name = Column(String)
    task_description = Column(Text)
    status = Column(String, default="pending")
    deadline = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, default=time.time)

    user = relationship("User", back_populates="tasks")
    schedules = relationship("MessageSchedule", back_populates="task")


class MessageSchedule(Base):
    __tablename__ = "message_schedule"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    task_id = Column(Integer, ForeignKey("tasks.task_id"))
    title = Column(String)
    description = Column(Text)
    status = Column(String, default="pending")
    time_to_send = Column(TIMESTAMP)

    user = relationship("User", back_populates="schedules")
    task = relationship("Task", back_populates="schedules")


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    raw_text = Column(Text)
    created_at = Column(TIMESTAMP, default=time.time)

    user = relationship("User", back_populates="receipts")
    spendings = relationship("Spending", back_populates="receipt")


class Spending(Base):
    __tablename__ = "spendings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    receipt_id = Column(Integer, ForeignKey("receipts.id"))
    spending_name = Column(String)
    spending_category = Column(String)
    amount = Column(Numeric)
    created_at = Column(TIMESTAMP, default=time.time)

    user = relationship("User", back_populates="spendings")
    receipt = relationship("Receipt", back_populates="spendings")


class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String) 
    content = Column(Text)
    created_at = Column(TIMESTAMP, default=time.time)

    user = relationship("User", back_populates="history")