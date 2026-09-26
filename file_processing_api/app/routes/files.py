from http.client import UNAUTHORIZED
from pathlib import Path
from tkinter import Image
import uuid
from botocore.exceptions import ClientError
from fastapi import Depends, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pypdf import PdfReader
from fastapi import APIRouter
from sqlmodel import select
from app.core.config import ALLOWED_EXTENSION, EXTENSION_TO_MIME, MAGIC_BYTES, MAX_FILE_SIZE, S3_BUCKET_NAME, UPLOAD_FOLDER, URL_EXPIRATION
from app.db.database import SessionDep
from app.models.file import FileMetadata
from app.core.security import get_current_user
from app.models.users import Users
from app.core.storage import delete_file_in_storage, generate_presigned_url, s3_client
from app.schemas.file import DownloadResponse

router = APIRouter()



# get all files metadata for specific user
@router.get("/files")
async def get_files(session: SessionDep,current_user: Users = Depends(get_current_user)):
    files = session.exec(select(FileMetadata).where(FileMetadata.user_id == current_user.id)).all()
    return {"files" : files}




# get file metadata using specific file id 

@router.get("/files/{file_id}")
async def get_file(file_id : int ,session: SessionDep,current_user: Users = Depends(get_current_user)):

    file = session.get(FileMetadata, file_id)
    if not file :
            raise HTTPException(
                        status_code=404,
                        detail = "File not found"
                    )
    
    if file.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail = "Forbidden"
        )
    
    return {"files" : file}




# Download single file from aws S3

@router.get("/files/{file_id}/download", response_model = DownloadResponse)
async def download_file(file_id : int ,session: SessionDep,
                        current_user: Users = Depends(get_current_user)):

    file =session.get(FileMetadata, file_id)
    if not file :
                raise HTTPException(
                            status_code=404,
                            detail = "File not found"
                        )
        
    if file.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail = "Forbidden"
        )

    
    url = generate_presigned_url(file.storage_key)

    
    return {
         "download_url": url,
         "expires_in" : URL_EXPIRATION
    }


# delete file object from S3 and file metadata from DB
@router.delete("/delete/{file_id}")
async def delete_file(file_id : int, 
                             session: SessionDep, 
                             current_user: Users = Depends(get_current_user)):

    file = session.get(FileMetadata, file_id)

    if not file:
          raise HTTPException(
               status_code = 404,
               detail = "File not found"
          )

    if file.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail = "Forbidden"
            )


    try:
        delete_file_in_storage(file.storage_key)

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        raise HTTPException(
            status_code=500,
            detail="Failed to delete file from storage"
        )

    session.delete(file)
    session.commit()

    return {
            "message": "File deleted successfully"
            }



@router.post("/uploadfile/")
async def create_upload_file(file : UploadFile, 
                             session: SessionDep, 
                             current_user: Users = Depends(get_current_user)):

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

    s3_key = f"uploads/{new_filename}"

    try:
        await file.seek(0)
        s3_client.put_object(
                Bucket="file-upload",
                Key=s3_key,
                Body=file.file
            )

    except Exception:
        raise HTTPException(
        status_code=500,
        detail="Failed to upload file to storage"
    )

    file_metadata = FileMetadata(
    user_id = current_user.id,
    original_filename=file.filename,
    stored_filename=new_filename,
    file_type=file_type,
    file_size=file_size,
    storage_key = s3_key,
    status="VALID"
)

    session.add(file_metadata)
    session.commit()
    session.refresh(file_metadata)
        

    return {"Allowed": {
            "user_id" : current_user.id,
            "File_extension" : extension,
            "MIME_type" : file_type,
            "File_Size" : file_size
            }
    }
