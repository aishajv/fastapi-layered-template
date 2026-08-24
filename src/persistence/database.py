from collections.abc import Generator
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class Database:
    engine: Engine
    session_factory: sessionmaker[Session]

    def __init__(self, database_url: str) -> None:
        self.engine = create_engine(database_url)
        self.session_factory = sessionmaker(bind=self.engine)

    def get_session(self) -> Generator[Session, None, None]:
        with self.session_factory.begin() as session:
            yield session
