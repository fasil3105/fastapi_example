#  Upload
#    ↓
# Is extension allowed?
#    ↓
# Is MIME type allowed?
#    ↓
# Is size within limit?
#    ↓
# YES → Save
# NO  → Reject 

import datetime
from typing_extensions import Annotated
import uuid
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from pathlib import Path
from PIL import Image

from fastapi.concurrency import asynccontextmanager
from pypdf import PdfReader
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Field, Session

from app.db.database import create_db_and_tables
from app.routes import auth, files


@asynccontextmanager
async def lifespan(app : FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan= lifespan)

app.include_router(auth.router, prefix="/auth")
app.include_router(files.router, prefix ="/files" )






    

 