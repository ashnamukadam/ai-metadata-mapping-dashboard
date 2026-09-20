# Backend

FastAPI service for the AI Metadata Mapping Dashboard.

## Backend Architecture

```text
backend/
├── app/
│   ├── api/
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── metadata_extraction.py
│   │   ├── relationship.py
│   │   └── ai_mapping.py
│   │
│   ├── database/
│   │   └── connection.py
│   │
│   ├── models/
│   │   ├── metadata_column.py
│   │   ├── metadata_constraint.py
│   │   ├── metadata_index.py
│   │   └── metadata_table.py
│   │
│   ├── schemas/
│   │   ├── ai_mapping.py
│   │   ├── ai_prompt_preview.py
│   │   └── export_mapping.py
│   │
│   ├── services/
│   │   ├── ai_mapping_service.py
│   │   ├── ai_prompt_preview_service.py
│   │   └── metadata_extraction_service.py
│   │
│   └── main.py
│
├── tests/
├── requirements.txt
└── .env
```

## API Modules

| Module | Purpose |
|---|---|
| `auth.py` | Registration, login and authenticated-user information |
| `dashboard.py` | Dashboard statistics |
| `metadata_extraction.py` | Database metadata extraction and schema information |
| `relationship.py` | Database relationship information |
| `ai_mapping.py` | AI business and column mapping |
| `main.py` | FastAPI application configuration and routing |

## Metadata Workflow

```text
Database Connection
        ↓
Connection Validation
        ↓
Metadata Extraction
        ↓
Schema / Tables / Columns
        ↓
Relationship Detection
        ↓
AI Business Mapping
        ↓
AI Column Mapping
        ↓
Export Mapping
```

## Authentication

The backend uses:

- OAuth2 password flow
- JWT access tokens
- bcrypt password hashing
- Protected API endpoints

The authenticated user's information is available through:

```text
GET /auth/me
```

## Important API Endpoints

### Authentication

```text
POST /auth/register
POST /auth/login
GET  /auth/me
POST /auth/forgot-password
```

### Metadata

```text
POST /database/metadata
GET  /database/metadata
POST /database/schema-view
GET  /database/relationships
```

### AI Mapping

```text
POST /database/ai-prompt-preview
POST /database/ai-mapping
POST /database/column-mapping
```

### Export

```text
POST /database/export-mapping
```

## Environment Configuration

Create a local `.env` file:

```env
DATABASE_URL=postgresql://<username>:<password>@localhost:5432/<database>
SECRET_KEY=<your-secret-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Never commit `.env` files or database credentials.

## Running the Backend

From this directory:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Ollama

AI mapping uses a locally running Ollama instance.

Expected model:

```text
llama3.2:3b
```

Ollama API:

```text
http://127.0.0.1:11434/api/generate
```

The AI service sends metadata context to the local model and converts the response into the mapping structure consumed by the frontend.

## Testing

Run:

```powershell
pytest
```

The backend test suite was verified during development with:

```text
85 tests passing
```

## Development Notes

- Keep database credentials in `.env`.
- Keep AI processing local through Ollama.
- Backend API changes should be tested through Swagger and the frontend workflow.
- Frontend requests use the backend URL configured through `VITE_API_BASE_URL`.