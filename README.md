# Flask SQLAlchemy User Management API

A comprehensive Flask application with SQLAlchemy for MySQL database connectivity, featuring complete CRUD operations for user management, role-based access control, and user-role assignments.

## 📋 Features

- **Complete User Management** - CRUD operations for users with authentication
- **Role-Based Access Control** - Create, manage, and assign roles
- **User-Role Assignments** - Flexible many-to-many relationships
- **MySQL Database Integration** - Using SQLAlchemy ORM with PyMySQL driver
- **Comprehensive API** - RESTful endpoints for all operations
- **Data Validation** - Email validation, password hashing, and integrity checks
- **Error Handling** - Proper JSON error responses with detailed messages
- **Database Initialization** - Automated setup with sample data

## 🗄️ Database Schema

### Tables Structure:
```sql
-- Roles table
CREATE TABLE roles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE,
  description VARCHAR(255) NULL
);

-- Users table  
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(190) NOT NULL UNIQUE,
  full_name VARCHAR(120) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  hourly_rate DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- User-Role assignments (many-to-many)
CREATE TABLE user_roles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  role_id INT NOT NULL,
  UNIQUE KEY uq_user_role (user_id, role_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT
);
```

## 🔧 Database Configuration

Database credentials are stored in `db_config.py`:
```
Host: 127.0.0.1
Port: 3306
User: root
Password: pass
Database: mydb
```

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
# Create tables and seed with sample data
python3 init_db.py

# Or use specific commands:
python3 init_db.py create  # Create tables only
python3 init_db.py seed    # Seed with sample data
python3 init_db.py reset   # Reset and recreate with data
```

### 3. Start the Application
```bash
python3 app.py
```
Server runs on `http://localhost:5000`

### 4. Test All Endpoints
```bash
python3 test_endpoints.py
```

## 📡 API Endpoints

### Health & System Endpoints

#### Health Check
```bash
GET /
```
**Response:**
```json
{
  "status": "success",
  "message": "Health API is working perfectly!",
  "service": "Flask SQLAlchemy Backend",
  "version": "1.0.0"
}
```

#### Database Connection Test
```bash
GET /connection
```

#### Initialize Database
```bash
POST /api/v1/init-db
```

#### System Statistics
```bash
GET /api/v1/stats
```

### Role Management

#### Get All Roles
```bash
GET /api/v1/roles

# Example Response:
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "Admin",
      "description": "System administrator"
    }
  ],
  "count": 1
}
```

#### Get Single Role
```bash
GET /api/v1/roles/{role_id}
```

#### Create Role
```bash
POST /api/v1/roles
Content-Type: application/json

{
  "name": "Developer",
  "description": "Software developer role"
}
```

#### Update Role
```bash
PUT /api/v1/roles/{role_id}
Content-Type: application/json

{
  "name": "Senior Developer",
  "description": "Senior software developer role"
}
```

#### Delete Role
```bash
DELETE /api/v1/roles/{role_id}
```

### User Management

#### Get All Users
```bash
# Without roles
GET /api/v1/users

# With roles included
GET /api/v1/users?include_roles=true
```

#### Get Single User
```bash
GET /api/v1/users/{user_id}
# Always includes roles
```

#### Create User
```bash
POST /api/v1/users
Content-Type: application/json

{
  "email": "john@example.com",
  "full_name": "John Doe",
  "password": "securepassword123",
  "hourly_rate": 75.00,
  "is_active": true
}
```

#### Update User
```bash
PUT /api/v1/users/{user_id}
Content-Type: application/json

{
  "full_name": "John Smith",
  "hourly_rate": 85.00,
  "is_active": true
}
```

#### Delete User
```bash
DELETE /api/v1/users/{user_id}
```

### User-Role Assignment

#### Assign Role to User
```bash
POST /api/v1/users/{user_id}/roles
Content-Type: application/json

{
  "role_id": 1
}
```

#### Remove Role from User
```bash
DELETE /api/v1/users/{user_id}/roles/{role_id}
```

#### Get User's Roles
```bash
GET /api/v1/users/{user_id}/roles
```

#### Get All User-Role Assignments
```bash
GET /api/v1/user-roles
```

## 🧪 Testing Examples

### Complete Workflow Example

```bash
# 1. Check health
curl http://localhost:5000/

# 2. Test database connection  
curl http://localhost:5000/connection

# 3. Create a role
curl -X POST http://localhost:5000/api/v1/roles \
  -H "Content-Type: application/json" \
  -d '{"name": "Developer", "description": "Software developer"}'

# 4. Create a user
curl -X POST http://localhost:5000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dev@example.com",
    "full_name": "Developer User",
    "password": "dev123",
    "hourly_rate": 60.00
  }'

# 5. Assign role to user (assuming role_id=1, user_id=1)
curl -X POST http://localhost:5000/api/v1/users/1/roles \
  -H "Content-Type: application/json" \
  -d '{"role_id": 1}'

# 6. Get user with roles
curl http://localhost:5000/api/v1/users/1

# 7. Get all users with roles
curl "http://localhost:5000/api/v1/users?include_roles=true"

# 8. Get statistics
curl http://localhost:5000/api/v1/stats
```

### Advanced Testing

```bash
# Get all roles
curl http://localhost:5000/api/v1/roles

# Update user
curl -X PUT http://localhost:5000/api/v1/users/1 \
  -H "Content-Type: application/json" \
  -d '{"hourly_rate": 75.00, "is_active": true}'

# Remove role from user
curl -X DELETE http://localhost:5000/api/v1/users/1/roles/1

# Delete user
curl -X DELETE http://localhost:5000/api/v1/users/1

# Delete role  
curl -X DELETE http://localhost:5000/api/v1/roles/1
```

## 📁 Project Structure

```
odoo-backend/
├── app.py                 # Main Flask application
├── user_management.py     # User management module with models & routes
├── db_config.py          # Database configuration
├── init_db.py            # Database initialization script
├── test_endpoints.py     # Comprehensive API testing script
├── requirements.txt      # Python dependencies
└── README.md            # This documentation
```

## 🔒 Dependencies

```
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
PyMySQL==1.1.0
cryptography==41.0.4
```

## ⚡ Features Included

### Security Features:
- Password hashing with Werkzeug
- Email format validation
- SQL injection protection via SQLAlchemy
- Foreign key constraints

### Data Integrity:
- Unique constraints on email and role names
- Cascade delete for user-role relationships
- Restrict delete for roles with users
- Automatic timestamp management

### Error Handling:
- Comprehensive error responses
- Database integrity error handling
- 404 handling for non-existent resources
- Validation error responses

## 🛠️ Sample Data

The initialization script creates sample users and roles:

**Roles:**
- Admin (System administrator)
- Manager (Project manager)  
- Developer (Software developer)
- Designer (UI/UX designer)
- Tester (QA tester)

**Users:**
- admin@example.com (Admin role)
- manager@example.com (Manager + Developer roles)
- dev1@example.com (Developer role)
- designer@example.com (Designer role)
- tester@example.com (Tester role)

Default password for all sample users: `[role]123` (e.g., admin123, manager123)

## 🎯 Usage Scenarios

Perfect for:
- User management systems
- Role-based access control (RBAC)
- Team management applications
- HR systems
- Project management tools
- Multi-tenant applications

## 🔧 Customization

To extend the system:
1. Add new fields to User/Role models in `user_management.py`
2. Create new endpoints in the blueprint
3. Update the database schema
4. Run database migrations

The modular design makes it easy to integrate with existing Flask applications or extend with additional features like JWT authentication, permissions, etc.