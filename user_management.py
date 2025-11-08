from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import re

# Create Blueprint for user management
user_management_bp = Blueprint('user_management', __name__)

# Database instance (will be initialized from main app)
db = None

def init_user_management(database):
    """Initialize the user management module with database instance"""
    global db, Role, User, UserRole
    db = database
    
    # Create model classes
    Role, User, UserRole = create_models(db)
    
    return Role, User, UserRole

# =============================================
# SQLAlchemy Models
# =============================================

def create_models(db_instance):
    """Create and return the model classes"""
    
    class Role(db_instance.Model):
        __tablename__ = 'roles'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String(50), nullable=False, unique=True)
        description = Column(String(255), nullable=True)
        
        # Relationships
        users = relationship('UserRole', back_populates='role', cascade='all, delete')
        
        def to_dict(self):
            return {
                'id': self.id,
                'name': self.name,
                'description': self.description
            }

    class User(db_instance.Model):
        __tablename__ = 'users'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        email = Column(String(190), nullable=False, unique=True)
        full_name = Column(String(120), nullable=False)
        password_hash = Column(String(255), nullable=False)
        is_active = Column(Boolean, nullable=False, default=True)
        hourly_rate = Column(DECIMAL(10, 2), nullable=False, default=0.00)
        created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
        updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        # Relationships
        roles = relationship('UserRole', back_populates='user', cascade='all, delete-orphan')
        
        def to_dict(self, include_roles=False):
            user_data = {
                'id': self.id,
                'email': self.email,
                'full_name': self.full_name,
                'is_active': self.is_active,
                'hourly_rate': float(self.hourly_rate),
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }
            
            if include_roles:
                user_data['roles'] = [
                    {
                        'id': ur.role.id,
                        'name': ur.role.name,
                        'description': ur.role.description
                    } for ur in self.roles
                ]
            
            return user_data
        
        def set_password(self, password):
            self.password_hash = generate_password_hash(password)
        
        def check_password(self, password):
            return check_password_hash(self.password_hash, password)

    class UserRole(db_instance.Model):
        __tablename__ = 'user_roles'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
        role_id = Column(Integer, ForeignKey('roles.id', ondelete='RESTRICT'), nullable=False)
        
        __table_args__ = (UniqueConstraint('user_id', 'role_id', name='uq_user_role'),)
        
        # Relationships
        user = relationship('User', back_populates='roles')
        role = relationship('Role', back_populates='users')
        
        def to_dict(self):
            return {
                'id': self.id,
                'user_id': self.user_id,
                'role_id': self.role_id,
                'user': {
                    'id': self.user.id,
                    'email': self.user.email,
                    'full_name': self.user.full_name
                } if self.user else None,
                'role': {
                    'id': self.role.id,
                    'name': self.role.name,
                    'description': self.role.description
                } if self.role else None
            }
    
    return Role, User, UserRole

# Model classes (will be set during initialization)
Role = None
User = None
UserRole = None# =============================================
# Helper Functions
# =============================================

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def handle_error(error, message="An error occurred"):
    """Standard error handler"""
    if isinstance(error, IntegrityError):
        return jsonify({'error': 'Data integrity error', 'details': str(error.orig)}), 400
    elif isinstance(error, SQLAlchemyError):
        return jsonify({'error': 'Database error', 'details': str(error)}), 500
    else:
        return jsonify({'error': message, 'details': str(error)}), 500

# =============================================
# ROLE CRUD Operations
# =============================================

@user_management_bp.route('/roles', methods=['GET'])
def get_all_roles():
    """Get all roles"""
    try:
        roles = Role.query.all()
        return jsonify({
            'status': 'success',
            'data': [role.to_dict() for role in roles],
            'count': len(roles)
        }), 200
    except Exception as e:
        return handle_error(e, "Failed to fetch roles")

@user_management_bp.route('/roles/<int:role_id>', methods=['GET'])
def get_role(role_id):
    """Get single role by ID"""
    try:
        role = Role.query.get(role_id)
        if not role:
            return jsonify({'error': 'Role not found'}), 404
        
        return jsonify({
            'status': 'success',
            'data': role.to_dict()
        }), 200
    except Exception as e:
        return handle_error(e, "Failed to fetch role")

@user_management_bp.route('/roles', methods=['POST'])
def create_role():
    """Create new role"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Role name is required'}), 400
        
        role = Role(
            name=data['name'],
            description=data.get('description')
        )
        
        db.session.add(role)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Role created successfully',
            'data': role.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to create role")

@user_management_bp.route('/roles/<int:role_id>', methods=['PUT'])
def update_role(role_id):
    """Update existing role"""
    try:
        role = Role.query.get(role_id)
        if not role:
            return jsonify({'error': 'Role not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if 'name' in data:
            role.name = data['name']
        if 'description' in data:
            role.description = data['description']
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Role updated successfully',
            'data': role.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to update role")

@user_management_bp.route('/roles/<int:role_id>', methods=['DELETE'])
def delete_role(role_id):
    """Delete role"""
    try:
        role = Role.query.get(role_id)
        if not role:
            return jsonify({'error': 'Role not found'}), 404
        
        # Check if role is assigned to any users
        user_count = UserRole.query.filter_by(role_id=role_id).count()
        if user_count > 0:
            return jsonify({
                'error': 'Cannot delete role',
                'details': f'Role is assigned to {user_count} user(s)'
            }), 400
        
        db.session.delete(role)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Role deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to delete role")

# =============================================
# USER CRUD Operations
# =============================================

@user_management_bp.route('/users', methods=['GET'])
def get_all_users():
    """Get all users with optional role information"""
    try:
        include_roles = request.args.get('include_roles', 'false').lower() == 'true'
        users = User.query.all()
        
        return jsonify({
            'status': 'success',
            'data': [user.to_dict(include_roles=include_roles) for user in users],
            'count': len(users)
        }), 200
    except Exception as e:
        return handle_error(e, "Failed to fetch users")

@user_management_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get single user by ID with roles"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'status': 'success',
            'data': user.to_dict(include_roles=True)
        }), 200
    except Exception as e:
        return handle_error(e, "Failed to fetch user")

@user_management_bp.route('/users', methods=['POST'])
def create_user():
    """Create new user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['email', 'full_name', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate email format
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if email already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        user = User(
            email=data['email'],
            full_name=data['full_name'],
            is_active=data.get('is_active', True),
            hourly_rate=data.get('hourly_rate', 0.00)
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'User created successfully',
            'data': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to create user")

@user_management_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update existing user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update fields if provided
        if 'email' in data:
            if not validate_email(data['email']):
                return jsonify({'error': 'Invalid email format'}), 400
            # Check if email already exists for another user
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({'error': 'Email already exists'}), 400
            user.email = data['email']
        
        if 'full_name' in data:
            user.full_name = data['full_name']
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        if 'hourly_rate' in data:
            user.hourly_rate = data['hourly_rate']
        
        if 'password' in data:
            user.set_password(data['password'])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'User updated successfully',
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to update user")

@user_management_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'User deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to delete user")

# =============================================
# USER-ROLE Assignment Operations
# =============================================

@user_management_bp.route('/users/<int:user_id>/roles', methods=['POST'])
def assign_role_to_user(user_id):
    """Assign role to user"""
    try:
        data = request.get_json()
        
        if not data or 'role_id' not in data:
            return jsonify({'error': 'role_id is required'}), 400
        
        role_id = data['role_id']
        
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if role exists
        role = Role.query.get(role_id)
        if not role:
            return jsonify({'error': 'Role not found'}), 404
        
        # Check if assignment already exists
        existing_assignment = UserRole.query.filter_by(user_id=user_id, role_id=role_id).first()
        if existing_assignment:
            return jsonify({'error': 'User already has this role'}), 400
        
        user_role = UserRole(user_id=user_id, role_id=role_id)
        db.session.add(user_role)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Role assigned successfully',
            'data': user_role.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to assign role")

@user_management_bp.route('/users/<int:user_id>/roles/<int:role_id>', methods=['DELETE'])
def remove_role_from_user(user_id, role_id):
    """Remove role from user"""
    try:
        user_role = UserRole.query.filter_by(user_id=user_id, role_id=role_id).first()
        if not user_role:
            return jsonify({'error': 'User role assignment not found'}), 404
        
        db.session.delete(user_role)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Role removed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to remove role")

@user_management_bp.route('/users/<int:user_id>/roles', methods=['GET'])
def get_user_roles(user_id):
    """Get all roles for a user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_roles = UserRole.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'status': 'success',
            'data': [ur.to_dict() for ur in user_roles],
            'count': len(user_roles)
        }), 200
        
    except Exception as e:
        return handle_error(e, "Failed to fetch user roles")

# =============================================
# USER-ROLE Table Operations
# =============================================

@user_management_bp.route('/user-roles', methods=['GET'])
def get_all_user_roles():
    """Get all user-role assignments"""
    try:
        user_roles = UserRole.query.all()
        
        return jsonify({
            'status': 'success',
            'data': [ur.to_dict() for ur in user_roles],
            'count': len(user_roles)
        }), 200
        
    except Exception as e:
        return handle_error(e, "Failed to fetch user roles")

# =============================================
# Statistics and Summary Endpoints
# =============================================

@user_management_bp.route('/stats', methods=['GET'])
def get_statistics():
    """Get system statistics"""
    try:
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        total_roles = Role.query.count()
        total_assignments = UserRole.query.count()
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_users': total_users,
                'active_users': active_users,
                'inactive_users': total_users - active_users,
                'total_roles': total_roles,
                'total_role_assignments': total_assignments
            }
        }), 200
        
    except Exception as e:
        return handle_error(e, "Failed to fetch statistics")