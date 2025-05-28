# AI-Multitool-Analyse

AI-Multitool-Analyse is a web application for analyzing files using artificial intelligence and various utilities. The project allows users to upload files, analyze them (compute hashes, extract strings, inspect PE files, scan with VirusTotal and etc.), and process results with AI models. Built with Django, it leverages Celery for asynchronous tasks, PostgreSQL for data storage, Redis for caching and queues, and Nginx as a reverse proxy.

## Table of Contents

- [Technology Stack](#technology-stack)
- [Setup Instructions](#setup-instructions)
- [Recommendations and Future Development](#recommendations-and-future-development)

## Technology Stack

- **Backend**: Django 4.2+ (web framework)
- **Asynchronous Tasks**: Celery 5.2+ (background task processing, e.g., file analysis)
- **Message Broker and Cache**: Redis 7 (for Celery and caching)
- **Database**: PostgreSQL 15 (storing user and file data)
- **Web Server**: Gunicorn 20.1+ (WSGI server for Django), Nginx (reverse proxy)
- **Containerization**: Docker, Docker Compose
- **AI Analysis**:
  - `google-genai` (Google Generative AI integration)
- **TelegramAPI**: Integration with Telegram bot

## Setup Instructions

### Prerequisites

- Docker and Docker Compose
- A `.env` file with configuration (see example below)

### Steps to Run

1. **Clone the Repository**:

   ```bash
   git clone <repository-url>
   cd ai-multitool-analyse
   ```

2. **Create a `.env` File** in the project root with the following variables (example):

   ```env
   HOST=https://yourhost.com
   
   # Django
   DJANGO_SECRET_KEY=your-secret-key
   DEBUG=True

   # PostgreSQL
   POSTGRES_DB=ai_multitool
   POSTGRES_USER=admin
   POSTGRES_PASSWORD=your-password
   POSTGRES_HOST=postgres
   POSTGRES_PORT=5432

   # Redis
   REDIS_HOST=redis
   REDIS_PORT=6379

   # VirusTotal API
   VT_API_KEY=your-virustotal-api-key

   # Google Generative AI
   GEMENI_API_KEY=your-google-api-key

   #
   TELEGRAM_BOT_TOKEN=your-bot-token
   TELEGRAM_WEBHOOK_URL={HOST}/telegram/webhook/
   ```

   Replace it with actual values.

3. **Run Docker Compose**:

   ```bash
   docker-compose up --build -d
   ```

   This command will:
   - Build images for Django, Celery, and Nginx.
   - Start containers: Django (port 8000), PostgreSQL (port 5432), Redis (port 6379), Celery (worker), Nginx (port 80).
   - Apply database migrations (`python manage.py migrate`).
   - Collect static files (`collectstatic`).

4. **Verify Accessibility**:
   - Open a browser: `http://localhost` (via Nginx on port 80) or `http://localhost:8000` (directly to Django).
   - Ensure the upload page is accessible.

5. **Stop the Project**:

   ```bash
   docker-compose down
   ```

### Accessing Services

- **Web Application**: `http://localhost`
- **Django Admin**: `http://localhost/admin` (create a superuser: `docker-compose exec django python manage.py createsuperuser`)
- **PostgreSQL**: `psql -h localhost -p 5432 -U <POSTGRES_USER> -d <POSTGRES_DB>`
- **Redis**: `redis-cli -h localhost -p 6379`

## Recommendations and Future Development

### Usage

- **File Upload**: Navigate to `/analysis/upload/`, log in, and upload a file. Analysis results (hashes, strings, PE data, VirusTotal, AI analysis) will appear on the dashboard (`/dashboard/`).
- **Asynchronous Analysis**: Celery handles tasks (e.g., VirusTotal scans) in the background. Check status in the `UploadedFile` model (`vt_status`, `ai_status` fields).
- **Logs**: View Django and Celery logs with `docker-compose logs django` and `docker-compose logs celery`.
- **Telegram**: Send "/start" to your @TelegramBot to access the functionality of the application using the bot.

### Warnings

For users from Russia you must use a VPN (for AI utils).

### Security

- Set `DEBUG=False` in `.env` for production.
- Use a secure `DJANGO_SECRET_KEY` and keep `.env` out of version control.
- Configure HTTPS for Nginx in production.

### Enhancements

- **New Analysis Modules**: Support analysis of PDF, APK, or archive files by extending `utils`.
- **AI Models**: Integrate additional models (e.g., Hugging Face Transformers) for local analysis.
- **UI/UX**: Add result visualizations (e.g., charts with Chart.js) or notifications via Django messages.

## License

MIT License.
