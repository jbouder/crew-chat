# Crew Chat

An agentic chatbot application powered by CrewAI and AWS Bedrock, with a FastAPI backend and React frontend.

## Features

- 🤖 AI-powered chat using AWS Bedrock LLM
- 🚀 CrewAI agent orchestration
- ⚡ FastAPI backend with async support
- 💬 Modern React chat UI
- 🐳 Docker Compose support
- 🔒 CORS enabled for local development

## Project Structure

```
crew-chat/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── agents.py         # CrewAI agent configuration
│   ├── config.py         # Configuration settings
│   ├── requirements.txt  # Python dependencies
│   ├── Dockerfile        # Backend container
│   └── .env.example      # Environment variables template
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatBox.jsx
│   │   │   └── ChatBox.css
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── Dockerfile        # Frontend container
│   ├── nginx.conf        # Nginx configuration
│   └── package.json
├── docker-compose.yml    # Docker Compose configuration
├── .env.example          # Root environment variables
└── README.md
```

## Prerequisites

- Docker and Docker Compose (recommended)
- Or for local development:
  - Python 3.10+
  - Node.js 18+
- AWS account with Bedrock access
- Configured AWS credentials

## Quick Start with Docker Compose

1. Clone the repository and navigate to it:
   ```bash
   git clone <repository-url>
   cd crew-chat
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials
   ```

3. Start the application:
   ```bash
   docker compose up --build
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

To stop the application:
```bash
docker compose down
```

## Local Development Setup

### Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials and settings
   ```

5. Start the server:
   ```bash
   python main.py
   # Or: uvicorn main:app --reload
   ```

The API will be available at http://localhost:8000

### Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The UI will be available at http://localhost:5173

## API Endpoints

- `GET /` - Health check
- `GET /health` - Health status
- `POST /chat` - Send a chat message

### Chat Request Example

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
```

## Technologies

- **Backend**: Python, FastAPI, CrewAI, AWS Bedrock, LangChain
- **Frontend**: React, Vite
- **LLM**: AWS Bedrock (Claude 3 Sonnet)

## License

MIT