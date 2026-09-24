
from sqlmodel import SQLModel, Field

from app.models.users import Users


class FileMetadata(SQLModel, table=True):
    __tablename__ = "files"

    id: int | None = Field(default=None, primary_key=True)
    user_id : int = Field(foreign_key = "users.id")
    original_filename: str
    stored_filename: str
    file_type: str
    file_size: int
    status: str