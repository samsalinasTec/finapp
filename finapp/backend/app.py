from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import ingest, review, ratios, runs

app = FastAPI(title="FinApp API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

app.include_router(ingest.router, prefix="/api/v1", tags=["ingest"])
app.include_router(review.router, prefix="/api/v1", tags=["review"])
app.include_router(ratios.router, prefix="/api/v1", tags=["ratios"])
app.include_router(runs.router,   prefix="/api/v1", tags=["runs"])
