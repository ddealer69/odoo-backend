#!/usr/bin/env python3
"""
Database initialization script for User Management System
Creates tables and optionally seeds with sample data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Role, User, UserRole

def create_tables():
    """Create all database tables"""
    try:
        with app.app_context():
            print("🏗️  Creating database tables...")
            db.create_all()
            print("✅ Database tables created successfully!")
            return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def seed_sample_data():
    """Seed database with sample data"""
    try:
        with app.app_context():
            print("🌱 Seeding sample data...")
            
            # Create sample roles
            roles_data = [
                {'name': 'Admin', 'description': 'System administrator with full access'},
                {'name': 'Manager', 'description': 'Project manager with limited admin access'},
                {'name': 'Developer', 'description': 'Software developer'},
                {'name': 'Designer', 'description': 'UI/UX designer'},
                {'name': 'Tester', 'description': 'Quality assurance tester'}
            ]
            
            created_roles = []
            for role_data in roles_data:
                # Check if role already exists
                existing_role = Role.query.filter_by(name=role_data['name']).first()
                if not existing_role:
                    role = Role(**role_data)
                    db.session.add(role)
                    created_roles.append(role)
                    print(f"  📝 Created role: {role_data['name']}")
                else:
                    created_roles.append(existing_role)
                    print(f"  ⚠️  Role already exists: {role_data['name']}")
            
            # Create sample users
            users_data = [
                {
                    'email': 'admin@example.com',
                    'full_name': 'System Administrator',
                    'password': 'admin123',
                    'hourly_rate': 100.00,
                    'roles': ['Admin']
                },
                {
                    'email': 'manager@example.com',
                    'full_name': 'Project Manager',
                    'password': 'manager123',
                    'hourly_rate': 80.00,
                    'roles': ['Manager', 'Developer']
                },
                {
                    'email': 'dev1@example.com',
                    'full_name': 'John Developer',
                    'password': 'dev123',
                    'hourly_rate': 60.00,
                    'roles': ['Developer']
                },
                {
                    'email': 'designer@example.com',
                    'full_name': 'Jane Designer',
                    'password': 'design123',
                    'hourly_rate': 55.00,
                    'roles': ['Designer']
                },
                {
                    'email': 'tester@example.com',
                    'full_name': 'Bob Tester',
                    'password': 'test123',
                    'hourly_rate': 45.00,
                    'roles': ['Tester']
                }
            ]
            
            created_users = []
            for user_data in users_data:
                # Check if user already exists
                existing_user = User.query.filter_by(email=user_data['email']).first()
                if not existing_user:
                    user = User(
                        email=user_data['email'],
                        full_name=user_data['full_name'],
                        hourly_rate=user_data['hourly_rate']
                    )
                    user.set_password(user_data['password'])
                    db.session.add(user)
                    db.session.flush()  # Get the user ID
                    created_users.append(user)
                    print(f"  👤 Created user: {user_data['email']}")
                    
                    # Assign roles
                    for role_name in user_data['roles']:
                        role = Role.query.filter_by(name=role_name).first()
                        if role:
                            user_role = UserRole(user_id=user.id, role_id=role.id)
                            db.session.add(user_role)
                            print(f"    🔗 Assigned role '{role_name}' to {user_data['email']}")
                else:
                    created_users.append(existing_user)
                    print(f"  ⚠️  User already exists: {user_data['email']}")
            
            db.session.commit()
            print("✅ Sample data seeded successfully!")
            
            # Print summary
            print("\n📊 Summary:")
            print(f"  Roles: {Role.query.count()}")
            print(f"  Users: {User.query.count()}")
            print(f"  Role Assignments: {UserRole.query.count()}")
            
            return True
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error seeding data: {e}")
        return False

def reset_database():
    """Drop and recreate all tables"""
    try:
        with app.app_context():
            print("🗑️  Dropping existing tables...")
            db.drop_all()
            print("✅ Tables dropped successfully!")
            
            return create_tables()
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False

def main():
    """Main function"""
    print("🚀 User Management Database Initialization")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'reset':
            if reset_database():
                seed_sample_data()
        elif command == 'seed':
            seed_sample_data()
        elif command == 'create':
            create_tables()
        else:
            print("❌ Unknown command. Available commands:")
            print("  create - Create tables only")
            print("  seed   - Seed with sample data")
            print("  reset  - Drop and recreate tables with sample data")
    else:
        # Default: create tables and seed data
        if create_tables():
            seed_sample_data()
    
    print("\n🎉 Database initialization complete!")
    print("You can now start the Flask application with: python3 app.py")

if __name__ == '__main__':
    main()