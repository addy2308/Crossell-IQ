from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from analytics import router as analytics_router
from auth import router as auth_router
from auth import router as auth_router
import uvicorn
import os

app = FastAPI(title="CrossSell IQ API Gateway")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Mount static dashboard
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {"service": "CrossSell IQ Gateway"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

app.include_router(auth_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
