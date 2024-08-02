# Demo Application: User Authentication and File Management

This application demonstrates a simple user authentication and file management system using Flask and PostgreSQL.

## Setup Instructions

Follow these steps to set up and run the application:

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Set up Venv

#### Mac or Unix
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Windows
```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install requirements.txt
```bash
pip install -r requirements.txt
```

### 4. Fill out .env

#### Generate random secret key
```python
import secrets

# Generate a 32-byte (256-bit) random key
secret_key = secrets.token_hex(32)
print(secret_key)
```

### 5. Docker Postgres Database 

#### To Run the Database
```bash
docker-compose up -d
```

#### To Bring Down the Database
```bash
docker-compose down
```

### 6. Run App 
```bash
python app.py
```

## API Endpoints

1. POST /register: Register a new user
2. POST /login: Log in and receive a JWT token
3. POST /upload: Upload a file (requires authentication)
4. GET /files: List all files for the authenticated user
5. GET /files/<file_id>: Download a specific file
6. GET /admin/users: List all users (admin only)

### Concepts for a Flask-based Application

- User authentication system (login, logout, registration)
- File upload and download functionality
- User activity logging
- Basic role-based access control

### Application Capabilities

- Generate logs for authentication attempts (successful and failed)
- Track file access and modifications
- Monitor user activities
- Implement and observe basic security measures

### Observability and Security Testing Opportunities

- Authentication flows (login attempts, successful/failed logins)
- File operations (uploads, downloads, access attempts)
- Role-based access control (regular users vs. admin)
- JWT token handling and validation

### Observability with OpenTelemetry

- Add tracing to each endpoint
- Log all authentication attempts and file operations
- Create custom metrics (e.g., login success rate, file upload/download counts)
- Add error handling and track exceptions

### Security and SIEM Use Cases

- Monitor failed login attempts (potential brute force attacks)
- Track file access patterns (potential data exfiltration)
- Implement rate limiting and log excessive requests (DoS prevention)
- Monitor admin activities
- Implement and log input validation to prevent injection attacks

### Enhancements for SIEM Testing

- Implement more detailed logging, including user IP addresses, user agents, and timestamps
- Add honeypot endpoints to detect potential scanners or attackers
- Implement session management and track concurrent logins
- Add file type checking and scanning for uploaded files