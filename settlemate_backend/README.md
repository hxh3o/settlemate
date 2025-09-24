# SettleMate Backend

A comprehensive Django backend for the SettleMate expense splitting application with real-time chat functionality.

## Features

- **User Authentication**: JWT-based authentication with password reset
- **Trip Management**: Create trips, invite members, manage trip details
- **Transaction Management**: Create transactions, split expenses, manage bills
- **Real-time Chat**: Socket.IO integration for trip chat
- **File Upload**: Image uploads for chat and bill receipts
- **Minimum Transfer Calculation**: Algorithm to minimize money transfers
- **Email Notifications**: Automated emails for invites and password resets
- **Admin Interface**: Django admin for managing data

## Technology Stack

- **Backend**: Django 5.2, Django REST Framework
- **Database**: PostgreSQL (with SQLite fallback for development)
- **Real-time**: Socket.IO with Eventlet
- **Task Queue**: Celery with Redis
- **Authentication**: JWT tokens
- **File Storage**: Local storage (with Google Drive integration ready)
- **Email**: SMTP with Celery background tasks

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL (optional, SQLite works for development)
- Redis (for Celery and caching)

### Setup

1. **Clone and navigate to the backend directory:**
   ```bash
   cd settlemate_backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration:**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Database Setup:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Create sample data (optional):**
   ```bash
   python manage.py create_sample_data
   ```

## Running the Application

### Development Mode

1. **Start Redis (required for Celery):**
   ```bash
   redis-server
   ```

2. **Start Celery worker (in a separate terminal):**
   ```bash
   celery -A settlemate worker --loglevel=info
   ```

3. **Start the main server:**
   ```bash
   python app.py
   ```

   Or use Django's development server:
   ```bash
   python manage.py runserver
   ```

### Production Mode

1. **Install production dependencies:**
   ```bash
   pip install gunicorn
   ```

2. **Configure environment variables for production**

3. **Run with Gunicorn:**
   ```bash
   gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:8000 settlemate.wsgi:application
   ```

## API Endpoints

### Authentication
- `POST /api/signup/` - User registration
- `POST /api/login/` - User login
- `POST /api/logout/` - User logout
- `POST /api/forgotPassword/` - Request password reset
- `POST /api/changePassword/` - Reset password
- `GET /api/getUserData/` - Get current user data
- `PUT /api/editprofile/` - Edit user profile

### Trip Management
- `POST /api/createtrip/` - Create a new trip
- `GET /api/getTripsData/` - Get user's trips
- `POST /api/getTripData/` - Get trip details
- `POST /api/invite/` - Invite member to trip
- `POST /api/acceptInvite/` - Accept trip invitation
- `POST /api/declineInvite/` - Decline trip invitation
- `GET /api/getInvites/` - Get pending invitations
- `PUT /api/edittrip/` - Edit trip details

### Transaction Management
- `POST /api/createtransaction/` - Create a new transaction
- `GET /api/getTransactions/` - Get trip transactions
- `POST /api/getTransactionData/` - Get transaction details
- `PUT /api/edittransaction/` - Edit transaction
- `DELETE /api/deleteTransaction/` - Delete transaction
- `POST /api/calculateTransfers/` - Calculate minimum transfers

### Chat
- `POST /api/addChat/` - Add chat message
- `POST /api/clearChat/` - Clear trip chat (admin only)
- `GET /api/getChatMessages/` - Get chat messages

### File Upload
- `POST /api/uploadDrive/` - Upload files
- `GET /api/getFileInfo/` - Get file information
- `GET /api/getTripFiles/` - Get trip files
- `DELETE /api/deleteFile/` - Delete file

## Socket.IO Events

### Client to Server
- `join_room` - Join a trip chat room
- `leave_room` - Leave a trip chat room
- `msg` - Send a chat message
- `typing` - Send typing indicator
- `clear_chat` - Clear chat (admin only)

### Server to Client
- `bcast` - Broadcast message to room
- `joined_room` - Confirmation of joining room
- `left_room` - Confirmation of leaving room
- `user_typing` - User typing indicator
- `error` - Error message

## Database Models

### Core Models
- **User**: Custom user model with email authentication
- **Trip**: Trip/group management
- **TripMember**: Many-to-many relationship between trips and users
- **Transaction**: Expense transactions
- **TransactionMember**: Transaction participants and amounts
- **ChatMessage**: Real-time chat messages
- **TripInvite**: Trip invitations
- **PasswordResetToken**: Password reset tokens
- **UserSession**: JWT session management
- **FileUpload**: File upload tracking

## Configuration

### Environment Variables

```bash
# Django Settings
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=settlemate
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
USE_SQLITE=True

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-jwt-secret

# Google Drive (optional)
GOOGLE_DRIVE_CLIENT_ID=your-client-id
GOOGLE_DRIVE_CLIENT_SECRET=your-client-secret
GOOGLE_DRIVE_REDIRECT_URI=your-redirect-uri
```

## Development

### Running Tests
```bash
python manage.py test
```

### Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Creating Superuser
```bash
python manage.py createsuperuser
```

### Django Admin
Access the admin interface at `http://localhost:8000/admin/`

## Deployment

### Docker Deployment (Recommended)

1. **Create Dockerfile:**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   EXPOSE 8000
   
   CMD ["python", "app.py"]
   ```

2. **Create docker-compose.yml:**
   ```yaml
   version: '3.8'
   services:
     web:
       build: .
       ports:
         - "8000:8000"
       environment:
         - DEBUG=False
         - DB_HOST=db
       depends_on:
         - db
         - redis
     
     db:
       image: postgres:15
       environment:
         POSTGRES_DB: settlemate
         POSTGRES_USER: postgres
         POSTGRES_PASSWORD: password
       volumes:
         - postgres_data:/var/lib/postgresql/data
     
     redis:
       image: redis:7-alpine
     
     celery:
       build: .
       command: celery -A settlemate worker --loglevel=info
       depends_on:
         - db
         - redis
   
   volumes:
     postgres_data:
   ```

3. **Deploy:**
   ```bash
   docker-compose up -d
   ```

### Manual Deployment

1. **Install dependencies on server**
2. **Configure environment variables**
3. **Set up PostgreSQL database**
4. **Run migrations**
5. **Start services with process manager (PM2, systemd, etc.)**

## API Documentation

### Request/Response Format

All API responses follow this format:

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {...},
  "errors": [...]
}
```

### Authentication

Include JWT token in Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

### Error Handling

Errors are returned with appropriate HTTP status codes and error messages:

```json
{
  "success": false,
  "errors": [
    {"msg": "Error message"}
  ]
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support, please open an issue on GitHub or contact the development team.
