import os
from dotenv import load_dotenv

load_dotenv()

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

CONF_HIGH = float(os.getenv("CONF_HIGH", "0.80"))
CONF_MED = float(os.getenv("CONF_MED", "0.50"))

GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
VERTEX_MODEL_ID = os.getenv("VERTEX_MODEL_ID", "gemini-2.0-flash")

GCS_BUCKET = os.getenv("GCS_BUCKET")

BASE_CURRENCY = os.getenv("BASE_CURRENCY", "MXN")
SCALE_DEFAULT = os.getenv("SCALE_DEFAULT", "UNIDAD")

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage")
DOCS_DIR = os.path.join(STORAGE_DIR, "docs")
CHECKPOINT_DB = os.path.join(STORAGE_DIR, "checkpoints.db")

os.makedirs(DOCS_DIR, exist_ok=True)
