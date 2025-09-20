from fastapi import APIRouter
from ..graph.build import build_graph

router = APIRouter()
graph = build_graph()

@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    config = {"configurable": {"thread_id": run_id}}
    state = graph.get_state(config)
    return {"run_id": run_id, "state": state.values, "interrupted": bool(state.next)}
