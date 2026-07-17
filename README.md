# AI-Powered Clinical Report Analysis & Nursing Assistance Platform

Production-ready Flask REST API backend for clinical report analysis, nursing education, simulations, quizzes, and progress tracking.

## Tech Stack

- Python 3.13
- Flask + Blueprint architecture (MVC)
- Flask-SQLAlchemy + MySQL
- Flask-JWT-Extended (access + refresh tokens)
- Flask-CORS
- OpenAI API (report analysis & simulation feedback)
- OCR (pytesseract) + PDF text extraction (pypdf)

## Project Structure

```
flask-student-api/
├── app/
│   ├── __init__.py          # App factory
│   ├── config.py            # Environment configuration
│   ├── constants.py         # Roles, notification types, etc.
│   ├── extensions.py        # db, jwt
│   ├── middleware.py        # Role-based access decorator
│   ├── utils.py             # File upload helpers
│   ├── helpers/
│   │   └── response.py      # Standard {status, message, data} responses
│   ├── models/              # SQLAlchemy models
│   ├── controllers/         # Request handlers (thin layer)
│   ├── services/            # Business logic
│   ├── validations/         # Input validation
│   ├── routes/              # Blueprint route definitions
│   └── seeders/             # Demo data
├── uploads/                 # Report & certificate files
├── run.py
├── run_seeders.py
├── requirements.txt
└── .env.example
```

## Setup

```bash
# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux

# 4. Create MySQL database
mysql -u root -p -e "CREATE DATABASE clinical_platform_db;"

# 5. Run migrations (creates tables) + optional seed data
python run.py
python run_seeders.py
```

### OCR (optional)

For image report OCR, install [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) on your system.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_USER` | MySQL username | `root` |
| `DB_PASSWORD` | MySQL password | — |
| `DB_HOST` | MySQL host | `localhost` |
| `DB_NAME` | Database name | `clinical_platform_db` |
| `JWT_SECRET_KEY` | JWT signing key | — |
| `OPENAI_API_KEY` | OpenAI API key | — (uses demo mock if empty) |
| `FRONTEND_URL` | Frontend URL for password reset | `http://localhost:3000` |

## API Response Format

Every endpoint returns:

```json
{
  "status": "success | error",
  "message": "Human-readable message",
  "data": { }
}
```

## Authentication

Protected routes require header:

```
Authorization: Bearer <access_token>
```

### Roles

- `admin` — Full access
- `doctor` — Create courses, cases, quizzes, simulations
- `nurse` — Clinical user
- `medical_student` — Default registration role

### Demo Accounts (after seeding)

| Email | Password | Role |
|-------|----------|------|
| admin@clinical.com | admin123 | admin |
| doctor@clinical.com | doctor123 | doctor |
| nurse@clinical.com | nurse123 | nurse |
| student@clinical.com | student123 | medical_student |

## API Endpoints

Base URL: `http://localhost:5000`

### Auth — `/api/auth`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | No | Register user |
| POST | `/login` | No | Login, get tokens |
| POST | `/refresh` | Refresh token | Refresh access token |
| POST | `/forgot-password` | No | Request password reset |
| POST | `/reset-password` | No | Reset password with token |
| GET/PUT | `/profile` | Yes | View/update profile |
| POST | `/logout` | Yes | Logout (client-side token discard) |

### Reports — `/api/reports`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload/pdf` | Upload PDF report (multipart) |
| POST | `/upload/image` | Upload image report (multipart) |
| POST | `/` | Save report metadata |
| GET | `/` | List user reports |
| GET | `/history` | Report history |
| GET | `/<id>` | Get report |
| POST | `/<id>/extract` | Extract text (OCR/PDF) |
| DELETE | `/<id>` | Delete report |

### AI Analysis — `/api/analysis`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Analyze report text via OpenAI |
| GET | `/` | Analysis history |
| GET | `/<id>` | Get analysis |
| DELETE | `/<id>` | Delete analysis |

### Learning — `/api/learning`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/courses` | List courses |
| GET | `/courses/<id>` | Course with lessons |
| POST | `/courses` | Create course (admin/doctor) |
| PUT/DELETE | `/courses/<id>` | Update/delete course |
| GET | `/courses/<id>/lessons` | List lessons |
| POST | `/lessons` | Create lesson |
| POST | `/lessons/<id>/complete` | Mark lesson complete |
| GET | `/bookmarks` | List bookmarks |
| POST/DELETE | `/lessons/<id>/bookmark` | Add/remove bookmark |
| GET | `/recommendations` | Personalized recommendations |
| GET | `/weak-topics` | Weak topic detection |

### Clinical Cases — `/api/clinical-cases`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List/search/filter cases |
| GET | `/<id>` | Get case |
| POST | `/` | Create case (admin/doctor) |
| PUT/DELETE | `/<id>` | Update/delete case |
| POST/DELETE | `/<id>/favorite` | Favorite/unfavorite |

### Simulations — `/api/simulations`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List scenarios |
| GET | `/<id>` | Get scenario |
| POST | `/<id>/submit` | Submit diagnosis & treatment |
| GET | `/history` | Attempt history |

### Quizzes — `/api/quizzes`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List quizzes |
| GET | `/<id>` | Quiz with questions |
| POST | `/<id>/submit` | Submit answers |
| GET | `/results` | My results |
| GET | `/leaderboard` | Leaderboard |

### Progress — `/api/progress`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Learning progress |
| GET | `/dashboard` | Dashboard analytics |
| GET | `/achievements` | Achievements |

### Certificates — `/api/certificates`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate` | Generate PDF certificate |
| GET | `/` | List certificates |
| GET | `/<id>/download` | Download PDF |

### Discussions — `/api/discussions`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/` | List/create discussions |
| GET/PUT/DELETE | `/<id>` | CRUD discussion |
| POST | `/<id>/comments` | Add comment/reply |
| POST | `/<id>/like` | Like discussion |

### Notifications — `/api/notifications`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List notifications |
| PUT | `/<id>/read` | Mark as read |
| POST | `/learning-reminder` | Create learning reminder |
| POST | `/quiz-reminder` | Create quiz reminder |

## Example Requests

### Register

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret123","full_name":"Jane Doe","role":"medical_student"}'
```

### Login

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@clinical.com","password":"student123"}'
```

### Analyze Report

```bash
curl -X POST http://localhost:5000/api/analysis \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"report_text":"Hemoglobin: 10.2 g/dL (low). WBC: 12,000."}'
```

## Production Deployment

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "run:app"
```

Use the included `Procfile` for Heroku/Railway-style deployments.

## License

MIT
