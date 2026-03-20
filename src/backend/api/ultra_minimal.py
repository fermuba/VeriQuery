"""Ultra-minimal test app"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("STARTUP - waiting indefinitely")
    yield
    logger.info("SHUTDOWN")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9002)
