
from sqlmodel import SQLModel, Field


class FileMetadata(SQLModel, table=True):
    __tablename__ = "files"

    id: int | None = Field(default=None, primary_key=True)
    original_filename: str
    stored_filename: str
    file_type: str
    file_size: int
    status: str