from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import SessionLocal, init_db
from app.routers import auth, cases, health, me
from app.services.catalog import seed_catalog


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    with SessionLocal() as session:
        seed_catalog(session)
    yield


app = FastAPI(
    title="Putokaz API",
    version="0.1.0",
    description="Matching namere građana na procedure. Adresa šaltera samo iz tabele offices.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(cases.router)
app.include_router(auth.router)
app.include_router(me.router)
