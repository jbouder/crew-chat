# Patriot Life Member Center

A Member Center application for Patriot Life Insurance, a fictitious life insurance company serving military personnel and their families. Built with FastAPI, React, and PostgreSQL.

## Features

- 🏠 **Home Page** - Information about benefits for non-members
- 📊 **Member Dashboard** - View membership details, active benefits, and coverage summary
- 🔍 **Benefit Search & Enrollment** - Browse and enroll in available benefits
- 💬 **AI Chat Assistant** - CrewAI-powered chatbot with personalized member support
- 🗃️ **PostgreSQL Database** - Store member profiles and benefit enrollments
- 🐳 **Docker Compose** - Easy deployment with all services

## AI Chat Assistant

The application includes an AI-powered chat assistant built with [CrewAI](https://www.crewai.com/) and AWS Bedrock. The assistant can answer questions about insurance products and provide personalized information for logged-in members.

### Agents

The chat system uses specialized AI agents powered by AWS Bedrock:

| Agent                         | Role                   | Description                                                                                                                                                 | Tools                                                                                                          |
| ----------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **AI Assistant Coordinator**  | Main orchestrator      | Handles all user interactions, answers general questions using the knowledge base, and fetches personalized member data when needed                         | Get Member Profile, Get Current Benefits and Enrollments, Get Available Benefits, Get Benefit Coverage Summary |
| **Member Profile Specialist** | Profile queries        | Retrieves personal information, military service details (branch, rank, active duty status), and membership information (member number, status, start date) | Get Member Profile                                                                                             |
| **Benefits Specialist**       | Benefits & enrollments | Provides current enrollments, available plans, eligibility requirements, premium costs, beneficiary designations, and coverage summaries by category        | Get Current Benefits and Enrollments, Get Available Benefits, Get Benefit Coverage Summary                     |

### Agent Tools

| Tool                                     | Description                                                                                            |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **Get Member Profile**                   | Retrieves the logged-in member's personal details, military service information, and membership status |
| **Get Current Benefits and Enrollments** | Fetches active benefit enrollments with coverage details, premiums, and beneficiary information        |
| **Get Available Benefits**               | Lists all available benefit plans with eligibility indicators based on the member's profile            |
| **Get Benefit Coverage Summary**         | Provides a high-level summary of the member's total coverage grouped by category                       |

### Knowledge Base Integration

The assistant integrates with AWS Bedrock Knowledge Base to retrieve relevant information about insurance products from documentation stored in S3. This enables the agent to answer detailed questions about:

- SGLI, VGLI, FSGLI, and S-DVI coverage
- Disability and accident protection plans
- Critical illness and supplemental life insurance
- Eligibility requirements and enrollment procedures

## Screenshots

The application includes:

- Public home page with benefit information
- Member login portal
- Dashboard with coverage summary and active enrollments
- Benefit catalog with search and filter capabilities
- Enrollment modal with beneficiary designation

## Project Structure

```
member-center/
├── backend/
│   ├── main.py           # FastAPI application with API endpoints
│   ├── agents.py         # CrewAI agent definitions and tools
│   ├── models.py         # SQLAlchemy database models
│   ├── database.py       # Database connection and seeding
│   ├── config.py         # Configuration settings
│   ├── requirements.txt  # Python dependencies
│   └── Dockerfile        # Backend container
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.tsx        # Public home page
│   │   │   ├── Login.tsx       # Member login
│   │   │   ├── Dashboard.tsx   # Member dashboard
│   │   │   └── Benefits.tsx    # Benefit search & enrollment
│   │   ├── components/
│   │   │   ├── Navigation.tsx  # Navigation bar
│   │   │   └── ChatAssistant.tsx # AI chat widget
│   │   ├── api.ts              # API service
│   │   ├── types.ts            # TypeScript types
│   │   ├── App.tsx             # Main app with routing
│   │   └── main.tsx
│   ├── Dockerfile        # Frontend container
│   ├── nginx.conf        # Nginx configuration
│   └── package.json
├── data/                 # Knowledge base documents
│   ├── sgli.md
│   ├── vgli.md
│   ├── fsgli.md
│   └── ...
├── docker-compose.yml    # Docker Compose with PostgreSQL
└── README.md
```

## Prerequisites

- Docker and Docker Compose (recommended)
- Or for local development:
  - Python 3.10+
  - Node.js 18+
  - PostgreSQL 16+

## Quick Start with Docker Compose

1. Clone the repository and navigate to it:

   ```bash
   git clone <repository-url>
   cd crew-chat
   ```

2. Start all services (PostgreSQL, Backend, Frontend):

   ```bash
   docker compose up --build
   ```

3. Access the application:

   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

4. Demo credentials:
   - **Email**: john.doe@military.mil
   - **Password**: demo

To stop the application:

```bash
docker compose down

# To also remove the database volume:
docker compose down -v
```

## Local Development Setup

### Database

Start PostgreSQL:

```bash
docker compose up postgres -d
```

Or install PostgreSQL locally and create a database:

```sql
CREATE DATABASE membercenter;
CREATE USER membercenter WITH PASSWORD 'membercenter_password';
GRANT ALL PRIVILEGES ON DATABASE membercenter TO membercenter;
```

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

4. Set the database URL (if not using Docker):

   ```bash
   export DATABASE_URL=postgresql://membercenter:membercenter_password@localhost:5432/membercenter
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

### Health

- `GET /` - Health check
- `GET /health` - Health status

### Chat

- `POST /api/chat` - Send a message to the AI assistant (accepts `message` and optional `user_id` for personalized responses)

### Members

- `POST /api/members/login` - Member login
- `GET /api/members/{member_id}` - Get member by ID
- `GET /api/members/{member_id}/dashboard` - Get member dashboard data
- `POST /api/members` - Create new member

### Benefits

- `GET /api/benefits` - List all benefits (filter by category)
- `GET /api/benefits/{benefit_id}` - Get benefit details

### Enrollments

- `GET /api/members/{member_id}/enrollments` - List member enrollments
- `POST /api/members/{member_id}/enrollments` - Enroll in benefit
- `DELETE /api/members/{member_id}/enrollments/{enrollment_id}` - Cancel enrollment

## Database Models

### Member

- Personal information (name, email, address)
- Military service details (branch, rank, active duty status)
- Membership information (member number, status)

### Benefit

- Coverage details (amount, premium, deductible)
- Category (Life Insurance, Disability, Accident, Critical Illness, Supplemental)
- Eligibility requirements (age range, active duty requirement)

### Enrollment

- Links members to benefits
- Tracks effective dates and status
- Stores beneficiary information

## Technologies

- **Backend**: Python, FastAPI, SQLAlchemy, Pydantic
- **AI/ML**: CrewAI, AWS Bedrock (Claude), AWS Bedrock Knowledge Base
- **Frontend**: React, TypeScript, React Router, Vite
- **Database**: PostgreSQL
- **Deployment**: Docker, Nginx

## Available Benefits (Demo Data)

1. **SGLI** - Service Members' Group Life Insurance ($400,000)
2. **FSGLI** - Family Service Members' Group Life Insurance ($100,000)
3. **VGLI** - Veterans' Group Life Insurance ($250,000)
4. **S-DVI** - Service-Disabled Veterans Insurance ($10,000)
5. **Military Disability Protection Plus** ($5,000/mo)
6. **Accident Protection Plan** ($50,000)
7. **Critical Illness Shield** ($75,000)
8. **Supplemental Term Life** ($500,000)

## License

MIT
