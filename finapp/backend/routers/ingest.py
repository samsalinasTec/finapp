import os, uuid, shutil
from fastapi import APIRouter, UploadFile, File, Form
from fastapi import HTTPException
from ..graph.build import build_graph
from ..settings import DOCS_DIR, CONF_HIGH, CONF_MED, GCS_BUCKET
from ..models import ExtractPauseResponse, ExtractReadyResponse
from langgraph.types import Command

router = APIRouter()
graph = build_graph()

@router.post("/ingest", response_model=ExtractPauseResponse|ExtractReadyResponse)
async def ingest(file: UploadFile = File(...),
                 period: str = Form(default="UNKNOWN"),
                 currency: str = Form(default="MXN"),
                 language: str = Form(default="es")):
    # Guarda archivo
    doc_id = uuid.uuid4().hex
    ext = os.path.splitext(file.filename)[1].lower()
    path = os.path.join(DOCS_DIR, f"{doc_id}{ext}")
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    run_id = uuid.uuid4().hex
    config = {"configurable": {"thread_id": run_id}}

    # Invoca grafo
    result = graph.invoke({
        "run_id": run_id,
        "doc_id": doc_id,
        "doc_path": path,
        "need_review": False,
        "issues": [],
        "audit": [],
        "confidence_thresholds": {"high": CONF_HIGH, "medium": CONF_MED},
        "use_gcs": bool(GCS_BUCKET)
    }, config=config)

    # ¿Se pausó?
    intr = result.get("__interrupt__")
    if intr:
        payload = intr[0].value if isinstance(intr, list) else intr.value
        return {
            "run_id": run_id,
            "doc_id": doc_id,
            "status": "NEEDS_REVIEW",
            **payload
        }
    # Listo
    fin = result["financials"]
    return {
        "run_id": run_id,
        "doc_id": doc_id,
        "status": "READY",
        "financials": fin,
        "ratios": result["ratios"],
        "audit": result.get("audit", [])
    }
