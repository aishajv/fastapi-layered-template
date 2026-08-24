from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session


def get_db(request: Request) -> Generator[Session, None, None]:
    yield from request.app.state.db.get_session()


DatabaseSession = Annotated[Session, Depends(get_db, scope="function")]
