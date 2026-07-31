# Website Uptime Monitor

A full-stack website uptime monitoring and alerting system built with Python and FastAPI.

The application monitors websites at scheduled intervals, records availability and response-time data, tracks historical health checks, and sends email alerts when monitored websites go down.

## Features

* Monitor multiple websites
* Automated scheduled health checks
* Manual website health checks
* HTTP status-code monitoring
* Response-time tracking
* Uptime/down status tracking
* Historical health-check records
* Response-time analytics and charts
* Email alerts for website failures
* Website recovery detection
* Create, edit, and delete monitors
* SQLite database
* Alembic database migrations
* Automated test suite
* Dashboard with monitoring statistics

## Tech Stack

**Backend**

* Python 3.12
* FastAPI
* SQLAlchemy
* Alembic
* APScheduler

**Frontend**

* HTML
* Jinja2
* Bootstrap
* Chart.js

**Database**

* SQLite

**Testing**

* Pytest

**Notifications**

* SMTP / Gmail

## Project Structure

```text
uptime-monitor/
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── services/
│   └── templates/
├── alembic/
├── tests/
├── .env
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

## Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd uptime-monitor
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

**Windows:**

```bash
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
DEBUG=True
DATABASE_URL=sqlite:///./uptime_monitor.db

SECRET_KEY=your_secret_key

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
```

> Never commit `.env` or SMTP credentials to GitHub.

For Gmail, use a Google App Password rather than your normal Gmail password.

### 6. Run database migrations

```bash
alembic upgrade head
```

### 7. Start the application

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Running Tests

Run the automated test suite with:

```bash
python -m pytest -v
```

Current test status:

**8 tests passed**

## How It Works

1. A user adds a website to monitor.
2. The scheduler periodically checks the website.
3. The application records availability, HTTP status, response time, timestamp, and error information.
4. Historical monitoring data is displayed through the dashboard.
5. When a monitored website goes down, an email alert is sent.
6. When the website becomes available again, its recovery is recorded.

## Email Alerts

The application uses Gmail SMTP to send monitoring alerts.

Alert information includes:

* Website name
* Website URL
* Current status
* Expected HTTP status
* Observed HTTP status
* Response time
* Error information when available

The email alert flow has been manually verified using a deliberately unreachable website.

## Testing

The project contains automated tests covering monitor validation and core application routes.

The complete failure-alert flow was also manually verified:

```text
Website failure
      ↓
Health check detects DOWN
      ↓
Alert logic triggered
      ↓
Gmail SMTP authentication
      ↓
Email delivered successfully
```

## Security

Sensitive configuration is stored in `.env` and excluded from version control.

Do not commit:

* SMTP passwords
* Gmail App Passwords
* Secret keys
* Other private environment variables

## License

This project is available for educational and portfolio purposes.
