from fastapi import APIRouter, HTTPException
from ..models import ReviewRequest, ExtractPauseResponse, ExtractReadyResponse
from ..graph.build import build_graph
from langgraph.types import Command

router = APIRouter()
graph = build_graph()

@router.post("/review", response_model=ExtractPauseResponse|ExtractReadyResponse)
async def review(req: ReviewRequest):
    config = {"configurable": {"thread_id": req.run_id}}
    # Reanuda con correcciones
    result = graph.invoke(Command(resume={"corrections": req.corrections}), config=config)

    intr = result.get("__interrupt__")
    if intr:
        payload = intr[0].value if isinstance(intr, list) else intr.value
        return {
            "run_id": req.run_id,
            "doc_id": result.get("doc_id",""),
            "status": "NEEDS_REVIEW",
            **payload
        }

    fin = result["financials"]
    return {
        "run_id": req.run_id,
        "doc_id": result.get("doc_id",""),
        "status": "READY",
        "financials": fin,
        "ratios": result["ratios"],
        "audit": result.get("audit", [])
    }
