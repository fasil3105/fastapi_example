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


from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from app.db.database import create_db_and_tables
from app.routes import auth, files


@asynccontextmanager
async def lifespan(app : FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan= lifespan)

app.include_router(auth.router, prefix="/auth")
app.include_router(files.router, prefix ="/files" )






    

 