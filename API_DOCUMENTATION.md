# Catopus API Documentation

## Overview

Catopus is a Django-based web application that provides SQL query execution capabilities across multiple country databases. The system allows users to execute SQL queries against various country-specific databases, save results, and manage their query history.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Authentication System](#authentication-system)
3. [Models](#models)
4. [API Endpoints](#api-endpoints)
5. [Utility Functions](#utility-functions)
6. [Background Tasks](#background-tasks)
7. [Configuration](#configuration)
8. [Usage Examples](#usage-examples)
9. [Installation & Setup](#installation--setup)

## Project Structure

```
catopus/
├── account/                 # User authentication and management
│   ├── models.py           # User model definitions
│   ├── views.py            # Authentication views
│   ├── auth_backend.py     # Custom authentication backend
│   └── urls.py             # Account URL patterns
├── search/                 # Core search functionality
│   ├── models.py           # Search result models
│   ├── views.py            # Search and result views
│   ├── tasks.py            # Celery background tasks
│   ├── multiprocessing.py  # Query execution utilities
│   ├── config.py           # Database connection configuration
│   └── urls.py             # Search URL patterns
├── catopus/                # Django project settings
│   ├── settings.py         # Main configuration
│   └── utils/              # Utility functions
└── static/                 # Static files
```

## Authentication System

### Custom User Model

The application uses a custom user model `LoginCreds` instead of Django's default User model.

#### LoginCreds Model

**Location:** `account/models.py`

```python
class LoginCreds(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, primary_key=True)
    password = models.CharField(max_length=255)
    hashed_password = models.CharField(max_length=255)
    last_login = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
```

**Fields:**
- `name`: User's display name
- `username`: Primary key, used for authentication
- `password`: Plain text password (for reference)
- `hashed_password`: Hashed password for authentication
- `last_login`: Timestamp of last login
- `is_active`: Whether the user account is active
- `is_staff`: Whether the user has staff privileges

### Custom Authentication Backend

**Location:** `account/auth_backend.py`

```python
class CustomUserAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Authenticates user using hashed password
    def get_user(self, user_id):
        # Retrieves user by ID
```

**Usage:**
- Handles authentication for the custom `LoginCreds` model
- Uses Django's `check_password` to verify hashed passwords
- Configured in `settings.py` as the primary authentication backend

## Models

### SearchResult Model

**Location:** `search/models.py`

```python
class SearchResult(models.Model):
    identifier = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(LoginCreds, on_delete=models.CASCADE)
    search_results_file = models.FileField(upload_to='search_results/')
    created_at = models.DateTimeField(auto_now_add=True)
    sql_query = models.TextField(null=True)
    countries_list = models.CharField(max_length=50, null=True)
    countries = models.CharField(max_length=8192, null=True)
```

**Purpose:** Stores search query results and metadata

**Fields:**
- `identifier`: Unique identifier for the search result (UUID)
- `user`: Foreign key to the user who created the search
- `search_results_file`: File containing the search results (Parquet format)
- `created_at`: Timestamp when the search was created
- `sql_query`: The SQL query that was executed
- `countries_list`: Comma-separated list of country codes
- `countries`: JSON string of selected countries

### RemoteLogs Model

**Location:** `search/models.py`

```python
class RemoteLogs(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(LoginCreds, on_delete=models.CASCADE)
    status = models.CharField(max_length=10)
    sql_query = models.TextField()
    step = models.CharField(max_length=255, null=True)
    table_name_created = models.CharField(max_length=50, null=True)
    log_field = models.TextField(null=True)
    countries_list = models.CharField(max_length=50, null=True)
    countries = models.CharField(max_length=255)
    run_on = models.DateTimeField(auto_now=True)
    updated_on = models.DateTimeField(null=True)
```

**Purpose:** Tracks remote query execution status and results

**Fields:**
- `status`: Execution status ('start', 'finished', 'error', 'empty')
- `sql_query`: The SQL query being executed
- `table_name_created`: Name of the table created from results
- `log_field`: Error messages or additional logging information
- `run_on`: When the remote execution started
- `updated_on`: When the status was last updated

### SavedScripts Model

**Location:** `search/models.py`

```python
class SavedScripts(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(LoginCreds, on_delete=models.CASCADE)
    sql_query = models.TextField()
    countries_list = models.CharField(max_length=50, null=True)
    countries = models.CharField(max_length=255)
    saved_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(null=True)
    deleted_on = models.DateTimeField(null=True)
```

**Purpose:** Allows users to save and reuse SQL queries

**Fields:**
- `sql_query`: The saved SQL query
- `countries`: Associated country codes
- `saved_on`: When the script was saved
- `updated_on`: When the script was last modified
- `deleted_on`: Soft delete timestamp

## API Endpoints

### Authentication Endpoints

#### Login
- **URL:** `/account/login/`
- **Method:** GET, POST
- **View:** `login_view`
- **Description:** User authentication

**GET Request:**
- Returns login form

**POST Request:**
- **Parameters:**
  - `username`: User's username
  - `password`: User's password
- **Response:** Redirects to search page on success, error message on failure

#### Logout
- **URL:** `/account/logout/`
- **Method:** POST
- **View:** `LogoutView` (Django built-in)
- **Description:** User logout

#### User Profile
- **URL:** `/account/user-profile/`
- **Method:** GET
- **View:** `user_profile`
- **Authentication:** Required
- **Description:** Display user profile page

#### User Registration
- **URL:** `/account/user-register/`
- **Method:** GET
- **View:** `user_register`
- **Authentication:** Required
- **Description:** Display user registration page

### Search Endpoints

#### Main Search Interface
- **URL:** `/`
- **Method:** GET, POST
- **View:** `index`
- **Authentication:** Required
- **Description:** Main search interface and query execution

**GET Request:**
- Returns search form

**POST Request:**
- **Parameters:**
  - `query`: SQL query to execute
  - `list_of_countries`: Comma-separated country codes
  - `selected_countries`: Array of selected countries
  - `is_remote`: Set to 'remote_start' for remote execution
  - `action`: Set to 'save_table' to save results as table
  - `identifier`: Search result identifier (for save_table action)
  - `table_name`: Custom table name (for save_table action)

**Response:**
- **Success:** JSON with table HTML and metadata
- **Error:** JSON with error message

#### Share Search Results
- **URL:** `/result/<str:identifier>/`
- **Method:** GET
- **View:** `share_results`
- **Authentication:** Required
- **Description:** Share and view specific search results

**Parameters:**
- `identifier`: Unique identifier of the search result

**Response:** Rendered HTML page with search results

#### Search History
- **URL:** `/history/`
- **Method:** GET
- **View:** `history`
- **Authentication:** Required
- **Description:** View user's search history

**Response:** HTML page with search history table

#### Remote Execution Logs
- **URL:** `/remote/`
- **Method:** GET
- **View:** `remote`
- **Authentication:** Required
- **Description:** View remote execution logs

**Response:** HTML page with remote execution status

#### Saved Scripts
- **URL:** `/saved_scripts/`
- **Method:** GET, POST
- **View:** `saved_scripts`
- **Authentication:** Required
- **Description:** Manage saved SQL scripts

**GET Request:**
- Returns list of saved scripts

**POST Request:**
- **Parameters:**
  - `sql_query`: SQL query to save
  - `countries_list`: Country list name
  - `selected_countries`: Array of selected countries
- **Response:** Redirects to saved scripts page

#### Python ETL
- **URL:** `/python_etl/`
- **Method:** GET
- **View:** `python_etl`
- **Authentication:** Required
- **Description:** Python ETL interface

## Utility Functions

### Database Utilities

**Location:** `catopus/utils/database.py`

#### create_db_psycopg2_connection
```python
def create_db_psycopg2_connection(host, dbname, user, password):
    """Create a psycopg2 database connection"""
    return psycopg2.connect(
        f"host={host} dbname={dbname} user={user} password={password}")
```

**Parameters:**
- `host`: Database host
- `dbname`: Database name
- `user`: Database username
- `password`: Database password

**Returns:** psycopg2 connection object

#### create_db_sqlalchemy_engine
```python
def create_db_sqlalchemy_engine(host, dbname, user, password):
    """Create a SQLAlchemy database engine with connection pooling"""
    return create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}/{dbname}",
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10)
```

**Parameters:**
- `host`: Database host
- `dbname`: Database name
- `user`: Database username
- `password`: Database password

**Returns:** SQLAlchemy engine with connection pooling

### Query Execution Utilities

**Location:** `search/multiprocessing.py`

#### run_select
```python
def run_select(code: str, countries: List[str], customer_table_name: str = None) -> pd.DataFrame:
    """Execute SQL query across multiple country databases"""
```

**Parameters:**
- `code`: SQL query to execute
- `countries`: List of country codes to query
- `customer_table_name`: Optional custom table name for saving results

**Returns:** 
- `pd.DataFrame`: Query results
- `tuple`: (DataFrame, table_name) if customer_table_name provided

**Features:**
- Parallel execution across multiple databases
- Thread pool with 8 workers
- Error handling for missing tables
- Automatic country code and ID addition to results

#### exec_sql_multiproc
```python
def exec_sql_multiproc(info: Dict[str, str]):
    """Execute SQL query on a single database"""
```

**Parameters:**
- `info`: Dictionary containing connection info and query
  - `host`: Database host
  - `port`: Database port
  - `db_name`: Database name
  - `code`: SQL query

**Returns:** `pd.DataFrame` with query results and country metadata

### Search View Utilities

**Location:** `search/views.py`

#### save_table_to_db
```python
def save_table_to_db(result_df, table_name: str):
    """Save DataFrame to database as a table"""
```

**Parameters:**
- `result_df`: pandas DataFrame to save
- `table_name`: Base name for the table

**Returns:** `str`: Generated table name with timestamp

**Features:**
- Saves to 'catopus' schema
- Adds timestamp to table name
- Uses chunked insertion for large datasets

## Background Tasks

### Celery Tasks

**Location:** `search/tasks.py`

#### run_sql_query_remotely
```python
@shared_task
def run_sql_query_remotely(rmt_user, rmt_input_code, rmt_countries, rmt_countries_list=None):
    """Execute SQL query remotely across multiple databases"""
```

**Parameters:**
- `rmt_user`: User object
- `rmt_input_code`: SQL query to execute
- `rmt_countries`: List of country codes
- `rmt_countries_list`: Optional country list name

**Process:**
1. Creates RemoteLogs entry with 'start' status
2. Spawns multiple processes for parallel execution
3. Executes query on each country database
4. Combines results into single DataFrame
5. Saves results to database table
6. Updates RemoteLogs with 'finished' status

**Error Handling:**
- Catches exceptions and updates status to 'error'
- Logs error details in log_field
- Updates timestamp on status changes

#### exec_sql_remote
```python
def exec_sql_remote(query, results_list):
    """Execute SQL query on remote database (worker function)"""
```

**Parameters:**
- `query`: Queue containing query information
- `results_list`: Manager list to store results

**Process:**
1. Retrieves query from queue
2. Executes SQL query on remote database
3. Adds country metadata to results
4. Appends results to shared list

## Configuration

### Database Configuration

**Location:** `search/config.py`

#### connection_info
Dictionary containing database connection information for different clusters:

```python
connection_info = {
    'nl': {
        'host': '10.0.1.65',
        'port': 5432,
        'dbs': ['pl', 'at', 'es', 'it', ...]  # Country codes
    },
    'us': {
        'host': '192.168.1.207',
        'port': 5432,
        'dbs': ['cl', 'id', 'mx', 'nz', ...]  # Country codes
    }
}
```

#### Country Mappings
- `map_country_code_to_id`: Maps 2-letter country codes to numeric IDs
- `map_full_country_code_to_id`: Maps full country names to numeric IDs
- `countries_lists`: Predefined country groups for easy selection

### Django Settings

**Location:** `catopus/settings.py`

#### Key Configuration:
- **Database:** PostgreSQL with custom schema
- **Authentication:** Custom user model and backend
- **Static Files:** WhiteNoise for serving static files
- **Celery:** Redis as broker and result backend
- **Logging:** File and console logging with custom formatters
- **Media Files:** Local filesystem storage for search results

## Usage Examples

### Basic Query Execution

```python
# Execute a simple query
from search.multiprocessing import run_select

# Query all users from specific countries
query = "SELECT * FROM users LIMIT 100"
countries = ['us', 'ca', 'uk']
results = run_select(query, countries)
print(results.head())
```

### Remote Query Execution

```python
# Execute query remotely using Celery
from search.tasks import run_sql_query_remotely

# Start remote execution
task = run_sql_query_remotely.delay(
    user=request.user,
    rmt_input_code="SELECT * FROM products WHERE category = 'electronics'",
    rmt_countries=['us', 'de', 'fr'],
    rmt_countries_list='first priority countries'
)
```

### Saving Results to Database

```python
# Save query results as a database table
from search.views import save_table_to_db

# Assuming you have a DataFrame from query results
table_name = save_table_to_db(results_df, "my_analysis")
print(f"Results saved to table: {table_name}")
```

### Custom Authentication

```python
# Authenticate user with custom backend
from django.contrib.auth import authenticate
from account.auth_backend import CustomUserAuthBackend

user = authenticate(
    request=request,
    username='myuser',
    password='mypassword'
)
if user:
    print(f"User {user.username} authenticated successfully")
```

## Installation & Setup

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis server
- Virtual environment (recommended)

### Installation Steps

1. **Clone the repository:**
```bash
git clone <repository-url>
cd catopus
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration:**
Create a `.env` file with the following variables:
```env
SECRET_KEY=your-secret-key
DWH_DB=your-database-name
DWH_USER=your-database-user
DWH_PASSWORD=your-database-password
DWH_HOST=your-database-host
DWH_PORT=5432
RPL_USER=remote-database-user
RPL_PASSWORD=remote-database-password
```

5. **Database Setup:**
```bash
python manage.py migrate
python manage.py createsuperuser
```

6. **Start Redis server:**
```bash
redis-server
```

7. **Start Celery worker:**
```bash
celery -A catopus worker --loglevel=info
```

8. **Start Django development server:**
```bash
python manage.py runserver
```

### Production Deployment

1. **Static Files:**
```bash
python manage.py collectstatic
```

2. **WSGI Server:**
```bash
gunicorn catopus.wsgi:application
```

3. **Environment Variables:**
Set production environment variables for database credentials and security settings.

### Docker Deployment

The project includes Docker configuration:

```bash
# Build and run with Docker Compose
docker-compose up --build
```

This will start the Django application, PostgreSQL database, and Redis server in containers.

## Error Handling

The application includes comprehensive error handling:

- **Database Errors:** Caught and logged with appropriate user messages
- **Authentication Errors:** Handled with redirect to login page
- **Query Execution Errors:** Logged and returned as JSON responses
- **File Upload Errors:** Validated and handled gracefully
- **Remote Execution Errors:** Tracked in RemoteLogs model

## Logging

The application uses Django's logging framework with:

- **File Logging:** All logs written to `logs/debug.log`
- **Console Logging:** Real-time log output
- **Module-specific Loggers:** Separate loggers for 'search' and 'account' modules
- **Structured Formatting:** Timestamp, module, and message information

## Security Considerations

- **Password Hashing:** Uses Django's built-in password hashing
- **CSRF Protection:** Enabled for all forms
- **SQL Injection Prevention:** Uses parameterized queries
- **File Upload Security:** Validates file types and sizes
- **Authentication Required:** All views require user authentication

## Performance Optimization

- **Connection Pooling:** SQLAlchemy connection pooling for database connections
- **Parallel Processing:** Thread pool for concurrent query execution
- **File Compression:** Parquet files with gzip compression
- **Chunked Database Inserts:** Large datasets inserted in chunks
- **Caching:** Redis for Celery task results

## Troubleshooting

### Common Issues

1. **Database Connection Errors:**
   - Check database credentials in `.env` file
   - Ensure PostgreSQL is running and accessible
   - Verify database schema exists

2. **Celery Task Errors:**
   - Ensure Redis server is running
   - Check Celery worker is started
   - Verify task queue configuration

3. **File Upload Issues:**
   - Check `MEDIA_ROOT` directory permissions
   - Ensure sufficient disk space
   - Verify file format compatibility

4. **Authentication Issues:**
   - Check custom authentication backend configuration
   - Verify user model settings
   - Ensure password hashing is working correctly

### Debug Mode

Enable debug mode in `settings.py` for development:
```python
DEBUG = True
```

This provides detailed error messages and stack traces for troubleshooting.

---

*This documentation covers the main APIs, functions, and components of the Catopus application. For additional information or specific use cases, please refer to the source code or contact the development team.*