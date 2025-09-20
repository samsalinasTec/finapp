#!/usr/bin/env bash
set -euo pipefail

# Carpetas
mkdir -p finapp/backend/routers
mkdir -p finapp/backend/services
mkdir -p finapp/backend/graph
mkdir -p finapp/backend/storage
mkdir -p finapp/frontend

# Archivos raíz
touch finapp/.env.example
touch finapp/.env



# Backend: archivos base
touch finapp/backend/app.py
touch finapp/backend/settings.py
touch finapp/backend/models.py

# Routers
touch finapp/backend/routers/ingest.py
touch finapp/backend/routers/review.py
touch finapp/backend/routers/ratios.py
touch finapp/backend/routers/runs.py

# Services
touch finapp/backend/services/parsers.py
touch finapp/backend/services/validators.py
touch finapp/backend/services/ratio_tools.py
touch finapp/backend/services/vertex_client.py
touch finapp/backend/services/gcs.py

# Graph
touch finapp/backend/graph/state.py
touch finapp/backend/graph/nodes.py
touch finapp/backend/graph/build.py

# Frontend
touch finapp/frontend/streamlit_app.py
