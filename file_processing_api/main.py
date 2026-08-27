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

app = FastAPI()

Allowed_file_types = {
".pdf"   : "application/pdf",
".jpg"   : "image/jpeg",
".jpeg"  : "image/jpeg",
".png"   : "image/png"
}

UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)
MAX_FILE_SIZE = 1 * 1024 * 1024

@app.post("/uploadfile/")
async def create_upload_file(file : UploadFile):

    file.file.seek(0,2)
    file_size = file.file.tell()
    file.file.seek(0)

    contents = await file.read()
    
    extension =  Path(file.filename).suffix
    
    if  extension not in Allowed_file_types:
        raise HTTPException(status_code = 415, detail ="Unsupported File Type")

    mime_type  = Allowed_file_types[extension]

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code = 413, detail ="File too large")

    if file.content_type == mime_type :
        destination_path = f"{UPLOAD_FOLDER}/{uuid.uuid4().hex[:8]}{extension}"

        with open(destination_path, "wb") as f:
            f.write(contents)

        return {"Allowed": {
                    "File_extension" : extension,
                    "MIME_type" : mime_type,
                    "File_Size" : file_size
                    }
        }
    else :
        return {"Invalid" :{
                    "File_extension" : extension,
                    "MIME_type" : file.content_type,
                    "File_Size" : file_size
                    }
                    }

    

 