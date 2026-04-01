from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Incident Response Agent API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import incidents, stream, auth, webhook  # noqa: E402

app.include_router(incidents.router, prefix="/api")
app.include_router(stream.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(webhook.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
