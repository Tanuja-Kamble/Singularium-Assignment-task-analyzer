# Smart Task Analyzer

## Overview
A Django-based task management system that intelligently scores and sorts tasks based on multiple factors including urgency, importance, effort, and dependencies. Helps users decide what to work on first.

## Project Structure
```
├── backend/              # Django project configuration
│   ├── settings.py       # Project settings
│   ├── urls.py           # Main URL routing
│   └── wsgi.py           # WSGI entry point
├── tasks/                # Task analyzer app
│   ├── models.py         # Task database model
│   ├── scoring.py        # Priority scoring algorithm
│   ├── views.py          # API endpoints
│   └── urls.py           # App URL routing
├── frontend/             # Static frontend files
│   ├── index.html        # Main HTML page
│   ├── styles.css        # CSS styling
│   └── script.js         # JavaScript logic
├── main.py               # Server entry point
└── requirements.txt      # Python dependencies
```

## How to Run
The application runs automatically via the workflow. It starts a Django development server on port 5000.

To run manually:
```bash
python main.py
```

## API Endpoints

### POST /api/tasks/analyze/
Accepts a list of tasks and returns them sorted by priority score.

**Request Body:**
```json
{
    "tasks": [
        {
            "id": 1,
            "title": "Task name",
            "due_date": "2025-12-01",
            "importance": 8,
            "estimated_hours": 2,
            "dependencies": []
        }
    ],
    "strategy": "smart_balance"
}
```

**Strategies:**
- `smart_balance` - Balanced algorithm considering all factors
- `fastest_wins` - Prioritizes low-effort tasks
- `high_impact` - Prioritizes importance over everything
- `deadline_driven` - Prioritizes based on due date

### GET /api/tasks/suggest/
Returns the top 3 tasks to work on with explanations.

## Algorithm Explanation

The scoring algorithm weighs multiple factors:

1. **Urgency (High Weight)**
   - Overdue tasks: +100 points
   - Due today: +90 points
   - Due tomorrow: +80 points
   - Due within 3 days: +50 points
   - Due within 7 days: +30 points

2. **Importance (Medium-High Weight)**
   - User rating (1-10) multiplied by 5
   - Maximum contribution: 50 points

3. **Effort/Quick Wins (Low-Medium Weight)**
   - Tasks under 2 hours: +15 points
   - Tasks 2-4 hours: +8 points
   - Tasks over 8 hours: -5 points

4. **Dependencies (Medium Weight)**
   - Tasks that block others: +20 points per dependent task

## Edge Case Handling
- **Past due dates**: Treated as highest priority with +100 urgency boost
- **Missing importance**: Defaults to 5/10
- **Missing estimated_hours**: Defaults to 1 hour
- **Invalid data**: Validation warnings are returned with the response
- **Circular dependencies**: Detected and reported as warnings

## Recent Changes
- Initial implementation (November 2025)
- Added multi-strategy sorting (Smart Balance, Fastest Wins, High Impact, Deadline Driven)
- Implemented circular dependency detection
- Added comprehensive edge case handling

## Technology Stack
- **Backend**: Python 3.11, Django 5.2
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Database**: SQLite
