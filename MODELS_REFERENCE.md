# Models Reference

This document provides detailed information about all Django models in the Catopus application.

## Account Models

### LoginCreds

**File:** `account/models.py`  
**Table:** `dwh_system.cat_login_creds`  
**Base Classes:** `AbstractBaseUser`, `PermissionsMixin`

Custom user model that replaces Django's default User model.

#### Fields

| Field | Type | Max Length | Description |
|-------|------|------------|-------------|
| `name` | CharField | 255 | User's display name |
| `username` | CharField | 255 | Primary key, used for authentication |
| `password` | CharField | 255 | Plain text password (for reference) |
| `hashed_password` | CharField | 255 | Hashed password for authentication |
| `last_login` | DateTimeField | - | Timestamp of last login |
| `is_active` | BooleanField | - | Whether the user account is active (default: True) |
| `is_staff` | BooleanField | - | Whether the user has staff privileges (default: False) |

#### Manager

```python
class LoginCredsManager(BaseUserManager):
    def get_by_natural_key(self, username):
        return self.get(username=username)
```

#### Meta Options

```python
class Meta:
    managed = True
    db_table = '"dwh_system"."cat_login_creds"'
```

#### Usage Examples

```python
# Create a new user
user = LoginCreds.objects.create(
    username='john_doe',
    name='John Doe',
    password='plaintext_password',
    hashed_password=make_password('plaintext_password'),
    last_login=timezone.now()
)

# Authenticate user
user = authenticate(username='john_doe', password='plaintext_password')

# Check if user is active
if user.is_active:
    print("User is active")

# Get user by natural key
user = LoginCreds.objects.get_by_natural_key('john_doe')
```

## Search Models

### SearchResult

**File:** `search/models.py`  
**Table:** `dwh_system.cat_search_result`

Stores search query results and associated metadata.

#### Fields

| Field | Type | Max Length | Description |
|-------|------|------------|-------------|
| `identifier` | CharField | 255 | Unique identifier (UUID) for the search result |
| `user` | ForeignKey | - | Reference to LoginCreds user |
| `search_results_file` | FileField | - | Parquet file containing search results |
| `created_at` | DateTimeField | - | Timestamp when search was created (auto) |
| `sql_query` | TextField | - | The SQL query that was executed |
| `countries_list` | CharField | 50 | Name of the country list used |
| `countries` | CharField | 8192 | JSON string of selected countries |

#### Relationships

- **One-to-Many with LoginCreds:** Each user can have multiple search results
- **Cascade Delete:** When a user is deleted, all their search results are deleted

#### Usage Examples

```python
# Create a search result
search_result = SearchResult.objects.create(
    identifier=str(uuid.uuid4()),
    user=request.user,
    sql_query="SELECT * FROM users WHERE country = 'US'",
    countries='["us", "ca", "uk"]',
    countries_list='first priority countries'
)

# Save file to search result
search_result.search_results_file.save(
    f"{search_result.identifier}.parquet.gzip",
    ContentFile(compressed_data)
)

# Query search results for a user
user_results = SearchResult.objects.filter(user=request.user)

# Get search result by identifier
result = SearchResult.objects.get(identifier='some-uuid')

# Order by creation date (newest first)
recent_results = SearchResult.objects.filter(
    user=request.user
).order_by('-created_at')
```

### RemoteLogs

**File:** `search/models.py`  
**Table:** `dwh_system.cat_remote_logs`

Tracks remote query execution status and results.

#### Fields

| Field | Type | Max Length | Description |
|-------|------|------------|-------------|
| `id` | AutoField | - | Primary key |
| `user` | ForeignKey | - | Reference to LoginCreds user |
| `status` | CharField | 10 | Execution status ('start', 'finished', 'error', 'empty') |
| `sql_query` | TextField | - | The SQL query being executed |
| `step` | CharField | 255 | Current execution step (optional) |
| `table_name_created` | CharField | 50 | Name of the table created from results |
| `log_field` | TextField | - | Error messages or additional logging info |
| `countries_list` | CharField | 50 | Name of the country list used |
| `countries` | CharField | 255 | Selected countries |
| `run_on` | DateTimeField | - | When remote execution started (auto) |
| `updated_on` | DateTimeField | - | When status was last updated |

#### Status Values

- `start`: Remote execution has started
- `finished`: Execution completed successfully
- `error`: Execution failed with an error
- `empty`: Query returned no results

#### Usage Examples

```python
# Create a remote log entry
log_entry = RemoteLogs.objects.create(
    user=request.user,
    status='start',
    sql_query="SELECT * FROM products",
    countries='["us", "de", "fr"]',
    countries_list='first priority countries'
)

# Update status to finished
log_entry.status = 'finished'
log_entry.table_name_created = 'user_rmt_20231201_14_30_45'
log_entry.updated_on = timezone.now()
log_entry.save()

# Update status to error
log_entry.status = 'error'
log_entry.log_field = 'Connection timeout to database'
log_entry.updated_on = timezone.now()
log_entry.save()

# Query remote logs for a user
user_logs = RemoteLogs.objects.filter(user=request.user)

# Get logs by status
error_logs = RemoteLogs.objects.filter(status='error')

# Order by run time (newest first)
recent_logs = RemoteLogs.objects.filter(
    user=request.user
).order_by('-run_on')
```

### SavedScripts

**File:** `search/models.py`  
**Table:** `dwh_system.cat2_saved_scripts`

Allows users to save and reuse SQL queries.

#### Fields

| Field | Type | Max Length | Description |
|-------|------|------------|-------------|
| `id` | AutoField | - | Primary key |
| `user` | ForeignKey | - | Reference to LoginCreds user |
| `sql_query` | TextField | - | The saved SQL query |
| `countries_list` | CharField | 50 | Name of the country list used |
| `countries` | CharField | 255 | Selected countries |
| `saved_on` | DateTimeField | - | When script was saved (auto) |
| `updated_on` | DateTimeField | - | When script was last modified |
| `deleted_on` | DateTimeField | - | Soft delete timestamp |

#### Soft Delete

The model supports soft delete functionality through the `deleted_on` field. Records are not physically deleted but marked as deleted.

#### Usage Examples

```python
# Save a script
script = SavedScripts.objects.create(
    user=request.user,
    sql_query="SELECT * FROM users WHERE created_at > '2023-01-01'",
    countries='["us", "ca"]',
    countries_list='first priority countries'
)

# Update a script
script.sql_query = "SELECT * FROM users WHERE created_at > '2023-06-01'"
script.updated_on = timezone.now()
script.save()

# Soft delete a script
script.deleted_on = timezone.now()
script.save()

# Query active (non-deleted) scripts
active_scripts = SavedScripts.objects.filter(
    user=request.user,
    deleted_on__isnull=True
)

# Query all scripts (including deleted)
all_scripts = SavedScripts.objects.filter(user=request.user)

# Order by save date (newest first)
recent_scripts = SavedScripts.objects.filter(
    user=request.user,
    deleted_on__isnull=True
).order_by('-saved_on')
```

## Model Relationships

### User-SearchResult Relationship

```python
# One-to-Many: One user can have many search results
user = LoginCreds.objects.get(username='john_doe')
search_results = user.searchresult_set.all()

# Reverse relationship
search_result = SearchResult.objects.get(identifier='some-uuid')
user = search_result.user
```

### User-RemoteLogs Relationship

```python
# One-to-Many: One user can have many remote logs
user = LoginCreds.objects.get(username='john_doe')
remote_logs = user.remotelogs_set.all()

# Reverse relationship
remote_log = RemoteLogs.objects.get(id=1)
user = remote_log.user
```

### User-SavedScripts Relationship

```python
# One-to-Many: One user can have many saved scripts
user = LoginCreds.objects.get(username='john_doe')
saved_scripts = user.savedscripts_set.all()

# Reverse relationship
saved_script = SavedScripts.objects.get(id=1)
user = saved_script.user
```

## Database Schema

### Table Creation

The models use custom table names and schemas:

```sql
-- LoginCreds table
CREATE TABLE dwh_system.cat_login_creds (
    username VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    last_login TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE
);

-- SearchResult table
CREATE TABLE dwh_system.cat_search_result (
    identifier VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL REFERENCES dwh_system.cat_login_creds(username),
    search_results_file VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sql_query TEXT,
    countries_list VARCHAR(50),
    countries VARCHAR(8192)
);

-- RemoteLogs table
CREATE TABLE dwh_system.cat_remote_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES dwh_system.cat_login_creds(username),
    status VARCHAR(10) NOT NULL,
    sql_query TEXT NOT NULL,
    step VARCHAR(255),
    table_name_created VARCHAR(50),
    log_field TEXT,
    countries_list VARCHAR(50),
    countries VARCHAR(255) NOT NULL,
    run_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_on TIMESTAMP
);

-- SavedScripts table
CREATE TABLE dwh_system.cat2_saved_scripts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES dwh_system.cat_login_creds(username),
    sql_query TEXT NOT NULL,
    countries_list VARCHAR(50),
    countries VARCHAR(255) NOT NULL,
    saved_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_on TIMESTAMP,
    deleted_on TIMESTAMP
);
```

## Model Validation

### Custom Validation

While the models don't include custom validation methods, the application relies on:

1. **Database Constraints:** Foreign key constraints ensure referential integrity
2. **Django Validation:** Built-in field validation (max_length, required fields)
3. **Application Logic:** Custom validation in views and forms

### Field Constraints

- **CharField max_length:** Enforced at database level
- **ForeignKey constraints:** Cascade delete for data integrity
- **Unique constraints:** `identifier` field in SearchResult must be unique
- **Required fields:** Most fields are required unless explicitly set to `null=True`

## Performance Considerations

### Indexing

Consider adding database indexes for frequently queried fields:

```sql
-- Index on user_id for faster filtering
CREATE INDEX idx_search_result_user_id ON dwh_system.cat_search_result(user_id);
CREATE INDEX idx_remote_logs_user_id ON dwh_system.cat_remote_logs(user_id);
CREATE INDEX idx_saved_scripts_user_id ON dwh_system.cat2_saved_scripts(user_id);

-- Index on created_at for ordering
CREATE INDEX idx_search_result_created_at ON dwh_system.cat_search_result(created_at);
CREATE INDEX idx_remote_logs_run_on ON dwh_system.cat_remote_logs(run_on);
CREATE INDEX idx_saved_scripts_saved_on ON dwh_system.cat2_saved_scripts(saved_on);

-- Index on status for filtering
CREATE INDEX idx_remote_logs_status ON dwh_system.cat_remote_logs(status);
```

### Query Optimization

```python
# Use select_related for foreign key access
search_results = SearchResult.objects.select_related('user').filter(
    user=request.user
)

# Use prefetch_related for reverse foreign key access
users = LoginCreds.objects.prefetch_related('searchresult_set').all()

# Use only() to limit fields when possible
search_results = SearchResult.objects.only(
    'identifier', 'created_at', 'sql_query'
).filter(user=request.user)
```

## Migration Management

### Creating Migrations

```bash
# Create migrations for model changes
python manage.py makemigrations account
python manage.py makemigrations search

# Apply migrations
python manage.py migrate
```

### Custom Migration for Data

```python
# Example migration for data transformation
from django.db import migrations

def update_countries_format(apps, schema_editor):
    SearchResult = apps.get_model('search', 'SearchResult')
    for result in SearchResult.objects.all():
        if result.countries and not result.countries.startswith('['):
            # Convert string to JSON format
            countries_list = result.countries.split(',')
            result.countries = json.dumps(countries_list)
            result.save()

class Migration(migrations.Migration):
    dependencies = [
        ('search', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(update_countries_format),
    ]
```

This comprehensive models reference provides detailed information about all database models, their relationships, usage patterns, and best practices for working with them in the Catopus application.