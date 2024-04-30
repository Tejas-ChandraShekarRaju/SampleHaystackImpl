from fastapi import FastAPI, File, UploadFile, Response
from fastapi import HTTPException
import json
import os

app = FastAPI()

class SimpleHaystack:
    def __init__(self, storage_file, index_file='haystack_index.json'):
        self.storage_file = storage_file
        self.index_file = index_file
        self.index = self.load_index()  # filename to (offset, size)

    def add_file(self, file_name: str, data: bytes):
        with open(self.storage_file, 'ab') as f:
            offset = f.tell()
            f.write(data)
            size = len(data)
            self.index[file_name] = (offset, size, file_name)
    def save_index(self):
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f)
        
    def load_index(self):
        if os.path.exists(self.index_file):
            with open(self.index_file) as f:
                return json.load(f)
        else:
            return {}

haystack = SimpleHaystack('haystack_storage.bin')

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    haystack.add_file(file.filename, contents)
    haystack.save_index()
    return {"filename": file.filename}



@app.get("/files/{filename}")
def get_file(filename: str):
    if filename in haystack.index:
        offset, size = haystack.index[filename]
        with open(haystack.storage_file, 'rb') as f:
            f.seek(offset)
            data = f.read(size)
        headers = {
        "Content-Disposition": f"attachment; filename={filename}"
                }
        return Response(content=data, media_type="application/octet-stream", headers=headers)

    else:
        raise HTTPException(status_code=404, detail="File not found")
    

@app.get("/index/")
def get_index():
    return haystack.index

