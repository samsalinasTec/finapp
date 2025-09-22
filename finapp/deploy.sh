#!/usr/bin/env bash
set -euo pipefail

# ===========================
#  FinApp - Cloud Run Deploy
# ===========================
# Mejores prácticas aplicadas:
# - Usa Artifact Registry (no GCR)
# - Selector de Service Account existente
# - Buckets limitados al proyecto actual
# - Tag de imagen INMUTABLE (fecha + git sha)
# - Concurrency y max-instances ajustables
# - Roles mínimos razonables + opcional Vertex
# - Env no sensible en .env.yaml (usa Secret Manager para secretos)

# ----- Colores -----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}🚀 Script de Despliegue de FinApp a Google Cloud Run${NC}"
echo "=================================================="

# ----- Prechequeos -----
if ! command -v gcloud &> /dev/null; then
  echo -e "${RED}❌ Error: gcloud CLI no está instalado${NC}"
  echo "Instala desde: https://cloud.google.com/sdk/docs/install"
  exit 1
fi

# PARCHE: si no hay Docker local, usa Cloud Build (remoto)
if ! command -v docker &> /dev/null; then
  echo -e "${YELLOW}⚠️ Docker no está disponible. Usaré Cloud Build (remoto).${NC}"
  USE_CLOUD_BUILD=1
else
  USE_CLOUD_BUILD=0
fi

# ----- Detectar config actual -----
echo -e "\n${YELLOW}📝 Detectando configuración actual...${NC}"
CURRENT_PROJECT="$(gcloud config get-value project 2>/dev/null || true)"
CURRENT_REGION="$(gcloud config get-value compute/region 2>/dev/null || true)"
CURRENT_ACCOUNT="$(gcloud config get-value account 2>/dev/null || true)"

# Proyecto
if [[ -z "${CURRENT_PROJECT}" ]]; then
  read -rp "Ingresa tu PROJECT_ID de GCP: " PROJECT_ID
  gcloud config set project "$PROJECT_ID" >/dev/null
else
  echo -e "${GREEN}✓${NC} Proyecto detectado: ${GREEN}${CURRENT_PROJECT}${NC}"
  read -rp "¿Usar este proyecto? (Y/n): " -n 1 -r; echo
  if [[ $REPLY =~ ^[Nn]$ ]]; then
    read -rp "Ingresa el PROJECT_ID a usar: " PROJECT_ID
    gcloud config set project "$PROJECT_ID" >/dev/null
  else
    PROJECT_ID="$CURRENT_PROJECT"
  fi
fi

# Región
if [[ -z "${CURRENT_REGION}" ]]; then
  read -rp "Ingresa la región (default: us-central1): " REGION
  REGION=${REGION:-us-central1}
  gcloud config set compute/region "$REGION" >/dev/null
else
  echo -e "${GREEN}✓${NC} Región detectada: ${GREEN}${CURRENT_REGION}${NC}"
  read -rp "¿Usar esta región? (Y/n): " -n 1 -r; echo
  if [[ $REPLY =~ ^[Nn]$ ]]; then
    read -rp "Ingresa la región a usar: " REGION
    gcloud config set compute/region "$REGION" >/dev/null
  else
    REGION="$CURRENT_REGION"
  fi
fi

# Nombre de servicio
read -rp "Nombre del servicio (default: finapp): " SERVICE_NAME
SERVICE_NAME=${SERVICE_NAME:-finapp}

# Ajustes de escalado (sanos por defecto para dev)
read -rp "Max instances (default: 5): " MAX_INSTANCES
MAX_INSTANCES=${MAX_INSTANCES:-5}
read -rp "Concurrency por instancia (default: 10; usa 1 si es pesado/Streamlit): " CONCURRENCY
CONCURRENCY=${CONCURRENCY:-10}

# Mostrar configuración
echo -e "\n${GREEN}Configuración a utilizar:${NC}"
echo "  Cuenta:          ${CURRENT_ACCOUNT:-(no detectada)}"
echo "  Proyecto:        $PROJECT_ID"
echo "  Región:          $REGION"
echo "  Servicio:        $SERVICE_NAME"
echo "  Max instances:   $MAX_INSTANCES"
echo "  Concurrency:     $CONCURRENCY"
echo ""
read -rp "¿Continuar con esta configuración? (y/n): " -n 1 -r; echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Despliegue cancelado."
  exit 0
fi

# ----- APIs necesarias -----
echo -e "\n${YELLOW}1️⃣ Habilitando APIs necesarias...${NC}"
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com \
  storage.googleapis.com \
  iam.googleapis.com \
  cloudbuild.googleapis.com >/dev/null

# ----- Buckets (solo del proyecto actual) -----
echo -e "\n${YELLOW}🗂️ Verificando buckets de GCS en el proyecto '${PROJECT_ID}'...${NC}"
# Nota: gcloud storage buckets list imprime "gs://bucket"
EXISTING_BUCKETS="$(gcloud storage buckets list --project="$PROJECT_ID" --format='value(name)' 2>/dev/null || true)"

if [[ -n "${EXISTING_BUCKETS}" ]]; then
  echo "Buckets encontrados:"
  # Limpia gs:// y slashes
  echo "$EXISTING_BUCKETS" | sed -E 's#^gs://##; s#/$##' | nl
  echo ""
  read -rp "¿Quieres usar un bucket existente? (y/N): " -n 1 -r; echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -rp "Ingresa el nombre del bucket (sin gs://): " GCS_BUCKET
  else
    read -rp "¿Crear un nuevo bucket? (y/N): " -n 1 -r; echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      GCS_BUCKET="${SERVICE_NAME}-storage-$RANDOM"
      echo "Creando bucket: gs://${GCS_BUCKET} (location: ${REGION})"
      gcloud storage buckets create "gs://${GCS_BUCKET}" \
        --project="$PROJECT_ID" \
        --location="$REGION" \
        --uniform-bucket-level-access >/dev/null
    fi
  fi
else
  read -rp "No hay buckets. ¿Crear un bucket GCS? (y/N): " -n 1 -r; echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    GCS_BUCKET="${SERVICE_NAME}-storage-$RANDOM"
    echo "Creando bucket: gs://${GCS_BUCKET} (location: ${REGION})"
    gcloud storage buckets create "gs://${GCS_BUCKET}" \
      --project="$PROJECT_ID" \
      --location="$REGION" \
      --uniform-bucket-level-access >/dev/null
  fi
fi

# ----- Service Account: elegir existente o crear -----
echo -e "\n${YELLOW}2️⃣ Seleccionando Service Account...${NC}"
read -rp "¿Usar una Service Account existente? (Y/n): " -n 1 -r; echo
SA_EMAIL=""
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
  mapfile -t SA_LIST < <(gcloud iam service-accounts list --project="$PROJECT_ID" --format="value(email)")
  if [[ ${#SA_LIST[@]} -eq 0 ]]; then
    echo -e "${RED}No hay Service Accounts en el proyecto.${NC}"
  else
    echo "Selecciona la SA a usar:"
    PS3="Opción: "
    select SA_SELECTED in "${SA_LIST[@]}"; do
      if [[ -n "${SA_SELECTED:-}" ]]; then
        SA_EMAIL="$SA_SELECTED"
        break
      fi
    done
  fi
fi

if [[ -z "${SA_EMAIL}" ]]; then
  read -rp "Nombre para nueva SA (sin @): " SA_NAME
  SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
  echo "Creando Service Account: $SA_EMAIL"
  gcloud iam service-accounts create "$SA_NAME" \
    --display-name="FinApp Service Account" \
    --project="$PROJECT_ID" >/dev/null
fi

echo -e "${GREEN}✓${NC} Usando SA: ${GREEN}${SA_EMAIL}${NC}"

# OMITIR asignación de permisos si ya es OWNER
echo "Verificando permisos existentes..."
EXISTING_ROLES=$(gcloud projects get-iam-policy "$PROJECT_ID" \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:${SA_EMAIL}" \
    --format="value(bindings.role)" 2>/dev/null || echo "")

if echo "$EXISTING_ROLES" | grep -q "roles/owner"; then
    echo -e "${GREEN}✓${NC} La SA tiene rol OWNER - omitiendo asignación de permisos adicionales"
else
    echo "La SA NO es owner. Permisos actuales:"
    echo "$EXISTING_ROLES"
    read -rp "¿Intentar asignar permisos básicos? (y/N): " -n 1 -r; echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for ROLE in "roles/aiplatform.user" "roles/logging.logWriter"; do
            echo "  Intentando asignar $ROLE..."
            gcloud projects add-iam-policy-binding "$PROJECT_ID" \
                --member="serviceAccount:${SA_EMAIL}" \
                --role="$ROLE" 2>/dev/null || echo "  ⚠️ No se pudo asignar $ROLE"
        done
    fi
fi

# Si hay bucket, dar permisos a nivel bucket (esto SÍ puede ser necesario incluso con OWNER)
if [[ -n "${GCS_BUCKET:-}" ]]; then
  echo "Verificando permisos sobre el bucket gs://${GCS_BUCKET}..."
  if ! gsutil iam get "gs://${GCS_BUCKET}" | grep -q "${SA_EMAIL}"; then
    echo "Concediendo acceso al bucket..."
    gcloud storage buckets add-iam-policy-binding "gs://${GCS_BUCKET}" \
      --member="serviceAccount:${SA_EMAIL}" \
      --role="roles/storage.objectAdmin" 2>/dev/null || \
      echo "  ⚠️ No se pudo asignar permisos al bucket (puede que ya los tenga)"
  else
    echo -e "${GREEN}✓${NC} Ya tiene permisos sobre el bucket"
  fi
fi

# ----- Artifact Registry: repo + auth -----
echo -e "\n${YELLOW}3️⃣ Configurando Artifact Registry...${NC}"
REPO_NAME="${SERVICE_NAME}-repo"

# Crear repo si no existe
if ! gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$REPO_NAME" \
    --repository-format=docker \
    --location="$REGION" \
    --description="FinApp images" >/dev/null
  echo -e "${GREEN}✓${NC} Repositorio creado: ${REPO_NAME}"
else
  echo -e "${GREEN}✓${NC} Repositorio existente: ${REPO_NAME}"
fi

# Autenticación Docker con AR
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet

# Tag inmutable (fecha + git sha si disponible)
TAG="$(date +%Y%m%d-%H%M%S)"
if git rev-parse --short HEAD >/dev/null 2>&1; then
  TAG="${TAG}-$(git rev-parse --short HEAD)"
fi

IMAGE_URL="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME:$TAG"
LATEST_URL="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME:latest"

# Dar a Cloud Run (service agent) permiso de lectura del repo (por si acaso)
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")"
SERVICE_AGENT="service-${PROJECT_NUMBER}@serverless-robot-prod.iam.gserviceaccount.com"
gcloud artifacts repositories add-iam-policy-binding "$REPO_NAME" \
  --location="$REGION" \
  --member="serviceAccount:${SERVICE_AGENT}" \
  --role="roles/artifactregistry.reader" >/dev/null || true

# ----- Build & Push -----
if [[ "${USE_CLOUD_BUILD:-0}" -eq 1 ]]; then
  echo -e "\n${YELLOW}4️⃣ Construyendo y subiendo imagen con Cloud Build (remoto)...${NC}"
  gcloud builds submit --tag "$IMAGE_URL" --project "$PROJECT_ID" --region "$REGION"

  # Mantener también el tag :latest (equivalente a docker tag/push latest)
  DIGEST="$(gcloud artifacts docker images describe "$IMAGE_URL" --format='value(image_summary.digest)')"
  gcloud artifacts docker tags add \
    "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME@${DIGEST}" \
    "$LATEST_URL"
else
  echo -e "\n${YELLOW}4️⃣ Construyendo imagen Docker...${NC}"
  docker build -t "$IMAGE_URL" .

  # (Opcional) mantiene conveniencia con :latest además del tag inmutable
  docker tag "$IMAGE_URL" "$LATEST_URL"

  echo -e "\n${YELLOW}5️⃣ Subiendo imagen a Artifact Registry...${NC}"
  docker push "$IMAGE_URL"
  docker push "$LATEST_URL"
fi

# ----- Variables de entorno (no sensibles) -----
echo -e "\n${YELLOW}6️⃣ Generando .env.yaml (no incluyas secretos aquí)...${NC}"
cat > .env.yaml << EOF
GCP_PROJECT: $PROJECT_ID
GCP_LOCATION: $REGION
VERTEX_MODEL_ID: gemini-2.0-flash
CONF_HIGH: "0.80"
CONF_MED: "0.50"
BASE_CURRENCY: MXN
SCALE_DEFAULT: UNIDAD
API_HOST: 0.0.0.0
EOF

if [[ -n "${GCS_BUCKET:-}" ]]; then
  echo "GCS_BUCKET: $GCS_BUCKET" >> .env.yaml
fi

# ----- Despliegue a Cloud Run -----
echo -e "\n${YELLOW}7️⃣ Desplegando a Cloud Run...${NC}"
# Nota: Asegúrate de que tu app escuche en 0.0.0.0:$PORT o usa --port acorde (p.ej., 8501)
read -rp "Puerto de la app dentro del contenedor (default: 8080): " APP_PORT
APP_PORT=${APP_PORT:-8080}  # ← Cambiar a 8080

# Si el servicio ya existe, simplemente crea nueva revisión
if gcloud run services describe "$SERVICE_NAME" --region "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1; then
  echo -e "${YELLOW}⚠️ Servicio ya existe. Se actualizará con una nueva revisión.${NC}"
fi

gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE_URL" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --concurrency "$CONCURRENCY" \
  --max-instances "$MAX_INSTANCES" \
  --min-instances 0 \
  --port "$APP_PORT" \
  --env-vars-file .env.yaml \
  --project "$PROJECT_ID" >/dev/null

# ----- URL del servicio -----
echo -e "\n${YELLOW}8️⃣ Obteniendo URL del servicio...${NC}"
SERVICE_URL="$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --format 'value(status.url)')"

# ----- Resumen -----
echo -e "\n${GREEN}✅ ¡Despliegue completado exitosamente!${NC}\n"
echo -e "${GREEN}🎉 Tu aplicación está disponible en:${NC}"
echo -e "${GREEN}${SERVICE_URL}${NC}\n"

echo -e "${YELLOW}📊 Resumen del despliegue:${NC}"
echo "  Project:          $PROJECT_ID"
echo "  Service Account:  $SA_EMAIL"
echo "  Región:           $REGION"
echo "  Servicio:         $SERVICE_NAME"
echo "  Imagen (inmutable): $IMAGE_URL"
echo "  Imagen (latest):    $LATEST_URL"
if [[ -n "${GCS_BUCKET:-}" ]]; then
  echo "  Bucket GCS:       gs://$GCS_BUCKET"
fi
echo ""

echo -e "${YELLOW}📝 Comandos útiles:${NC}"
echo "  Ver logs en tiempo real:"
echo "    gcloud logs tail --service=$SERVICE_NAME"
echo ""
echo "  Ver logs recientes:"
echo "    gcloud run logs read --service=$SERVICE_NAME --region=$REGION --limit=100"
echo ""
echo "  Actualizar variables de entorno:"
echo "    gcloud run services update $SERVICE_NAME --update-env-vars KEY=value --region=$REGION"
echo ""
echo "  Inspeccionar revisiones:"
echo "    gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.traffic)'"
echo ""
echo -e "${YELLOW}🔐 Notas de seguridad:${NC}"
echo "  - Usa Secret Manager para credenciales y secretos."
echo "  - Mantén .env.yaml para config no sensible."
echo ""
echo -e "${GREEN}¡Listo! 🚀${NC}"
