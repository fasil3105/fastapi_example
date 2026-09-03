from pathlib import Path

source = Path(r"C:\Users\HP\Desktop\Omnicopy\file_processing_api\Photo.jpg")

output = Path(
    r"C:\Users\HP\Desktop\Omnicopy\file_processing_api\uploads\photo_corrupted.jpg"
)

data = bytearray(source.read_bytes())

# Keep the JPEG header untouched.
# Corrupt some bytes in the middle.
start = len(data) // 2

for i in range(start, min(start + 100, len(data))):
    data[i] = 0

output.write_bytes(data)