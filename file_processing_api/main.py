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

import uuid
from fastapi import FastAPI, File, HTTPException, UploadFile
from pathlib import Path
from PIL import Image
from pypdf import PdfReader


app = FastAPI()
ALLOWED_EXTENSION = {".pdf", ".jpg", ".jpeg", ".png"}

EXTENSION_TO_MIME = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}

MAGIC_BYTES = {
"application/pdf": b"%PDF",
"image/jpeg": b"\xff\xd8\xff",
"image/png": b"\x89PNG\r\n\x1a\n",
}

UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)
MAX_FILE_SIZE = 2 * 1024 * 1024

@app.post("/uploadfile/")
async def create_upload_file(file : UploadFile):

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

        return {"Allowed": {
                "File_extension" : extension,
                "MIME_type" : mime_type,
                "File_Size" : file_size
                }
        }

        

    

 