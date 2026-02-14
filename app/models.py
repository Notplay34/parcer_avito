"""SQLAlchemy models."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Numeric, Boolean, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    searches: Mapped[list["Search"]] = relationship("Search", back_populates="user")


class Search(Base):
    __tablename__ = "searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    search_url: Mapped[str] = mapped_column(Text, nullable=False)
    max_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_check_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    blocked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="searches")
    seen_ads: Mapped[list["SeenAd"]] = relationship("SeenAd", back_populates="search", cascade="all, delete-orphan")


class SeenAd(Base):
    __tablename__ = "seen_ads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    search_id: Mapped[int] = mapped_column(Integer, ForeignKey("searches.id", ondelete="CASCADE"), nullable=False)
    avito_ad_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    search: Mapped["Search"] = relationship("Search", back_populates="seen_ads")

    __table_args__ = (UniqueConstraint("search_id", "avito_ad_id", name="uq_search_avito_ad"),)
