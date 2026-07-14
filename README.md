# Here are your Instructions
Cognify 2026 🎓
AI-Powered School Management, Learning & Career Intelligence Platform
Cognify 2026 is a full-stack, enterprise-grade school management platform that combines AI-driven learning tools, biometric attendance, multilingual support, and career intelligence into a single unified system. Designed for schools, universities, and training organizations across Africa and beyond.
---
Table of Contents
Overview
Features
Tech Stack
Project Structure
Getting Started
Prerequisites
Environment Variables
Backend Setup
Frontend Setup
API Reference
User Roles
Supported Languages
Architecture
Testing
Contributing
---
Overview
Cognify 2026 is built on a FastAPI backend and a React 19 frontend, connected to a MongoDB database. It provides an AI-enhanced experience for students, teachers, school administrators, parents, and super-admins — all within a single platform.
Key capabilities:
AI Mentor & Study Tools — Personalized tutoring, knowledge graphs, and adaptive learning paths
Course Management — Create, manage, and publish courses with AI-generated content
Attendance Tracking — Manual, RFID-based, and biometric attendance systems
Credentials & Certifications — Issue and verify digital credentials/certificates
Career Intelligence — LinkedIn integration, career guidance, and learning journeys
Virtual Classrooms — Zoom integration and study groups
Multilingual Support — English, Shona, Ndebele, Swahili, and Zulu
Payment Management — Stripe-powered fees, subscriptions, and invoicing
---
Features
🤖 AI & Learning
Feature	Description
AI Mentor	Personalized AI tutor powered by Google Gemini / OpenAI
AI Training Engine	Build and fine-tune custom AI knowledge bases
Assignment Generator	Auto-generate assignments and quizzes from syllabi
Learn by Teaching	Socratic AI that lets students "teach" concepts to reinforce learning
Live Research	AI-assisted real-time research digest
Syllabus Ingestion	Upload and parse curriculum documents (PDF, DOCX, PPTX)
Knowledge Graph	Visual concept map of a student's learning
KTCE Learning	Key Takeaway / Concept Extraction learning mode
Outcome Learning	Goal-oriented learning path generation
Multi-Subject Learning	Cross-disciplinary AI lesson support
VR Learning	Immersive VR-ready lesson frameworks
Question Analysis	AI-powered exam question performance analytics
🏫 School Management
Feature	Description
Organization Management	Multi-tenant support for schools and organizations
Student & Teacher Portals	Dedicated dashboards per role
Attendance (Manual / RFID / Biometric)	Multiple attendance capture methods
Grades & Reports	Academic performance tracking
Fees & Payments	Stripe-integrated billing, invoicing, and payment history
Notifications	In-app and email notifications (SMTP + Resend)
Parent Portal	Parent access to student progress and communications
Bulk Enrollment	CSV/bulk student import and enrollment
Teacher Messaging	Secure in-app messaging between teachers and students
Lesson Planner	AI-assisted lesson plan generation
🏆 Achievements & Career
Feature	Description
Achievements System	Badges and milestone tracking for students
Certificates	Auto-generated, shareable PDF certificates
Credential Gallery	Blockchain-verifiable credential display
Career Guidance	AI career path recommendations
LinkedIn Integration	Share credentials and learning achievements to LinkedIn
Student Risk Analysis	Early warning system for at-risk students
⚙️ Platform & Admin
Feature	Description
Super Admin Dashboard	Global platform monitoring and controls
Org Admin Dashboard	Per-school administration
Avatar Settings	Customizable AI avatar personas
Public Content	Public-facing course/content catalog
Study Groups	Collaborative group learning
Virtual Classroom	Zoom-powered live sessions
---
Tech Stack
Backend
Technology	Purpose
Python 3.11+	Core language
FastAPI 0.110	REST API framework
MongoDB + Motor	Async NoSQL database
Uvicorn	ASGI server
JWT (PyJWT)	Authentication
bcrypt + passlib	Password hashing
Google Gemini / Generative AI	AI capabilities
OpenAI	Supplementary LLM
LiteLLM	LLM abstraction layer
ElevenLabs	AI voice synthesis
Zoom SDK	Virtual classroom integration
Stripe	Payment processing
boto3 (AWS S3)	File/media storage
Resend	Transactional email
ReportLab + PyMuPDF	PDF generation and parsing
python-pptx / python-docx	Document processing
Socket.IO	Real-time events
Frontend
Technology	Purpose
React 19	UI framework
React Router DOM 7	Client-side routing
Tailwind CSS 3	Utility-first styling
Radix UI	Accessible headless components
Recharts	Data visualization
React Flow	Knowledge graph visualization
Axios	HTTP client
React Hook Form + Zod	Form validation
Sonner	Toast notifications
React PDF	In-browser PDF viewer
CRACO	CRA configuration override
---
Project Structure
```
cognito-kuwana-gateway-main/
├── backend/
│   ├── main.py                # FastAPI app entry point
│   ├── server.py              # Legacy monolithic router (being migrated)
│   ├── config.py              # Environment configuration
│   ├── database.py            # MongoDB async connection
│   ├── auth.py                # JWT auth, password hashing
│   ├── auth\_utils.py          # Auth helper utilities
│   ├── requirements.txt       # Python dependencies
│   ├── routers/               # Modular API routers (new)
│   │   ├── auth.py
│   │   ├── courses.py
│   │   ├── students.py
│   │   └── dashboard.py
│   ├── services/              # Business logic services
│   │   ├── ai\_service.py
│   │   ├── advanced\_ai.py
│   │   ├── email\_service.py
│   │   ├── multilingual.py
│   │   ├── notification\_service.py
│   │   ├── payment\_service.py
│   │   ├── payment\_platform.py
│   │   ├── linkedin\_service.py
│   │   ├── ktce\_service.py
│   │   ├── research\_digest.py
│   │   └── smtp\_notifications.py
│   ├── models/                # Pydantic data models
│   ├── routes/                # Additional route definitions
│   └── middleware/            # Custom middleware
│
├── frontend/
│   ├── src/
│   │   ├── App.js             # Root component \& routing
│   │   ├── pages/             # 60+ page components
│   │   ├── components/        # Reusable UI components
│   │   ├── context/           # React context providers
│   │   ├── hooks/             # Custom React hooks
│   │   ├── services/          # API client services
│   │   └── lib/               # Utilities and helpers
│   ├── public/
│   ├── package.json
│   ├── tailwind.config.js
│   └── craco.config.js
│
├── course\_uploads/            # Uploaded course material files
├── generated\_audio/           # ElevenLabs-generated voice files
├── generated\_slides/          # AI-generated slide decks
├── generated\_videos/          # AI-generated video content
├── generated\_pdf\_cache/       # Cached PDF generations
├── memory/                    # AI context memory store
├── profile\_photos/            # User profile images
├── source\_uploads/            # Raw source document uploads
├── design\_guidelines.json     # Frontend design system spec
└── tests/                     # Integration and E2E tests
```
---
Getting Started
Prerequisites
Python 3.11+
Node.js 18+ and Yarn 1.22+
MongoDB instance (local or Atlas)
API keys for: Google Gemini, ElevenLabs, Zoom, Stripe (see below)
---
Environment Variables
Create a `.env` file inside the `backend/` directory:
```env
# Database
MONGO\_URL=mongodb://localhost:27017
DB\_NAME=Cognify2026

# JWT
JWT\_SECRET=your-super-secret-jwt-key
JWT\_ALGORITHM=HS256
JWT\_EXPIRATION\_HOURS=24

# CORS (comma-separated origins, or \* for development)
CORS\_ORIGINS=http://localhost:3000

# AI Services
EMERGENT\_LLM\_KEY=your-emergent-llm-api-key

# Voice Synthesis
ELEVENLABS\_API\_KEY=your-elevenlabs-api-key

# Virtual Classroom
ZOOM\_CLIENT\_ID=your-zoom-client-id
ZOOM\_CLIENT\_SECRET=your-zoom-client-secret
ZOOM\_ACCOUNT\_ID=your-zoom-account-id

# Payments (Stripe)
STRIPE\_SECRET\_KEY=your-stripe-secret-key
STRIPE\_PUBLISHABLE\_KEY=your-stripe-publishable-key

# Email
RESEND\_API\_KEY=your-resend-api-key
SMTP\_HOST=smtp.gmail.com
SMTP\_PORT=587
SMTP\_USER=your-email@gmail.com
SMTP\_PASSWORD=your-smtp-password

# AWS S3 (optional, for media storage)
AWS\_ACCESS\_KEY\_ID=your-aws-key
AWS\_SECRET\_ACCESS\_KEY=your-aws-secret
AWS\_S3\_BUCKET=your-bucket-name
AWS\_REGION=us-east-1
```
---
Backend Setup
```bash
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate       # Linux/macOS
venv\\Scripts\\activate          # Windows

# Install dependencies
pip install -r requirements.txt

# Start the development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
The API will be available at `http://localhost:8000`.  
Interactive API docs: `http://localhost:8000/docs`
---
Frontend Setup
```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
yarn install

# Start the development server
yarn start
```
The frontend will be available at `http://localhost:3000`.
---
API Reference
All API endpoints are prefixed with `/api`.
Health Check
```
GET /api/health
```
Authentication
```
POST /api/auth/register        # Register a new user
POST /api/auth/login           # Login and receive JWT
POST /api/auth/forgot-password # Initiate password reset
```
Courses
```
GET    /api/courses            # List courses
POST   /api/courses            # Create a new course
GET    /api/courses/{id}       # Get course details
PUT    /api/courses/{id}       # Update a course
DELETE /api/courses/{id}       # Delete a course
```
Students
```
GET  /api/students             # List students
POST /api/students/enroll      # Enroll a student
GET  /api/students/{id}        # Get student profile
```
Dashboard
```
GET /api/dashboard/stats       # Aggregated dashboard statistics
```
> For the complete list of endpoints (including AI, payments, attendance, credentials, etc.), refer to the auto-generated Swagger docs at `/docs` or `/redoc` when the backend is running.
---
User Roles
Role	Description
`super\_admin`	Global platform administrator
`org\_admin`	School/organization administrator
`teacher`	Instructor with course management access
`student`	Learner with access to enrolled courses and AI tools
`parent`	Parent/guardian with read access to linked student data
---
Supported Languages
The platform supports multilingual content and UI in:
Code	Language
`en`	English
`sn`	Shona
`nd`	Ndebele
`sw`	Swahili
`zu`	Zulu
---
Architecture
```
┌───────────────────────────────────────────────────────┐
│                     React Frontend                    │
│         (React 19 + Tailwind CSS + Radix UI)         │
└───────────────────────┬───────────────────────────────┘
                        │  HTTP / REST
                        ▼
┌───────────────────────────────────────────────────────┐
│                   FastAPI Backend                     │
│    ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│    │  Routers │  │ Services │  │   Middleware      │  │
│    │ auth     │  │ AI/LLM   │  │ JWT Auth          │  │
│    │ courses  │  │ payments │  │ CORS              │  │
│    │ students │  │ email    │  │ Logging           │  │
│    │ dashboard│  │ voice    │  └──────────────────┘  │
│    └──────────┘  └──────────┘                        │
└───────────────────────┬───────────────────────────────┘
                        │
          ┌─────────────┴─────────────┐
          ▼                           ▼
  ┌───────────────┐         ┌─────────────────────┐
  │   MongoDB     │         │  External Services   │
  │  (Motor async)│         │ Google Gemini        │
  └───────────────┘         │ OpenAI / LiteLLM     │
                            │ ElevenLabs           │
                            │ Zoom                 │
                            │ Stripe               │
                            │ AWS S3               │
                            │ Resend (Email)       │
                            └─────────────────────┘
```
Backend Migration Status
The backend is undergoing a modular refactor from a monolithic `server.py`:
Router	Status
`auth`	✅ Migrated
`courses`	✅ Migrated
`students`	✅ Migrated
`dashboard`	✅ Migrated
`organizations`, `knowledge`, `mentor`, `content`	⏳ Legacy (server.py)
`voice`, `fees`, `grades`, `attendance`, `achievements`	⏳ Legacy (server.py)
`notifications`, `parents`, `reports`, `credentials`	⏳ Legacy (server.py)
`rfid`, `messages`, `study\_groups`, `zoom`	⏳ Legacy (server.py)
---
Testing
Backend Tests
```bash
cd backend
pytest tests/ -v
```
AI Role Tests
```bash
python ai\_role\_test.py
```
Backend Integration Tests
```bash
python backend\_test.py
```
Test reports are written to the `test\_reports/` directory. Test state is tracked in `test\_result.md`.
---
Contributing
Fork the repository
Create a feature branch: `git checkout -b feature/your-feature-name`
Make your changes and add tests
Commit your changes: `git commit -m "feat: describe your change"`
Push to your fork: `git push origin feature/your-feature-name`
Open a Pull Request
Code Style
Backend: Follow PEP 8. Formatters: `black`, linter: `flake8`
Frontend: ESLint with React and accessibility plugins
Components: Named exports (`export const Component = ...`)
Pages: Default exports (`export default function Page() {}`)
Toasts: Use `sonner` (not other toast libraries)
---
License
This project is proprietary software. All rights reserved.
---
Cognify 2026 — Empowering Education with AI
