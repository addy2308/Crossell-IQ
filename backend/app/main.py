from fastapi import FastAPI
from app.core.metrics import metrics_middleware, metrics_endpoint, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from contextlib import asynccontextmanager
import uvicorn, os, time, logging
from app.config import get_settings
from app.database import Base, sync_engine
from app.api import analytics, auth, websocket, feedback, evaluation
from app.core.logging_config import setup_logging
from app.core.rate_limit import RateLimiter
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

settings = get_settings()
logger = setup_logging(settings.LOG_LEVEL)

# Initialize rate limiter
rate_limiter = RateLimiter(requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=sync_engine)
    logger.info(f"CrossSell IQ v{settings.VERSION} started")
    yield

app = FastAPI(title="CrossSell IQ", version=settings.VERSION, lifespan=lifespan)
app.middleware('http')(metrics_middleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if not request.url.path.startswith("/static") and request.url.path != "/metrics":
        client_ip = request.client.host if request.client else "unknown"
        if not rate_limiter.is_allowed(client_ip):
            return JSONResponse(status_code=429, content={"detail": "Too many requests"})
    return await call_next(request)

# Process time header
@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(round(time.time() - start, 4))
    return response

# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    pass

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)
app.include_router(websocket.router)
app.include_router(evaluation.router, prefix=settings.API_V1_PREFIX)
app.include_router(feedback.router, prefix=settings.API_V1_PREFIX)

@app.get("/")
async def root():
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {"service": settings.PROJECT_NAME, "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

