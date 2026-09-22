
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)

MAX_FILE_SIZE = 2 * 1024 * 1024

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

