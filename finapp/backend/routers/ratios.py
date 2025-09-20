from fastapi import APIRouter
from ..models import WhatIfRequest, ExtractReadyResponse
from ..graph.build import build_graph
from ..services import ratio_tools

router = APIRouter()
graph = build_graph()

@router.post("/ratios/whatif", response_model=ExtractReadyResponse)
async def whatif(req: WhatIfRequest):
    if not req.run_id:
        # Para MVP, usamos run_id vigente; podrías cargar por financials_id si persistieras
        raise ValueError("Provee run_id")

    config = {"configurable": {"thread_id": req.run_id}}
    state = graph.get_state(config)

    fin = state.values.get("financials")
    audit = state.values.get("audit", [])
    for ch in req.changes:
        path = ch["path"]
        new_val = ch.get("new_value")
        factor = ch.get("factor")
        if factor is not None and new_val is None:
            # obtener actual y multiplicar
            obj, attr = path.split(".")
            cur = getattr(getattr(fin, obj), attr)
            if cur is not None:
                new_val = cur * float(factor)
        if new_val is not None:
            obj, attr = path.split(".")
            section = getattr(fin, obj)
            old = getattr(section, attr)
            setattr(section, attr, float(new_val))
            audit.append({"path": path, "old": old, "new": new_val, "by": "user", "scenario": req.scenario_name})

    ratios = ratio_tools.compute(fin)
    return {
        "run_id": req.run_id,
        "doc_id": state.values.get("doc_id",""),
        "status": "READY",
        "financials": fin,
        "ratios": ratios,
        "audit": audit
    }
