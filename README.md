# AI Metadata Mapping Dashboard

An AI-powered dashboard for extracting database metadata, exploring schemas and relationships, and generating business-friendly metadata mappings.

## Features

- User registration and JWT authentication
- Database connection and metadata extraction
- Schema and table exploration
- Table relationship visualization
- AI-powered business entity mapping
- AI-powered column mapping
- JSON and TXT metadata export
- Local AI processing using Ollama

## Supported Databases

The backend supports:

- PostgreSQL
- MySQL
- SQL Server
- Oracle
- SQLite
- MongoDB
- Firebase / Firestore
- DynamoDB
- Cassandra

## Tech Stack

### Frontend

- React
- Vite
- Material UI
- React Router
- Axios
- JavaScript

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT Authentication

### AI

- Ollama
- Llama 3.2 3B

## Project Structure

```text
ai-metadata-mapping-dashboard/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── database/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── tests/
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── components/
    │   ├── context/
    │   ├── hooks/
    │   ├── layouts/
    │   ├── pages/
    │   ├── routes/
    │   ├── services/
    │   └── styles/
    ├── package.json
    └── vite.config.js
```

## Setup

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a `backend/.env` file:

```env
DATABASE_URL=<your-database-url>
SECRET_KEY=<your-secret-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Start the backend:

```powershell
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

### Frontend

```powershell
cd frontend
npm install
```

Create a `frontend/.env` file:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the frontend:

```powershell
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## AI Setup

The AI mapping functionality uses Ollama with the following model:

```text
llama3.2:3b
```

Make sure Ollama is installed and the model is available locally before using the AI mapping features.

## Testing

The backend test suite was verified during development with:

```text
85 tests passing
```

Run the backend tests with:

```powershell
pytest
```

## Security

Do not commit sensitive files or credentials, including:

- `.env` files
- Database passwords
- JWT secrets
- API keys
- Private keys
- Service-account credentials

## Project Status

Core frontend and backend functionality has been implemented, integrated, and tested locally.

The application supports database metadata extraction, schema exploration, relationship analysis, AI-powered metadata mapping, authentication, and metadata export.