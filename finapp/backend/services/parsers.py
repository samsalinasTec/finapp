import os, io, pdfplumber, pandas as pd
from typing import Tuple, List, Dict

def parse_document(path: str) -> Tuple[str, List[Dict]]:
    text = ""
    tables = []
    ext = os.path.splitext(path)[1].lower()

    if ext in [".pdf"]:
        with pdfplumber.open(path) as pdf:
            for pi, page in enumerate(pdf.pages):
                t = page.extract_text() or ""
                text += f"\n[PAGE {pi+1}]\n{t}\n"
                try:
                    for table in page.extract_tables() or []:
                        tables.append({"page": pi+1, "rows": table})
                except Exception:
                    pass

    elif ext in [".csv"]:
        df = pd.read_csv(path)
        tables.append({"page": None, "rows": df.values.tolist(), "columns": df.columns.tolist()})
    elif ext in [".xls", ".xlsx"]:
        df = pd.read_excel(path)
        tables.append({"page": None, "rows": df.values.tolist(), "columns": df.columns.tolist()})
    else:
        # binario imagen: no extraemos texto aquí; multimodal lo leerá
        pass

    return text.strip(), tables
