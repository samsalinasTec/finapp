#!/bin/bash
set -e

echo "🚀 Iniciando FinApp..."

# Configurar variables de entorno
export API_PORT=7070
export API_BASE="http://localhost:${API_PORT}/api/v1"
export STREAMLIT_SERVER_PORT=${PORT:-8080}
export STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Iniciar FastAPI en background
echo "📡 Iniciando API Backend en puerto ${API_PORT}..."
cd /app
python -m uvicorn finapp.backend.app:app \
    --host 0.0.0.0 \
    --port ${API_PORT} \
    --workers 1 &

# Esperar que el backend esté listo
echo "⏳ Esperando que el backend esté listo..."
sleep 5

# Verificar que el backend responda
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost:${API_PORT}/docs > /dev/null 2>&1; then
        echo "✅ Backend listo!"
        break
    fi
    echo "Intento $((attempt+1))/$max_attempts..."
    sleep 2
    attempt=$((attempt+1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Error: Backend no respondió después de $max_attempts intentos"
    exit 1
fi

# Iniciar Streamlit
echo "🎨 Iniciando Frontend Streamlit..."
cd /app
streamlit run finapp/frontend/streamlit_app.py \
    --server.port ${STREAMLIT_SERVER_PORT} \
    --server.address 0.0.0.0 \
    --server.baseUrlPath / \
    --browser.gatherUsageStats false \
    --server.fileWatcherType none