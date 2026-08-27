from turtle import title
from sqlalchemy import delete, func
from sqlmodel import select
from annotated_types import T
from fastapi import Depends, FastAPI, HTTPException, Response, Query
from pydantic import BaseModel
from sqlmodel import SQLModel, Session, create_engine, select, Field
from decimal import Decimal
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Numeric
from datetime import date, datetime,timedelta
from typing_extensions import Annotated
from fastapi.concurrency import asynccontextmanager

class TodoRequest(SQLModel):
     title: str
     due_date: datetime

class TodoUpdate(SQLModel):
     title: str | None = None
     status : str| None = None
     due_date: datetime | None = None

class TodoResponse(SQLModel):
    id: int
    title: str
    status: str
    created_at: datetime
    due_date: datetime
    

class TODO(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title : str = Field(index = True,unique = True)
    status : str = Field (default = "pending")
   
    due_date : datetime | None = Field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    created_at : datetime = Field(default_factory =  datetime.now,  index = True)



sqlite_file_name = "C:\\Users\\HP\\Desktop\\Omnicopy\\Basic_crud\\database.db"

sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread":False}
engine = create_engine(sqlite_url,connect_args =connect_args )



def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app : FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        if not session.exec(select(TODO)).first():
            session.add_all([
                TODO(title = "Backend",due_date = datetime.now()),
                TODO(title = "Aptitude",due_date = datetime.now())])
            session.commit()
    yield

app = FastAPI(lifespan=lifespan)



@app.get("/")
async def root():
    return {"message": "Hello World"}




@app.get("/get")
async def get_all_users(
    session: SessionDep,
    skip : int = Query(0,ge=0),
    limit : int = Query(10,ge=1, le=100)
    
):
    result = session.exec(select(TODO).offset(skip).limit(limit)).all()
    total = session.exec(
    select(func.count()).select_from(TODO)
).one()
    
    return {
    "total": total,
    "skip": skip,
    "limit": limit,
    "items": result
    }



@app.get("/get/{id}",response_model=TodoResponse)
async def read_task(id : int, session: SessionDep):
    task = session.get(TODO,id)
    if not task:
            raise HTTPException(status_code = 404)
    return task



@app.post("/tasks",status_code = 201,response_model=TodoResponse)
async def create_tasks(task: TodoRequest, session: SessionDep):

        db_task = TODO.model_validate(task)
        if db_task:
             raise HTTPException(status_code = 404,detail = "The title with this name already exist")
        session.add(db_task)
        session.commit()
        session.refresh(db_task)
        return db_task
     

@app.put("/Update_Task/{id}",response_model=TodoResponse)
async def Update_task(id : int, todo : TodoRequest,session : SessionDep):
    result = session.get(TODO, id)
    if not result:
            raise HTTPException(status_code = 404, detail="Task title not found")
    
    update_todo = todo.model_dump(exclude_unset=True)

    for key, val in update_todo.items():
        setattr(result,key, val)

    session.add(result)
    session.commit()
    session.refresh(result)
    return result
     
     

@app.patch("/updateStatus",response_model=TodoResponse)
async def update_status(task : TodoUpdate, session : SessionDep):

     
     result = session.exec(select(TODO).where(TODO.title == task.title)).first()
     if not result:
          raise HTTPException(status_code = 404, detail="Task title not found")

     update_todo = task.model_dump(exclude_unset=True)

     for key, val in update_todo.items():
        setattr(result,key, val)

     
     session.add(result)
     session.commit()
     session.refresh(result)
     return result



    
@app.delete("/todo")
async def delete_all(session: SessionDep):
    
    session.exec(delete(TODO))
    session.commit()
    return {"message" : "All tasks are deleted"}





@app.delete("/todo/{id}")
async def delete_task(id:int,session: SessionDep):
    data = session.get(TODO,id)
    if not data:
            raise HTTPException(status_code = 404)
    session.delete(data)
    session.commit()

    return {"message": f"Id {id} is deleted"}
    







    






