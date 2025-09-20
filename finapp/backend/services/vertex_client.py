import os, json
from typing import Dict, Any, List, Tuple
from ..settings import GCP_PROJECT, GCP_LOCATION, VERTEX_MODEL_ID, GCS_BUCKET
from vertexai import init as vertex_init
from vertexai.generative_models import GenerativeModel, Part, Tool, FunctionDeclaration, GenerationConfig, Content

vertex_initialized = False
model: GenerativeModel = None

def init_vertex():
    global vertex_initialized, model
    if vertex_initialized:
        return
    if not GCP_PROJECT:
        raise RuntimeError("GCP_PROJECT no configurado")
    vertex_init(project=GCP_PROJECT, location=GCP_LOCATION or "us-central1")
    model = GenerativeModel(VERTEX_MODEL_ID or "gemini-2.0-flash")
    vertex_initialized = True

def _build_extraction_tool() -> Tool:
    # Function schema: el modelo "llama" submit_extraction con los campos y confidencias
    submit_extraction = FunctionDeclaration(
        name="submit_extraction",
        description="Devuelve valores extraídos de estados financieros normalizados con confianza 0-1",
        parameters={
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "Periodo reportado, por ej. 2024Q4 o 2024-12-31"},
                "currency": {"type": "string"},
                "scale_hint": {"type": "string", "enum": ["UNIDAD", "MILES", "MILLONES"]},
                "fields": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "p.ej. balance.total_assets"},
                            "value": {"type": "number", "nullable": True},
                            "unit": {"type": "string", "nullable": True},
                            "confidence": {"type": "number"}
                        },
                        "required": ["path","confidence"]
                    }
                }
            },
            "required": ["fields"]
        }
    )
    return Tool(function_declarations=[submit_extraction])

SYSTEM_PROMPT = """Eres un extractor financiero. 
Lee el documento (texto/tablas/imagen) y devuelve campos en el esquema pedido. 
NO inventes valores. Cuando no estés seguro deja value = null y confidence baja.
Usa nombres canónicos:
balance.(cash,accounts_receivable,inventory,current_assets,total_assets,accounts_payable,short_term_debt,current_liabilities,long_term_debt,total_liabilities,shareholders_equity)
income.(revenue,cogs,gross_profit,operating_income,ebitda,interest_expense,net_income)
cashflow.(operating_cf,investing_cf,financing_cf,free_cf)
Devuelve con function calling a submit_extraction."""

def extract_with_vertex(gcs_uri_mime: Tuple[str,str] = None,
                        inline_text: str = "",
                        tables: List[Dict[str,Any]] = None) -> Dict[str, Any]:
    """Intenta extracción multimodal (GCS). Si no, usa texto/tablas como contexto."""
    init_vertex()
    parts = [Part.from_text(SYSTEM_PROMPT)]
    if gcs_uri_mime:
        uri, mime = gcs_uri_mime
        parts.append(Part.from_uri(uri=uri, mime_type=mime))
    if inline_text:
        parts.append(Part.from_text(f"CONTEXT_TEXT:\n{inline_text[:18000]}"))
    if tables:
        # Adjunta tablas como texto simplificado
        tb = ""
        for t in tables[:5]:
            rows = t.get("rows") or []
            cols = t.get("columns")
            if cols:
                tb += " | ".join(map(str, cols)) + "\n"
            for r in rows[:20]:
                tb += " | ".join(map(lambda x: str(x) if x is not None else "", r)) + "\n"
            tb += "\n"
        parts.append(Part.from_text(f"CONTEXT_TABLES:\n{tb[:12000]}"))

    resp = model.generate_content(
        [Content(role="user", parts=parts)],
        tools=[_build_extraction_tool()],
        generation_config=GenerationConfig(temperature=0)
    )
    # Busca function_call
    fn_call = None
    for cand in (resp.candidates or []):
        for p in cand.content.parts:
            if getattr(p, "function_call", None):
                fn_call = p.function_call
                break
    if not fn_call:
        # fallback: intenta leer texto JSON de la respuesta
        try:
            data = json.loads(resp.text)
            return data
        except Exception:
            return {"fields": [], "period": None, "currency": None, "scale_hint": None}

    # Args de la function
    args = json.loads(fn_call.args) if isinstance(fn_call.args, str) else dict(fn_call.args)
    return args
