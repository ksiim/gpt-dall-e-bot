from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os
import uvicorn

app = FastAPI()

@app.get("/image/{file_path:path}")
async def get_image(file_path: str):
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="image/jpeg")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)