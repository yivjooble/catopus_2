# Catopus

A Django-based web application for executing SQL queries across multiple country databases with real-time results and background processing capabilities.

## Features

- **Multi-Database Query Execution**: Execute SQL queries across multiple country-specific databases simultaneously
- **Real-Time Results**: Get instant results with parallel processing using thread pools
- **Background Processing**: Execute long-running queries asynchronously using Celery
- **User Authentication**: Custom authentication system with user management
- **Query History**: Save and manage search query history
- **Result Sharing**: Share search results with unique identifiers
- **Script Management**: Save and reuse SQL scripts
- **Remote Execution**: Execute queries on remote database clusters
- **Data Export**: Export results as database tables or files

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis server
- Virtual environment (recommended)

### Installation

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

4. **Environment setup:**
Create a `.env` file:
```env
SECRET_KEY=your-secret-key
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
python manage.py migrate
python manage.py createsuperuser
```

6. **Start services:**
```bash
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: Redis server
redis-server

# Terminal 3: Celery worker
celery -A catopus worker --loglevel=info
```

7. **Access the application:**
Open your browser and navigate to `http://localhost:8000`

## Usage

### Basic Query Execution

1. **Login** to the application
2. **Enter your SQL query** in the query field
3. **Select countries** from the available options
4. **Click Execute** to run the query
5. **View results** in the table below

### Remote Query Execution

1. **Enter your SQL query** and select countries
2. **Check "Remote Execution"** option
3. **Click Execute** to start background processing
4. **Monitor progress** in the Remote Logs section
5. **View results** when processing is complete

### Saving and Sharing Results

1. **Execute a query** and get results
2. **Click "Save as Table"** to save results to database
3. **Use the identifier** to share results with others
4. **Access shared results** via the result URL

## API Documentation

Comprehensive API documentation is available in the following files:

- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Complete API reference
- **[API_ENDPOINTS.md](API_ENDPOINTS.md)** - Detailed endpoint documentation
- **[MODELS_REFERENCE.md](MODELS_REFERENCE.md)** - Database models reference
- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Developer guide and best practices

## Project Structure

```
catopus/
├── account/                 # User authentication
│   ├── models.py           # User model
│   ├── views.py            # Authentication views
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
├── static/                 # Static files
├── logs/                   # Application logs
└── search_result_df/       # Search result files
```

## Configuration

### Database Configuration

The application supports multiple database clusters:

- **NL Cluster**: European and Middle Eastern countries
- **US Cluster**: American and Asian countries

### Country Support

The application supports queries across 70+ countries including:
- United States, Canada, United Kingdom
- Germany, France, Netherlands
- Australia, Japan, South Korea
- And many more...

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key | Yes |
| `DWH_DB` | Main database name | Yes |
| `DWH_USER` | Database username | Yes |
| `DWH_PASSWORD` | Database password | Yes |
| `DWH_HOST` | Database host | Yes |
| `DWH_PORT` | Database port | Yes |
| `RPL_USER` | Remote database username | Yes |
| `RPL_PASSWORD` | Remote database password | Yes |

## Docker Deployment

### Using Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# Stop services
docker-compose down
```

### Manual Docker Build

```bash
# Build image
docker build -t catopus .

# Run container
docker run -p 8000:8000 catopus
```

## Development

### Running Tests

```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Code Style

The project follows PEP 8 and Django conventions:

```bash
# Install development dependencies
pip install black flake8

# Format code
black .

# Check code style
flake8 .
```

### Database Migrations

```bash
# Create migration
python manage.py makemigrations

# Apply migration
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors:**
   - Check database credentials in `.env` file
   - Ensure PostgreSQL is running
   - Verify database exists and is accessible

2. **Celery Task Errors:**
   - Ensure Redis server is running
   - Check Celery worker is started
   - Verify task queue configuration

3. **File Upload Issues:**
   - Check `MEDIA_ROOT` directory permissions
   - Ensure sufficient disk space
   - Verify file format compatibility

4. **Authentication Issues:**
   - Check custom authentication backend
   - Verify user model configuration
   - Ensure password hashing is working

### Debug Mode

Enable debug mode for development:

```python
# settings.py
DEBUG = True
```

### Logging

Application logs are written to:
- `logs/debug.log` - File logging
- Console output - Real-time logging

## Security

### Security Features

- **Password Hashing**: Uses Django's built-in password hashing
- **CSRF Protection**: Enabled for all forms
- **SQL Injection Prevention**: Uses parameterized queries
- **File Upload Security**: Validates file types and sizes
- **Authentication Required**: All views require user authentication

### Security Considerations

- SQL queries are executed directly (consider implementing query validation)
- File uploads are validated for type and size
- User input is sanitized through Django's form handling
- Sessions are managed by Django's session framework

## Performance

### Optimization Features

- **Connection Pooling**: SQLAlchemy connection pooling
- **Parallel Processing**: Thread pool for concurrent queries
- **File Compression**: Parquet files with gzip compression
- **Chunked Database Inserts**: Large datasets inserted in chunks
- **Caching**: Redis for Celery task results

### Performance Monitoring

Monitor application performance using:
- Django Debug Toolbar (development)
- Application logs
- Database query logs
- Celery task monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Guidelines

- Follow PEP 8 and Django conventions
- Write tests for new features
- Update documentation
- Consider security implications
- Test with multiple countries

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the documentation
- Review the source code
- Contact the development team
- Create an issue on GitHub

## Changelog

### Version 1.0.0
- Initial release
- Multi-database query execution
- User authentication system
- Background processing with Celery
- Result sharing and management
- Query history and script saving

---

*For detailed information, refer to the comprehensive documentation files in this repository.*