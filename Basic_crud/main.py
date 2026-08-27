import cmath
from datetime import date, datetime, timezone
from email.mime import base
from random import randint
import stat
from typing import Any, Generic, TypeVar
from unittest.mock import Base
from urllib import response
from fastapi.concurrency import asynccontextmanager
from pydantic import BaseModel
from typing_extensions import Annotated
from fastapi import Depends, FastAPI, HTTPException, Response

from sqlmodel import SQLModel, Session, create_engine, select, Field


class Campaign(SQLModel, table=True):
    
    campaign_id : int | None = Field(default= None,primary_key = True)
    name :str = Field(index = True)
    due_date : datetime | None = Field(default= None,index = True)
    created_at : datetime = Field(default_factory =  datetime.now,  index = True)


class CampaignCreate(SQLModel):
    name : str
    due_date : datetime | None = None


sqlite_file_name = "database.db"

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
        if not session.exec(select(Campaign)).first():
            session.add_all([
                Campaign(name = "Summer Lunch",due_date = datetime.now()),
                Campaign(name = "Black Friday",due_date = datetime.now())])
            session.commit()
    yield


app = FastAPI(root_path="/api/v1",lifespan=lifespan)

T = TypeVar("T")
class Response(BaseModel,Generic[T]):
    data : T
    
   

@app.get("/")

async def root():
    return {"message":"Hello world"}


@app.get("/compaigns",response_model = Response[list[Campaign]] )

async def read_campaigns(session: SessionDep):
    data = session.exec(select(Campaign)).all()
    return {"data":data}

@app.get("/campaign/{id}",response_model = Response[Campaign])
async def read_campaign(id : int,session: SessionDep):
    data = session.get(Campaign,id)
    if not data:
        raise HTTPException(status_code = 404)
    return {"data":data}

@app.post("/campaigns",status_code = 201,response_model = Response[Campaign])

async def create_campaign(campaign:CampaignCreate,session: SessionDep):
    db_campaign = Campaign.model_validate(campaign)
    session.add(db_campaign)
    session.commit()
    session.refresh(db_campaign)
    return {"data":db_campaign}


@app.put("/campaigns/{id}",response_model = Response[Campaign])
async def update_campaign(id:int,campaign:CampaignCreate,session: SessionDep):
    db_campaign = session.get(Campaign,id)
    if not db_campaign:
        raise HTTPException(status_code = 404)
    db_campaign.name = campaign.name
    db_campaign.due_date = campaign.due_date
    session.add(db_campaign)
    session.commit()
    session.refresh(db_campaign)
    return {"data":db_campaign}



@app.delete("/campaigns/{id}",status_code = 204)
async def delete_campaign(id:int,session: SessionDep):
    data = session.get(Campaign,id)  
    if not data:
        raise HTTPException(status_code = 404)
    session.delete(data)
    session.commit()







    
# @app.delete("/campaigns/{id}")
# async def delete_campaign(id:int):

#     for index,item in enumerate(data):

#         if item.get("campaign_id") == id:
            
            
#             data.pop(index)
#             return Response(status_code = 204)
#     raise HTTPException(status_code = 404)

