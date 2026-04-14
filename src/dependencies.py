from typing import Annotated

from fastapi import Request, Depends
from sqlalchemy.orm import Session

def get_database_session(request: Request) -> Session:
    return request.app.state.db

DatabaseDep = Annotated[Session, Depends(get_database_session)]