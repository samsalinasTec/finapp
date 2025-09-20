import uuid
from typing import Dict, Any, List
from ..models import Financials, ExtractionField
from ..services import parsers, validators, ratio_tools, gcs, vertex_client
from ..settings import CONF_HIGH, CONF_MED, SCALE_DEFAULT
from langgraph.types import interrupt

def node_parse(state: Dict[str, Any]) -> Dict[str, Any]:
    text, tables = parsers.parse_document(state["doc_path"])
    return {"text": text, "tables": tables}

def _to_financials_from_fields(period, currency, scale, fields: List[ExtractionField]) -> Financials:
    fin = Financials(period=period or "UNKNOWN", currency=currency or "MXN", scale=scale or SCALE_DEFAULT)
    # Rellena atributos usando path
    for f in fields:
        path = f.path
        if f.value is None:
            continue
        obj, attr = path.split(".")
        section = getattr(fin, obj, None)
        if section and hasattr(section, attr):
            setattr(section, attr, f.value)
        fin.fields_raw[path] = f
    # Derivaciones rápidas
    if fin.income.gross_profit is None and fin.income.revenue is not None and fin.income.cogs is not None:
        fin.income.gross_profit = (fin.income.revenue or 0) - (fin.income.cogs or 0)
    return fin

def node_extract(state: Dict[str, Any]) -> Dict[str, Any]:
    # Si hay bucket, sube a GCS para multimodal; si no, usa texto/tablas
    gcs_uri_mime = None
    try:
        if state.get("use_gcs"):
            gcs_uri, mime = gcs.upload_to_gcs(state["doc_path"])
            gcs_uri_mime = (gcs_uri, mime)
    except Exception:
        gcs_uri_mime = None

    result = vertex_client.extract_with_vertex(gcs_uri_mime, state.get("text") or "", state.get("tables") or [])
    # Normaliza a ExtractionField[]
    fields = []
    for item in result.get("fields", []):
        fields.append(ExtractionField(
            path=item.get("path"),
            value=item.get("value"),
            unit=item.get("unit"),
            confidence=float(item.get("confidence", 0.0))
        ))
    fin = _to_financials_from_fields(result.get("period"), result.get("currency"), result.get("scale_hint"), fields)
    need_review = any(f.confidence < CONF_MED for f in fields)
    return {
        "financials": fin,
        "need_review": need_review,
        "issues": [],
        "confidence_thresholds": {"high": CONF_HIGH, "medium": CONF_MED}
    }

def node_validate(state: Dict[str, Any]) -> Dict[str, Any]:
    issues = validators.check_accounting_constraints(state["financials"])
    need_review = state.get("need_review", False) or bool(issues)
    return {"issues": issues, "need_review": need_review}

def node_hitl_gate(state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("need_review"):
        # Pausa y devuelve payload para UI (HITL)
        fields = list(state["financials"].fields_raw.values())
        payload = {
            "period": state["financials"].period,
            "currency": state["financials"].currency,
            "scale_hint": state["financials"].scale,
            "issues": [i.model_dump() for i in state["issues"]],
            "fields": [f.model_dump() for f in fields],
            "confidence_thresholds": state.get("confidence_thresholds", {})
        }
        corrections = interrupt(payload)  # reanuda al recibir dict con correcciones
        # Aplica correcciones cuando regrese
        return {"human_feedback": corrections}
    return {}

def node_apply_feedback(state: Dict[str, Any]) -> Dict[str, Any]:
    fin = state["financials"]
    feedback = state.get("human_feedback") or {"corrections": []}
    audit = state.get("audit") or []

    # Escala/moneda
    for c in feedback.get("corrections", []):
        path = c["path"]
        new_value = c.get("new_value")
        if path.startswith("meta.scale_confirmed"):
            fin.scale = str(new_value)
            continue
        if path.startswith("meta.currency_confirmed"):
            fin.currency = str(new_value)
            continue
        # actualiza campo
        obj, attr = path.split(".")
        section = getattr(fin, obj)
        old = getattr(section, attr)
        setattr(section, attr, new_value)
        audit.append({"path": path, "old": old, "new": new_value, "by": "user"})

    return {"financials": fin, "issues": [], "need_review": False, "audit": audit}

def node_ratios(state: Dict[str, Any]) -> Dict[str, Any]:
    ratios = ratio_tools.compute(state["financials"])
    return {"ratios": ratios}
