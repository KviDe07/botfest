import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from admin_api.routers import analytics, auth, events, registrations
from admin_api.settings import get_settings
from persistence.session import get_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.database_url:
        os.environ["DATABASE_URL"] = settings.database_url
    get_engine()
    yield


def _cors_origins() -> list[str]:
    s = get_settings()
    return [x.strip() for x in s.cors_origins.split(",") if x.strip()]


app = FastAPI(title="Botfest Admin API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(registrations.router, prefix="/api")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
