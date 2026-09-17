from pathlib import Path
from tkinter import Image
import uuid

from fastapi import HTTPException, UploadFile
from pypdf import PdfReader
from fastapi import APIRouter
from app.core.config import ALLOWED_EXTENSION, EXTENSION_TO_MIME, MAGIC_BYTES, MAX_FILE_SIZE, UPLOAD_FOLDER
from app.db.database import SessionDep
from app.models.file import FileMetadata

router = APIRouter()

@router.post("/uploadfile/")
async def create_upload_file(file : UploadFile, session: SessionDep):

    extension =  Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSION:
        raise HTTPException(
             status_code=400,
             detail = "Unsupported extension"
        )

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size == 0:
        raise HTTPException(400, "File is empty")

    if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code = 413, detail ="File too large")

    header = await file.read(8)

    file_type = None

    for mime_type, signature in MAGIC_BYTES.items():
         if header.startswith(signature):
              file_type = mime_type
              break
    
    if file_type is None:
         raise HTTPException(
              status_code = 400,
              detail = "Unsupported file type"
         )

    if EXTENSION_TO_MIME[extension] != file_type:
         raise HTTPException(
              status_code = 400,
              detail= "File extension does not match file content"
         )
    await file.seek(0)
    try:
        if file_type == "application/pdf":
            reader = PdfReader(file.file)

            # Make sure PDF has at least one page
            if len(reader.pages) == 0:
                raise ValueError("PDF contains no pages")

            # Access each page to force parsing
            for page in reader.pages:
                page.extract_text()

        elif file_type in {"image/jpeg", "image/png"}:
            image = Image.open(file.file)
            image.verify()

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid or corrupted file"
    )

    new_filename = f"{uuid.uuid4().hex[:8]}{extension}"
    destination_path = UPLOAD_FOLDER / new_filename

    with open(destination_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            f.write(chunk)

            file_metadata = FileMetadata(
            original_filename=file.filename,
            stored_filename=new_filename,
            file_type=file_type,
            file_size=file_size,
            status="VALID"
        )

            session.add(file_metadata)
            session.commit()
            session.refresh(file_metadata)
            

        return {"Allowed": {
                "File_extension" : extension,
                "MIME_type" : file_type,
                "File_Size" : file_size
                }
        }
