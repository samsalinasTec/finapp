import os
from dotenv import load_dotenv

load_dotenv()

# === Configuración API ===
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# === Umbrales de confianza ===
CONF_HIGH = float(os.getenv("CONF_HIGH", "0.80"))
CONF_MED = float(os.getenv("CONF_MED", "0.50"))

# === GCP / Vertex ===
GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
VERTEX_MODEL_ID = os.getenv("VERTEX_MODEL_ID", "gemini-2.0-flash")
GCS_BUCKET = os.getenv("GCS_BUCKET")

# === App Config ===
BASE_CURRENCY = os.getenv("BASE_CURRENCY", "MXN")
SCALE_DEFAULT = os.getenv("SCALE_DEFAULT", "UNIDAD")

# === ALMACENAMIENTO: Detectar si estamos en Cloud Run ===
# Cloud Run siempre setea la variable K_SERVICE
IS_CLOUD_RUN = os.getenv("K_SERVICE") is not None

if IS_CLOUD_RUN:
    # En Cloud Run: usar /tmp/ que es el único directorio escribible
    print("🔷 Ejecutando en Cloud Run - usando /tmp/ para almacenamiento temporal")
    STORAGE_DIR = "/tmp/finapp_storage"
    DOCS_DIR = "/tmp/finapp_storage/docs"
    CHECKPOINT_DB = "/tmp/finapp_storage/checkpoints.db"
else:
    # En local: usar directorio relativo como antes
    print("💻 Ejecutando en local - usando directorio ./storage")
    STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage")
    DOCS_DIR = os.path.join(STORAGE_DIR, "docs")
    CHECKPOINT_DB = os.path.join(STORAGE_DIR, "checkpoints.db")

# Crear directorios si no existen
try:
    os.makedirs(DOCS_DIR, exist_ok=True)
    print(f"✅ Directorio DOCS_DIR creado/verificado: {DOCS_DIR}")
except Exception as e:
    print(f"⚠️ Advertencia: No se pudo crear DOCS_DIR: {e}")
    # En Cloud Run esto no es crítico si usamos GCS directamente

# === VALIDACIÓN: Si estamos en Cloud Run, GCS_BUCKET es obligatorio ===
if IS_CLOUD_RUN and not GCS_BUCKET:
    print("⚠️ ADVERTENCIA: Ejecutando en Cloud Run sin GCS_BUCKET configurado.")
    print("   Los archivos temporales se perderán al reiniciar la instancia.")
    print("   Configura GCS_BUCKET para almacenamiento permanente.")
