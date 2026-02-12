from sqlalchemy import ForeignKey, String, Integer, Text, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class ClassGroup(Base):
    """Represents a school class (e.g. '9A')."""
    __tablename__ = "class_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True)
    # Storing schedule call times as JSON string for now, or could be a separate table
    # format: {"1": ["08:30", "09:15"], "2": ...}
    schedule_calls: Mapped[str] = mapped_column(Text, nullable=True) 

    users: Mapped[list["User"]] = relationship(back_populates="class_group")
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="class_group")
    homeworks: Mapped[list["Homework"]] = relationship(back_populates="class_group")

class User(Base):
    """Represents a Telegram user."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    full_name: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(20), default="student") # student, headman
    
    class_group_id: Mapped[int] = mapped_column(ForeignKey("class_groups.id"), nullable=True)
    class_group: Mapped["ClassGroup"] = relationship(back_populates="users")

class Schedule(Base):
    """Represents the schedule for a specific class and day."""
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    class_group_id: Mapped[int] = mapped_column(ForeignKey("class_groups.id"))
    day_of_week: Mapped[int] = mapped_column(Integer) # 0=Monday, 6=Sunday
    lesson_number: Mapped[int] = mapped_column(Integer)
    subject_name: Mapped[str] = mapped_column(String(128))
    
    class_group: Mapped["ClassGroup"] = relationship(back_populates="schedules")

class Homework(Base):
    """Represents homework for a subject."""
    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(primary_key=True)
    class_group_id: Mapped[int] = mapped_column(ForeignKey("class_groups.id"))
    subject_name: Mapped[str] = mapped_column(String(128))
    content: Mapped[str] = mapped_column(Text)
    attachment_id: Mapped[str] = mapped_column(String(256), nullable=True) # file_id from Telegram
    date_assigned: Mapped[str] = mapped_column(String(32)) # ISO format YYYY-MM-DD
    
    class_group: Mapped["ClassGroup"] = relationship(back_populates="homeworks")
