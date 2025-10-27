from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select, JSON, Column

class String(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    value: str = Field(index=True, unique=True)
    properties: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: str | None = Field(default=None)
    
engine = create_engine(
    "sqlite:///database.db",
    connect_args={"check_same_thread": False}
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
        
SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()