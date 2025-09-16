# API Endpoints Reference

This document provides detailed information about all API endpoints in the Catopus application.

## Base URL

All endpoints are relative to the application's base URL. In development, this is typically `http://localhost:8000`.

## Authentication

Most endpoints require user authentication. Unauthenticated users will be redirected to the login page.

**Authentication Method:** Session-based authentication with custom user model

## Account Endpoints

### Login

**Endpoint:** `POST /account/login/`  
**View:** `account.views.login_view`  
**Authentication:** Not required

#### Request

**Content-Type:** `application/x-www-form-urlencoded`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username` | string | Yes | User's username |
| `password` | string | Yes | User's password |

#### Response

**Success (200):**
- Redirects to `/` (search page)

**Error (200):**
- Returns HTML with error message: "Invalid credentials"

#### Example

```bash
curl -X POST http://localhost:8000/account/login/ \
  -d "username=john_doe&password=secret123"
```

### Logout

**Endpoint:** `POST /account/logout/`  
**View:** `django.contrib.auth.views.LogoutView`  
**Authentication:** Required

#### Request

No parameters required.

#### Response

**Success (302):**
- Redirects to `/account/login/`

#### Example

```bash
curl -X POST http://localhost:8000/account/logout/ \
  -H "Cookie: sessionid=your_session_id"
```

### User Profile

**Endpoint:** `GET /account/user-profile/`  
**View:** `account.views.user_profile`  
**Authentication:** Required

#### Request

No parameters required.

#### Response

**Success (200):**
- Returns HTML page with user profile information

#### Example

```bash
curl -X GET http://localhost:8000/account/user-profile/ \
  -H "Cookie: sessionid=your_session_id"
```

### User Registration

**Endpoint:** `GET /account/user-register/`  
**View:** `account.views.user_register`  
**Authentication:** Required

#### Request

No parameters required.

#### Response

**Success (200):**
- Returns HTML page with user registration form

#### Example

```bash
curl -X GET http://localhost:8000/account/user-register/ \
  -H "Cookie: sessionid=your_session_id"
```

## Search Endpoints

### Main Search Interface

**Endpoint:** `GET /`  
**View:** `search.views.index`  
**Authentication:** Required

#### Request

No parameters required.

#### Response

**Success (200):**
- Returns HTML page with search form

#### Example

```bash
curl -X GET http://localhost:8000/ \
  -H "Cookie: sessionid=your_session_id"
```

### Execute Query

**Endpoint:** `POST /`  
**View:** `search.views.index`  
**Authentication:** Required

#### Request

**Content-Type:** `application/x-www-form-urlencoded`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | SQL query to execute |
| `list_of_countries` | string | No | Comma-separated country codes |
| `selected_countries` | array | No | Array of selected countries |

#### Response

**Success (200):**
```json
{
  "table_html": "<table>...</table>",
  "identifier": "uuid-string",
  "table_name": "optional_table_name",
  "status": "success"
}
```

**Error (400):**
```json
{
  "status": "error",
  "message": "Query is required."
}
```

**Error (500):**
```json
{
  "status": "error",
  "message": "An unexpected error occurred. Please try again."
}
```

#### Example

```bash
curl -X POST http://localhost:8000/ \
  -H "Cookie: sessionid=your_session_id" \
  -d "query=SELECT * FROM users LIMIT 10&selected_countries[]=us&selected_countries[]=ca"
```

### Remote Query Execution

**Endpoint:** `POST /`  
**View:** `search.views.index`  
**Authentication:** Required

#### Request

**Content-Type:** `application/x-www-form-urlencoded`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | SQL query to execute |
| `selected_countries` | array | Yes | Array of selected countries |
| `list_of_countries` | string | No | Country list name |
| `is_remote` | string | Yes | Must be 'remote_start' |

#### Response

**Success (200):**
```json
{
  "status": "processing",
  "message": "Remote execution started."
}
```

**Error (400):**
```json
{
  "status": "error",
  "message": "Query and countries are required for remote execution."
}
```

#### Example

```bash
curl -X POST http://localhost:8000/ \
  -H "Cookie: sessionid=your_session_id" \
  -d "query=SELECT * FROM products&selected_countries[]=us&selected_countries[]=de&is_remote=remote_start"
```

### Save Table

**Endpoint:** `POST /`  
**View:** `search.views.index`  
**Authentication:** Required

#### Request

**Content-Type:** `application/x-www-form-urlencoded`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | string | Yes | Must be 'save_table' |
| `identifier` | string | Yes | Search result identifier |
| `table_name` | string | Yes | Custom table name |

#### Response

**Success (200):**
```json
{
  "post_factum_table": "table_name_20231201_14_30_45",
  "status": "success"
}
```

**Error (400):**
```json
{
  "status": "error",
  "message": "Missing identifier or table name."
}
```

**Error (404):**
```json
{
  "status": "error",
  "message": "Invalid identifier or unauthorized."
}
```

**Error (500):**
```json
{
  "status": "error",
  "message": "An error occurred: [error details]"
}
```

#### Example

```bash
curl -X POST http://localhost:8000/ \
  -H "Cookie: sessionid=your_session_id" \
  -d "action=save_table&identifier=uuid-string&table_name=my_analysis"
```

### Share Search Results

**Endpoint:** `GET /result/<str:identifier>/`  
**View:** `search.views.share_results`  
**Authentication:** Required

#### Request

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `identifier` | string | Yes | Search result identifier (URL path) |

#### Response

**Success (200):**
- Returns HTML page with search results

**Error (404):**
- Returns 404 error if search result not found

#### Example

```bash
curl -X GET http://localhost:8000/result/uuid-string/ \
  -H "Cookie: sessionid=your_session_id"
```

### Search History

**Endpoint:** `GET /history/`  
**View:** `search.views.history`  
**Authentication:** Required

#### Request

No parameters required.

#### Response

**Success (200):**
- Returns HTML page with search history table

#### Example

```bash
curl -X GET http://localhost:8000/history/ \
  -H "Cookie: sessionid=your_session_id"
```

### Remote Execution Logs

**Endpoint:** `GET /remote/`  
**View:** `search.views.remote`  
**Authentication:** Required

#### Request

No parameters required.

#### Response

**Success (200):**
- Returns HTML page with remote execution logs

#### Example

```bash
curl -X GET http://localhost:8000/remote/ \
  -H "Cookie: sessionid=your_session_id"
```

### Saved Scripts

**Endpoint:** `GET /saved_scripts/`  
**View:** `search.views.saved_scripts`  
**Authentication:** Required

#### Request

No parameters required.

#### Response

**Success (200):**
- Returns HTML page with saved scripts list

#### Example

```bash
curl -X GET http://localhost:8000/saved_scripts/ \
  -H "Cookie: sessionid=your_session_id"
```

### Save Script

**Endpoint:** `POST /saved_scripts/`  
**View:** `search.views.saved_scripts`  
**Authentication:** Required

#### Request

**Content-Type:** `application/x-www-form-urlencoded`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sql_query` | string | Yes | SQL query to save |
| `countries_list` | string | No | Country list name |
| `selected_countries` | array | No | Array of selected countries |

#### Response

**Success (302):**
- Redirects to saved scripts page

#### Example

```bash
curl -X POST http://localhost:8000/saved_scripts/ \
  -H "Cookie: sessionid=your_session_id" \
  -d "sql_query=SELECT * FROM users&countries_list=first priority countries&selected_countries[]=us"
```

### Python ETL

**Endpoint:** `GET /python_etl/`  
**View:** `search.views.python_etl`  
**Authentication:** Required

#### Request

No parameters required.

#### Response

**Success (200):**
- Returns HTML page with Python ETL interface

#### Example

```bash
curl -X GET http://localhost:8000/python_etl/ \
  -H "Cookie: sessionid=your_session_id"
```

## Error Responses

### Common Error Codes

| Code | Description |
|------|-------------|
| 200 | Success (with error message in JSON) |
| 302 | Redirect |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "status": "error",
  "message": "Error description"
}
```

### Authentication Errors

When authentication is required but not provided:

- **Response:** 302 Redirect to `/account/login/`
- **Headers:** `Location: /account/login/`

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting for production use.

## CORS

CORS is not explicitly configured. For API access from different domains, configure CORS settings in Django.

## Content Types

### Supported Content Types

- `application/x-www-form-urlencoded` (forms)
- `text/html` (page responses)
- `application/json` (API responses)

### File Uploads

Search results are stored as Parquet files with gzip compression:

- **Format:** Parquet with gzip compression
- **Storage:** Local filesystem (`MEDIA_ROOT`)
- **Path:** `search_results/{identifier}.parquet.gzip`

## Security Considerations

### CSRF Protection

All POST requests require CSRF tokens:

```bash
# Get CSRF token first
curl -X GET http://localhost:8000/ \
  -c cookies.txt

# Use CSRF token in POST request
curl -X POST http://localhost:8000/ \
  -b cookies.txt \
  -H "X-CSRFToken: csrf_token_value" \
  -d "query=SELECT * FROM users"
```

### Input Validation

- SQL queries are executed directly (consider implementing query validation)
- File uploads are validated for type and size
- User input is sanitized through Django's form handling

### Authentication Security

- Passwords are hashed using Django's built-in hashing
- Sessions are managed by Django's session framework
- Custom authentication backend validates against hashed passwords

## Testing Endpoints

### Using curl

```bash
# Login and get session cookie
curl -c cookies.txt -X POST http://localhost:8000/account/login/ \
  -d "username=testuser&password=testpass"

# Execute a query
curl -b cookies.txt -X POST http://localhost:8000/ \
  -d "query=SELECT 1 as test&selected_countries[]=us"

# Check history
curl -b cookies.txt -X GET http://localhost:8000/history/
```

### Using Python requests

```python
import requests

# Create session
session = requests.Session()

# Login
login_data = {
    'username': 'testuser',
    'password': 'testpass'
}
response = session.post('http://localhost:8000/account/login/', data=login_data)

# Execute query
query_data = {
    'query': 'SELECT * FROM users LIMIT 10',
    'selected_countries': ['us', 'ca']
}
response = session.post('http://localhost:8000/', data=query_data)
result = response.json()
print(result['table_html'])
```

## WebSocket Support

Currently, no WebSocket endpoints are implemented. Consider implementing WebSocket support for real-time updates on remote query execution.

## API Versioning

Currently, no API versioning is implemented. All endpoints use the current version.

## Documentation Updates

This documentation should be updated whenever:
- New endpoints are added
- Existing endpoints are modified
- Request/response formats change
- Authentication requirements change
- Error handling is updated

For the most up-to-date information, refer to the source code and Django URL configuration.