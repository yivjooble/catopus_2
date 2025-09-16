# Developer Guide

This guide provides comprehensive information for developers working on the Catopus application.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Architecture](#project-architecture)
3. [Code Style and Conventions](#code-style-and-conventions)
4. [Database Management](#database-management)
5. [Testing](#testing)
6. [Debugging](#debugging)
7. [Performance Optimization](#performance-optimization)
8. [Security Considerations](#security-considerations)
9. [Deployment](#deployment)
10. [Contributing](#contributing)

## Development Environment Setup

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Redis server
- Git
- Virtual environment tool (venv, virtualenv, or conda)

### Local Development Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd catopus
```

2. **Create and activate virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Environment configuration:**
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DWH_DB=your-database-name
DWH_USER=your-database-user
DWH_PASSWORD=your-database-password
DWH_HOST=localhost
DWH_PORT=5432
RPL_USER=remote-database-user
RPL_PASSWORD=remote-database-password
```

5. **Database setup:**
```bash
# Create database
createdb your-database-name

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

6. **Start development servers:**
```bash
# Terminal 1: Django development server
python manage.py runserver

# Terminal 2: Redis server
redis-server

# Terminal 3: Celery worker
celery -A catopus worker --loglevel=info
```

### IDE Configuration

#### VS Code

Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.linting.flake8Enabled": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

#### PyCharm

1. Open project in PyCharm
2. Configure Python interpreter to use virtual environment
3. Set up database connection in Database tool window
4. Configure run configurations for Django and Celery

## Project Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Django App    │    │   PostgreSQL    │
│                 │◄──►│                 │◄──►│                 │
│  - HTML/CSS/JS  │    │  - Views        │    │  - User Data    │
│  - AJAX Calls   │    │  - Models       │    │  - Search Results│
└─────────────────┘    │  - Templates    │    │  - Logs         │
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Celery        │
                       │                 │
                       │  - Background   │
                       │    Tasks        │
                       │  - Remote Query │
                       │    Execution    │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Redis         │
                       │                 │
                       │  - Task Queue   │
                       │  - Result Store │
                       └─────────────────┘
```

### Application Structure

```
catopus/
├── account/                 # User authentication
│   ├── models.py           # User model
│   ├── views.py            # Auth views
│   ├── auth_backend.py     # Custom auth backend
│   └── urls.py             # URL patterns
├── search/                 # Core functionality
│   ├── models.py           # Data models
│   ├── views.py            # Business logic
│   ├── tasks.py            # Celery tasks
│   ├── multiprocessing.py  # Query execution
│   ├── config.py           # Database config
│   └── urls.py             # URL patterns
├── catopus/                # Django project
│   ├── settings.py         # Configuration
│   ├── urls.py             # Root URLs
│   └── utils/              # Utilities
└── static/                 # Static files
```

### Data Flow

1. **User Authentication:**
   - User submits credentials
   - Custom auth backend validates
   - Session created and maintained

2. **Query Execution:**
   - User submits SQL query and countries
   - Query executed across multiple databases
   - Results combined and returned
   - Results saved to database and file

3. **Remote Execution:**
   - User requests remote execution
   - Celery task queued
   - Background processes execute query
   - Results saved to database table
   - Status tracked in RemoteLogs

## Code Style and Conventions

### Python Style

Follow PEP 8 with these project-specific conventions:

```python
# Imports order
import os
import sys
from datetime import datetime

import pandas as pd
from django.conf import settings
from django.http import JsonResponse

from .models import SearchResult
from .utils import helper_function

# Class naming
class CustomUserAuthBackend(BaseBackend):
    pass

# Function naming
def execute_sql_query(query, countries):
    pass

# Variable naming
user_id = request.user.id
search_results = SearchResult.objects.filter(user=request.user)

# Constants
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT = 30
```

### Django Conventions

```python
# Model naming
class SearchResult(models.Model):
    class Meta:
        db_table = '"dwh_system"."cat_search_result"'
        ordering = ['-created_at']

# View naming
def index(request):
    """Main search interface view."""
    pass

# URL naming
urlpatterns = [
    path('', views.index, name='index'),
    path('result/<str:identifier>/', views.share_results, name='result'),
]

# Template naming
# templates/search/index.html
# templates/account/pages-login.html
```

### Error Handling

```python
# Use specific exception handling
try:
    search_result = SearchResult.objects.get(identifier=identifier)
except SearchResult.DoesNotExist:
    logger.error(f"SearchResult with identifier {identifier} not found")
    return JsonResponse({'status': 'error', 'message': 'Result not found'}, status=404)
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return JsonResponse({'status': 'error', 'message': 'Internal server error'}, status=500)
```

### Logging

```python
import logging

logger = logging.getLogger('search')

# Use appropriate log levels
logger.debug("Detailed information for debugging")
logger.info("General information about program execution")
logger.warning("Something unexpected happened")
logger.error("A serious error occurred")
logger.critical("A very serious error occurred")

# Include context in log messages
logger.info(f"User {user.username} executed query: {query[:50]}...")
logger.error(f"Failed to execute query for user {user.username}: {str(e)}")
```

## Database Management

### Database Schema

The application uses PostgreSQL with a custom schema (`dwh_system`):

```sql
-- Main tables
dwh_system.cat_login_creds      -- User authentication
dwh_system.cat_search_result    -- Search results
dwh_system.cat_remote_logs      -- Remote execution logs
dwh_system.cat2_saved_scripts   -- Saved SQL scripts

-- Results tables (created dynamically)
catopus.user_rmt_YYYYMMDD_HH_MM_SS
```

### Migrations

```bash
# Create migration
python manage.py makemigrations search

# Apply migration
python manage.py migrate

# Check migration status
python manage.py showmigrations

# Rollback migration
python manage.py migrate search 0001
```

### Database Queries

```python
# Use select_related for foreign keys
search_results = SearchResult.objects.select_related('user').filter(
    user=request.user
)

# Use prefetch_related for reverse foreign keys
users = LoginCreds.objects.prefetch_related('searchresult_set').all()

# Use only() to limit fields
search_results = SearchResult.objects.only(
    'identifier', 'created_at', 'sql_query'
).filter(user=request.user)

# Use values() for specific fields
user_logs = RemoteLogs.objects.filter(user=request.user).values(
    'status', 'sql_query', 'run_on'
)
```

### Database Indexing

Add indexes for frequently queried fields:

```sql
-- User-based queries
CREATE INDEX idx_search_result_user_id ON dwh_system.cat_search_result(user_id);
CREATE INDEX idx_remote_logs_user_id ON dwh_system.cat_remote_logs(user_id);

-- Time-based queries
CREATE INDEX idx_search_result_created_at ON dwh_system.cat_search_result(created_at);
CREATE INDEX idx_remote_logs_run_on ON dwh_system.cat_remote_logs(run_on);

-- Status queries
CREATE INDEX idx_remote_logs_status ON dwh_system.cat_remote_logs(status);
```

## Testing

### Test Structure

```python
# tests/test_views.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

class SearchViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass'
        )
    
    def test_index_requires_login(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/account/login/')
    
    def test_index_with_login(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
```

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test search

# Run specific test
python manage.py test search.tests.test_views.SearchViewTests.test_index_requires_login

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Test Data

```python
# Create test data
def create_test_user():
    return get_user_model().objects.create_user(
        username='testuser',
        name='Test User',
        password='testpass'
    )

def create_test_search_result(user):
    return SearchResult.objects.create(
        identifier='test-uuid',
        user=user,
        sql_query='SELECT 1',
        countries='["us", "ca"]'
    )
```

## Debugging

### Django Debug Toolbar

Add to `INSTALLED_APPS` in development:

```python
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

### Logging Configuration

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'search': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### Debugging Queries

```python
# Enable query logging
from django.db import connection
from django.conf import settings

if settings.DEBUG:
    print(connection.queries)

# Use Django Debug Toolbar
# Install: pip install django-debug-toolbar
# Add to INSTALLED_APPS and MIDDLEWARE
```

### Common Debugging Techniques

```python
# Print debugging
print(f"Debug: user={user}, query={query}")

# Logging
logger.debug(f"Processing query: {query}")

# Django shell
python manage.py shell
>>> from search.models import SearchResult
>>> SearchResult.objects.all()

# Database queries
python manage.py dbshell
```

## Performance Optimization

### Database Optimization

```python
# Use select_related for foreign keys
search_results = SearchResult.objects.select_related('user').all()

# Use prefetch_related for reverse foreign keys
users = LoginCreds.objects.prefetch_related('searchresult_set').all()

# Use only() to limit fields
search_results = SearchResult.objects.only('identifier', 'created_at')

# Use values() for specific fields
user_logs = RemoteLogs.objects.values('status', 'run_on')

# Use exists() for boolean checks
if SearchResult.objects.filter(user=user).exists():
    pass
```

### Caching

```python
# Use Django cache framework
from django.core.cache import cache

# Cache expensive operations
def get_user_search_count(user):
    cache_key = f'user_search_count_{user.id}'
    count = cache.get(cache_key)
    if count is None:
        count = SearchResult.objects.filter(user=user).count()
        cache.set(cache_key, count, 300)  # 5 minutes
    return count
```

### File Handling

```python
# Use streaming for large files
from django.http import StreamingHttpResponse

def stream_large_file(file_path):
    def file_generator():
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                yield chunk
    
    return StreamingHttpResponse(file_generator())
```

### Celery Optimization

```python
# Use appropriate task routing
CELERY_TASK_ROUTES = {
    'search.tasks.run_sql_query_remotely': {'queue': 'remote_queries'},
}

# Use task retry with exponential backoff
@shared_task(bind=True, max_retries=3)
def my_task(self, param):
    try:
        # Task logic
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

## Security Considerations

### Input Validation

```python
# Validate SQL queries (consider using a SQL parser)
def validate_sql_query(query):
    # Basic validation
    if not query.strip():
        raise ValueError("Query cannot be empty")
    
    # Check for dangerous operations
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER']
    query_upper = query.upper()
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            raise ValueError(f"Operation '{keyword}' not allowed")
    
    return True
```

### File Upload Security

```python
# Validate file uploads
def validate_uploaded_file(file):
    # Check file size
    if file.size > 10 * 1024 * 1024:  # 10MB
        raise ValueError("File too large")
    
    # Check file type
    allowed_extensions = ['.parquet']
    if not any(file.name.endswith(ext) for ext in allowed_extensions):
        raise ValueError("Invalid file type")
    
    return True
```

### Authentication Security

```python
# Use secure password hashing
from django.contrib.auth.hashers import make_password, check_password

# Hash password
hashed_password = make_password('plaintext_password')

# Verify password
is_valid = check_password('plaintext_password', hashed_password)
```

### CSRF Protection

```python
# Ensure CSRF protection is enabled
MIDDLEWARE = [
    'django.middleware.csrf.CsrfViewMiddleware',
    # ... other middleware
]

# Use CSRF token in forms
{% csrf_token %}
```

## Deployment

### Production Settings

```python
# settings/production.py
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']

# Use environment variables
SECRET_KEY = os.environ.get('SECRET_KEY')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
    }
}

# Static files
STATIC_ROOT = '/var/www/static/'
MEDIA_ROOT = '/var/www/media/'

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "catopus.wsgi:application", "--bind", "0.0.0.0:8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - SECRET_KEY=your-secret-key
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=catopus
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:6-alpine
  
  celery:
    build: .
    command: celery -A catopus worker --loglevel=info
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

### Environment Variables

```bash
# .env.production
SECRET_KEY=your-production-secret-key
DEBUG=False
DB_NAME=catopus_prod
DB_USER=catopus_user
DB_PASSWORD=secure-password
DB_HOST=localhost
DB_PORT=5432
RPL_USER=remote_user
RPL_PASSWORD=remote-password
```

## Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/new-feature
   ```
3. **Make changes and commit:**
   ```bash
   git add .
   git commit -m "Add new feature"
   ```
4. **Run tests:**
   ```bash
   python manage.py test
   ```
5. **Push and create pull request**

### Code Review Checklist

- [ ] Code follows project style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance impact considered
- [ ] Error handling is appropriate

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

Examples:
```
feat(search): add query validation
fix(auth): resolve login redirect issue
docs(api): update endpoint documentation
```

This developer guide provides comprehensive information for working with the Catopus application. For additional information or specific questions, refer to the source code or contact the development team.