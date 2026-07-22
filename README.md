# Brainiac Proctored Smart Assessment Portal

A full-stack web application for conducting online quizzes with real-time camera proctoring, computer vision violation detection, and an instructor audit dashboard.

## Tech Stack

- **Backend:** Django 4.2 + SQLite
- **Frontend:** HTML5, ES6 JavaScript, Tailwind CSS
- **Computer Vision:** OpenCV Haar Cascades for face detection
- **Proctoring Sync:** HTTP POST snapshots every 2 seconds

## Features

- Student / Instructor role-based authentication
- Quiz CRUD with Multiple Choice & Short Answer questions
- Proctored exam with webcam preview, full-screen mode, countdown timer
- Frontend violation detection (tab switch, window blur)
- Backend CV analysis (no face, multiple faces, head turned away)
- Debounced face violations (2 consecutive bad frames before strike)
- Integrity Score: `max(0, 100 - violations × 15)`
- Auto-disqualification when max warnings exceeded
- Instructor Audit Dashboard with violation snapshot previews

## Quick Start

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed demo data
python manage.py seed_demo

# Start server
python manage.py runserver
```

Open http://127.0.0.1:8000/

### Demo Accounts

| Role       | Username    | Password       |
|------------|-------------|----------------|
| Instructor | instructor  | instructor123  |
| Student    | student     | student123     |

## Project Structure

```
├── accounts/              # User auth (STUDENT / INSTRUCTOR roles)
├── assessments/
│   ├── models.py          # Quiz, Question, QuizAttempt, ViolationLog
│   ├── proctor.py         # OpenCV + MediaPipe CV engine
│   ├── views.py           # Page views + API endpoints
│   └── management/        # seed_demo command
├── static/js/proctor.js   # Frontend proctoring controller
├── templates/             # HTML templates (Tailwind CSS)
└── config/settings.py     # Django settings + proctor config
```

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/assessments/api/attempt/<id>/analyze/` | Send camera frame for CV analysis |
| POST | `/assessments/api/attempt/<id>/violation/` | Log frontend violation |
| POST | `/assessments/api/attempt/<id>/submit/` | Submit quiz answers |
| GET  | `/assessments/api/attempt/<id>/status/` | Poll attempt status |

## Proctoring Configuration

Edit `config/settings.py`:

```python
PROCTOR_FRAME_INTERVAL_MS = 2000   # Frame capture interval
PROCTOR_FACE_DEBOUNCE_CHECKS = 2   # Consecutive bad frames before strike
PROCTOR_INTEGRITY_PENALTY = 15     # Points deducted per violation
```

## License

MIT
