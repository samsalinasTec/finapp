# FinApp - Financial Statement Analysis Platform 📊

An intelligent platform for automated extraction and analysis of financial data from multiple document formats (PDF, Excel, CSV, Images), powered by AI and featuring Human-in-the-Loop (HITL) validation.

## Key Features

- **Multi-format Document Processing**: Supports PDF, Excel (.xlsx, .xls), CSV, and image files
- **AI-Powered Extraction**: Uses Google Vertex AI (Gemini 2.0 Flash) for intelligent data extraction
- **Human-in-the-Loop (HITL)**: Interactive validation interface for reviewing and correcting AI extractions
- **Financial Ratios Calculation**: Automatic computation of 13+ key financial metrics
- **What-if Analysis**: Interactive scenario modeling with real-time ratio recalculation
- **Cloud-Native Architecture**: Designed for Google Cloud Run with automatic scaling
- **Production-Ready**: Complete CI/CD pipeline with automated deployment script

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│  FastAPI Backend │────▶│  Google Cloud   │
│   (Frontend)    │     │   (REST API)     │     │  Services       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                          │
                               ▼                          ▼
                        ┌──────────────┐         ┌────────────────┐
                        │  LangGraph   │         │  Vertex AI     │
                        │  Workflow    │         │  GCS Storage   │
                        └──────────────┘         └────────────────┘
```

### Technology Stack

- **Backend**: FastAPI, LangGraph, Pydantic
- **Frontend**: Streamlit, Plotly
- **AI/ML**: Google Vertex AI (Gemini 2.0 Flash), LangChain
- **Cloud**: Google Cloud Run, Cloud Storage, Artifact Registry
- **Document Processing**: PDFPlumber, Pandas, OpenPyXL, Tesseract OCR
- **Container**: Docker (multi-stage build)

## Financial Metrics Calculated

### Liquidity Ratios
- Current Ratio
- Quick Ratio (Acid-Test)
- Working Capital

### Leverage Ratios
- Debt-to-Equity
- Interest Coverage

### Profitability Ratios
- Gross Margin
- Operating Margin
- Net Margin
- Return on Assets (ROA)
- Return on Equity (ROE)
- EBITDA Margin

### Efficiency Ratios
- Asset Turnover
- Inventory Turnover

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Docker (optional, for containerized deployment)
- Google Cloud SDK (for cloud deployment)
- Google Cloud Project with enabled APIs:
  - Cloud Run API
  - Vertex AI API
  - Cloud Storage API
  - Artifact Registry API

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd finapp
   ```

2. **Install dependencies**
   ```bash
   pip install -e .
   # or using uv for faster installation
   uv pip install -e .
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**
   ```bash
   # Terminal 1: Start Backend
   cd backend
   uvicorn app:app --reload --port 8000
   
   # Terminal 2: Start Frontend
   cd frontend
   streamlit run streamlit_app.py
   ```

5. **Access the application**
   - Frontend: http://localhost:8501
   - API Documentation: http://localhost:8000/docs

### Docker Deployment (Local)

```bash
# Build the image
docker build -t finapp .

# Run the container
docker run -p 8080:8080 --env-file .env finapp
```

### Cloud Deployment (Google Cloud Run)

The project includes an automated deployment script with best practices:

```bash
# Make the script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

The script will:
- ✅ Configure your GCP project and region
- ✅ Set up necessary service accounts and permissions
- ✅ Create GCS bucket for document storage (optional)
- ✅ Build and push Docker image to Artifact Registry
- ✅ Deploy to Cloud Run with auto-scaling configuration
- ✅ Provide the public URL for your application

## 📁 Project Structure

```
finapp/
├── backend/
│   ├── app.py              # FastAPI application entry point
│   ├── models.py            # Pydantic models for data validation
│   ├── settings.py          # Configuration management
│   ├── routers/            # API endpoints
│   │   ├── ingest.py       # Document upload and processing
│   │   ├── review.py       # HITL validation endpoints
│   │   ├── ratios.py       # Financial calculations
│   │   └── runs.py         # Session management
│   ├── services/           # Business logic
│   │   ├── parsers.py      # Document parsing utilities
│   │   ├── validators.py   # Data validation logic
│   │   ├── ratio_tools.py  # Financial ratio calculations
│   │   ├── vertex_client.py # Vertex AI integration
│   │   └── gcs.py          # Cloud Storage operations
│   └── graph/              # LangGraph workflow
│       ├── state.py        # State management
│       ├── nodes.py        # Processing nodes
│       └── build.py        # Graph construction
├── frontend/
│   └── streamlit_app.py    # Streamlit UI application
├── Dockerfile              # Multi-stage Docker build
├── start.sh                # Container startup script
├── deploy.sh               # Automated GCP deployment
├── pyproject.toml          # Python project dependencies
└── .env.example            # Environment variables template
```

## Workflow Process

1. **Document Upload**: User uploads financial statement (PDF/Excel/CSV/Image)
2. **AI Extraction**: Vertex AI analyzes and extracts financial data
3. **Validation Check**: System evaluates confidence scores
4. **HITL Review** (if needed): User reviews and corrects low-confidence extractions
5. **Ratio Calculation**: Automatic computation of all financial metrics
6. **Dashboard Display**: Interactive visualization of results
7. **What-if Analysis**: User can modify values and see updated ratios

## Configuration

### Environment Variables

```bash
# GCP Configuration
GCP_PROJECT=your-project-id
GCP_LOCATION=us-central1
GCS_BUCKET=your-bucket-name      # Optional: for document storage

# AI Model
VERTEX_MODEL_ID=gemini-2.0-flash

# Confidence Thresholds
CONF_HIGH=0.80                    # High confidence threshold
CONF_MED=0.50                     # Medium confidence threshold

# Application Settings
BASE_CURRENCY=MXN
SCALE_DEFAULT=UNIDAD              # UNIDAD | MILES | MILLONES
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/ingest` | POST | Upload and process financial documents |
| `/api/v1/review` | POST | Submit human corrections for HITL |
| `/api/v1/ratios/whatif` | POST | Calculate what-if scenarios |
| `/api/v1/runs/{run_id}` | GET | Retrieve processing session status |
| `/docs` | GET | Interactive API documentation (Swagger UI) |

## Testing the Application

1. **Upload a Test Document**: Try with a financial statement PDF or Excel file
2. **Review Extractions**: Check the HITL interface if confidence is low
3. **Validate Ratios**: Verify calculated financial metrics
4. **Test What-if**: Modify values and observe ratio changes


## Performance Features

- **Multi-stage Docker build**: Optimized image size (~500MB)
- **Async processing**: Non-blocking document analysis
- **Auto-scaling**: Cloud Run automatically scales based on load
- **Caching**: LangGraph state management for session persistence
- **Efficient parsing**: Specialized libraries for each file format

## Monitoring and Logs

```bash
# View real-time logs
gcloud logs tail --service=finapp

# View recent logs
gcloud run logs read --service=finapp --region=us-central1 --limit=100

# Access metrics in Cloud Console
# https://console.cloud.google.com/run
```


## Future Enhancements

The following features are planned for future development:

### Testing & Quality Assurance
- **Unit Tests**: Comprehensive test suite for ratio calculations and validators
- **Integration Tests**: End-to-end testing of document processing pipeline
- **Load Testing**: Performance benchmarks for concurrent document processing
- **Data Validation Tests**: Edge cases for various financial statement formats

### Advanced Features
- **Multi-period Analysis**: Compare financial statements across multiple periods
- **Industry Benchmarking**: Compare ratios against industry standards
- **Automated Anomaly Detection**: ML-based detection of unusual financial patterns
- **Export Functionality**: Generate professional PDF reports with analysis
- **Multi-language Support**: Extend beyond Spanish/English document processing
- **Batch Processing**: Handle multiple documents simultaneously
- **Real-time Collaboration**: Multiple users reviewing the same document

### Architecture Improvements
- **Structured Logging**: Integration with Cloud Logging for better observability
- **API Rate Limiting**: Implement rate limiting for production use
- **Database Persistence**: Move from SQLite to Cloud SQL for production

### DevOps & Monitoring
- **GitHub Actions CI/CD**: Automated testing and deployment pipeline
- **Monitoring Dashboard**: Custom metrics and alerts in Cloud Monitoring

### AI/ML Enhancements
- **Fine-tuned Models**: Custom models for specific financial document types
- **Confidence Score Calibration**: Improve accuracy of confidence thresholds
- **Active Learning**: Learn from user corrections to improve extraction
- **OCR Improvements**: Better handling of scanned documents with poor quality

 
**Created**: 2025  
**Stack**: FastAPI + Streamlit + Google Cloud + Vertex AI  