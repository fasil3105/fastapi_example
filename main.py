from datetime import datetime
from random import randint
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from h11 import Request
from pydantic import BaseModel


app = FastAPI(root_path="/api/v1")

class Campaign(BaseModel):
    name: str
    due_date: str

@app.get("/")

async def root():
    return {"message":"Hello world"}

data : Any =[
    {
        "campaign_id" :1,
        "name" : "Summer Lunch",
        "due_date":datetime.now(),
        "created_at":datetime.now()

    },
    {
        "campaign_id" :2,
        "name" : "Black Friday",
        "due_date":datetime.now(),
        "created_at":datetime.now()
    }
]

@app.get("/compaigns")

async def read_campaigns():
    return {"campaigns":data}


@app.get("/campaign/{id}")
async def read_campaign(id : int):
    for campaign in data:
        if campaign.get("campaign_id") == id:
            return {"campaign":campaign}
    raise HTTPException(status_code = 404)

@app.post("/campaigns")
async def create_campaign(campaign:Campaign):

    

    new = {
        "campaign_id" :randint(100,1000),
        "name" : campaign.name,
        "due_date":campaign.due_date,
        "created_at":datetime.now()
    }

    data.append(new)
    return {"campaigns":new}

    
@app.put("/campaigns/{id}")
async def update_campaign(id:int,campaign:Campaign):

    for index,item in enumerate(data):

        if item.get("campaign_id") == id:
            updated = {
            "campaign_id" :id,
            "name" : campaign.name,
            "due_date":campaign.due_date,
            "created_at":item.get("created_at")
             }
            
            data[index] = updated
            return {"campaign":updated}
    raise HTTPException(status_code = 404)


    
@app.delete("/campaigns/{id}")
async def delete_campaign(id:int):

    for index,item in enumerate(data):

        if item.get("campaign_id") == id:
            
            
            data.pop(index)
            return Response(status_code = 204)
    raise HTTPException(status_code = 404)

