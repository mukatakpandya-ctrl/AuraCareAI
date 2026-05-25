# AuraCare / GlowUp AI — Backend

> AI-powered personal grooming assistant — BCA 6th Semester Project  
> Mohanlal Sukhadia University, Udaipur

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (Python 3.11+) |
| Database | SQLite + SQLAlchemy 2.0 |
| Auth | JWT (python-jose + passlib/bcrypt) |
| AI | Google Gemini 1.5 Flash |
| Weather | OpenWeatherMap API |
| Validation | Pydantic v2 |

---

## Folder Structure

```
glowup-backend/
├── app/
│   ├── main.py              ← FastAPI app, CORS, router registration
│   ├── config.py            ← Pydantic Settings (reads .env)
│   ├── database.py          ← SQLAlchemy engine, session, init_db()
│   ├── models/
│   │   ├── user.py          ← User table
│   │   ├── profile.py       ← UserProfile (questionnaire answers)
│   │   ├── habit.py         ← HabitLog (daily check-ins)
│   │   ├── recommendation.py← AI-generated recommendations
│   │   └── chat.py          ← ChatSession + ChatMessage
│   ├── schemas/
│   │   ├── user.py          ← Register/Login/Token Pydantic models
│   │   ├── profile.py       ← Profile create/update/out
│   │   ├── habit.py         ← HabitLog + HabitSummary
│   │   ├── recommendation.py← Recommendation request/response
│   │   └── chat.py          ← Chat request/session/message
│   ├── routers/
│   │   ├── auth.py          ← POST /api/auth/register, /login, /me
│   │   ├── profile.py       ← GET/POST/PUT /api/profile
│   │   ├── analysis.py      ← POST /api/analysis/skin-image
│   │   ├── weather.py       ← GET /api/weather
│   │   ├── recommendations.py← POST /api/recommendations/routine|products
│   │   ├── habits.py        ← POST/GET /api/habits/checkin|summary|today
│   │   └── chat.py          ← POST /api/chat, GET /api/chat/sessions
│   ├── services/
│   │   ├── gemini_service.py← Image analysis, routine gen, chatbot
│   │   ├── weather_service.py← OpenWeatherMap + AQI + UV
│   │   └── habit_service.py ← Score calculation, streaks, weekly stats
│   └── utils/
│       ├── auth.py          ← JWT encode/decode, get_current_user dep
│       └── helpers.py       ← JSON helpers, file save/delete
├── uploads/                 ← Uploaded selfie images (auto-created)
├── glowup.db               ← SQLite database (auto-created)
├── .env.example            ← Environment variable template
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone & create virtual environment
```bash
git clone <repo>
cd glowup-backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env and fill in your API keys:
#   GEMINI_API_KEY    → https://aistudio.google.com/app/apikey
#   OPENWEATHER_API_KEY → https://openweathermap.org/api
#   SECRET_KEY        → any long random string
```

### 4. Run
```bash
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login → JWT token |
| GET | `/api/auth/me` | Current user info |

### Profile (requires JWT)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/profile` | Submit onboarding questionnaire |
| GET | `/api/profile` | Fetch profile |
| PUT | `/api/profile` | Update profile fields |

### Analysis (requires JWT)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/analysis/skin-image` | Upload selfie → Gemini Vision analysis |

### Weather (requires JWT)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/weather?city=Udaipur` | Current weather + UV + AQI |

### Recommendations (requires JWT)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/recommendations/routine` | Generate AM/PM routine (weather-aware) |
| POST | `/api/recommendations/products` | Get product recommendations |
| GET | `/api/recommendations` | List past recommendations |
| GET | `/api/recommendations/{id}` | Get single recommendation |

### Habit Tracking (requires JWT)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/habits/checkin` | Log today's habits |
| PUT | `/api/habits/{id}` | Update a habit log |
| GET | `/api/habits` | List habit logs |
| GET | `/api/habits/today` | Today's log |
| GET | `/api/habits/summary` | Stats, streaks, weekly chart data |

### Chat — Grooming Coach (requires JWT)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat` | Send message (new or existing session) |
| GET | `/api/chat/sessions` | List all sessions |
| GET | `/api/chat/sessions/{id}` | Get session with full history |
| DELETE | `/api/chat/sessions/{id}` | Delete session |

---

## Habit Score Calculation

Each daily check-in is scored out of 100:

| Habit | Weight |
|---|---|
| Cleansed face | 20 |
| Applied sunscreen | 20 |
| Moisturized | 15 |
| Drank water (met goal) | 15 |
| Washed hair | 10 |
| Slept enough | 10 |
| Exercised | 10 |

The **overall habit score** is the rolling 30-day average of daily scores, stored in the user profile.

---

## Frontend Integration

The React frontend should:
1. Store the JWT token in localStorage / context
2. Send `Authorization: Bearer <token>` on every protected request
3. Use `/uploads/<filename>` to display uploaded images
4. Connect to `ws://localhost:8000` for future WebSocket chat (optional upgrade)

---

## Authors

Pratiksha Kumawat · Priyanshi Jaisinghani · Vanshika Paliwal · Sarvesh Dak · Yash Raj Wadhwani  
Supervisor: Dr. Avinash Pawar
"# AuraCareAI" 
