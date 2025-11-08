#!/usr/bin/env python3
"""
Database initialization script for User Management System
Creates tables and optionally seeds with sample data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Role, User, UserRole, Partner, Product, Project, ProjectMember

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

def seed_master_data():
    """Seed database with master data"""
    try:
        with app.app_context():
            print("🌱 Seeding master data...")
            
            # Create sample partners
            partners_data = [
                {
                    'name': 'Acme Corporation',
                    'type': 'customer',
                    'email': 'contact@acme.com',
                    'phone': '+1-555-0101',
                    'tax_id': 'TAX001',
                    'billing_address': '123 Business Ave, Business City, BC 12345',
                    'shipping_address': '123 Business Ave, Business City, BC 12345'
                },
                {
                    'name': 'Global Suppliers Inc',
                    'type': 'vendor',
                    'email': 'sales@globalsuppliers.com',
                    'phone': '+1-555-0202',
                    'tax_id': 'TAX002',
                    'billing_address': '456 Supplier St, Supply City, SC 54321',
                    'shipping_address': '456 Supplier St, Supply City, SC 54321'
                },
                {
                    'name': 'TechnoMart Ltd',
                    'type': 'both',
                    'email': 'info@technomart.com',
                    'phone': '+1-555-0303',
                    'tax_id': 'TAX003',
                    'billing_address': '789 Tech Plaza, Tech City, TC 67890',
                    'shipping_address': '789 Tech Plaza, Tech City, TC 67890'
                },
                {
                    'name': 'Local Retail Store',
                    'type': 'customer',
                    'email': 'manager@localretail.com',
                    'phone': '+1-555-0404',
                    'tax_id': 'TAX004',
                    'billing_address': '321 Main St, Downtown, DT 13579',
                    'shipping_address': '321 Main St, Downtown, DT 13579'
                },
                {
                    'name': 'Premium Parts Co',
                    'type': 'vendor',
                    'email': 'orders@premiumparts.com',
                    'phone': '+1-555-0505',
                    'tax_id': 'TAX005',
                    'billing_address': '654 Industrial Blvd, Industry City, IC 97531',
                    'shipping_address': '654 Industrial Blvd, Industry City, IC 97531'
                }
            ]
            
            created_partners = []
            for partner_data in partners_data:
                # Check if partner already exists
                existing_partner = Partner.query.filter_by(name=partner_data['name']).first()
                if not existing_partner:
                    partner = Partner(**partner_data)
                    db.session.add(partner)
                    created_partners.append(partner)
                    print(f"  📝 Created partner: {partner_data['name']}")
                else:
                    created_partners.append(existing_partner)
                    print(f"  ⚠️  Partner already exists: {partner_data['name']}")
            
            # Create sample products
            products_data = [
                {
                    'sku': 'LAPTOP-001',
                    'name': 'Business Laptop Pro',
                    'description': 'High-performance laptop for business users',
                    'uom': 'pieces',
                    'default_price': 1299.99
                },
                {
                    'sku': 'MOUSE-001',
                    'name': 'Wireless Optical Mouse',
                    'description': 'Ergonomic wireless mouse with optical sensor',
                    'uom': 'pieces',
                    'default_price': 29.99
                },
                {
                    'sku': 'KB-001',
                    'name': 'Mechanical Keyboard',
                    'description': 'Premium mechanical keyboard with backlight',
                    'uom': 'pieces',
                    'default_price': 149.99
                },
                {
                    'sku': 'MON-001',
                    'name': '27" 4K Monitor',
                    'description': 'Ultra HD 4K monitor for professional use',
                    'uom': 'pieces',
                    'default_price': 399.99
                },
                {
                    'sku': 'CABLE-001',
                    'name': 'USB-C Cable 2m',
                    'description': 'High-speed USB-C cable, 2 meter length',
                    'uom': 'pieces',
                    'default_price': 19.99
                },
                {
                    'sku': 'PAPER-001',
                    'name': 'Copy Paper A4',
                    'description': 'Premium white copy paper, 80gsm',
                    'uom': 'reams',
                    'default_price': 8.99
                },
                {
                    'sku': 'PEN-001',
                    'name': 'Blue Ballpoint Pen',
                    'description': 'Professional ballpoint pen, blue ink',
                    'uom': 'pieces',
                    'default_price': 2.49
                },
                {
                    'sku': 'CHAIR-001',
                    'name': 'Ergonomic Office Chair',
                    'description': 'Adjustable ergonomic chair with lumbar support',
                    'uom': 'pieces',
                    'default_price': 299.99
                }
            ]
            
            created_products = []
            for product_data in products_data:
                # Check if product already exists
                existing_product = Product.query.filter_by(sku=product_data['sku']).first()
                if not existing_product:
                    product = Product(**product_data)
                    db.session.add(product)
                    created_products.append(product)
                    print(f"  📦 Created product: {product_data['sku']} - {product_data['name']}")
                else:
                    created_products.append(existing_product)
                    print(f"  ⚠️  Product already exists: {product_data['sku']}")
            
            db.session.commit()
            print("✅ Master data seeded successfully!")
            
            # Print summary
            print("\n📊 Master Data Summary:")
            print(f"  Partners: {Partner.query.count()}")
            print(f"  Products: {Product.query.count()}")
            
            return True
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error seeding master data: {e}")
        return False

def seed_projects_data():
    """Seed database with projects and team data"""
    try:
        with app.app_context():
            print("🌱 Seeding projects and teaming data...")
            
            # Get existing users for project assignments
            admin_user = User.query.filter_by(email='admin@example.com').first()
            manager_user = User.query.filter_by(email='manager@example.com').first()
            dev_user = User.query.filter_by(email='dev1@example.com').first()
            designer_user = User.query.filter_by(email='designer@example.com').first()
            tester_user = User.query.filter_by(email='tester@example.com').first()
            
            from datetime import date, timedelta
            today = date.today()
            
            # Create sample projects
            projects_data = [
                {
                    'project_code': 'WEB-2024-001',
                    'name': 'E-commerce Website Redesign',
                    'description': 'Complete redesign of the company e-commerce website with modern UI/UX',
                    'project_manager_id': manager_user.id if manager_user else None,
                    'start_date': today,
                    'end_date': today + timedelta(days=90),
                    'status': 'in_progress',
                    'budget_amount': 50000.00,
                    'members': [
                        {'user': dev_user, 'role': 'Lead Developer'},
                        {'user': designer_user, 'role': 'UI/UX Designer'},
                        {'user': tester_user, 'role': 'QA Tester'}
                    ]
                },
                {
                    'project_code': 'MOB-2024-001',
                    'name': 'Mobile App Development',
                    'description': 'Development of cross-platform mobile application',
                    'project_manager_id': manager_user.id if manager_user else None,
                    'start_date': today + timedelta(days=30),
                    'end_date': today + timedelta(days=180),
                    'status': 'planned',
                    'budget_amount': 75000.00,
                    'members': [
                        {'user': dev_user, 'role': 'Mobile Developer'},
                        {'user': designer_user, 'role': 'UI Designer'}
                    ]
                },
                {
                    'project_code': 'INT-2024-001',
                    'name': 'System Integration Project',
                    'description': 'Integration of multiple backend systems and APIs',
                    'project_manager_id': admin_user.id if admin_user else None,
                    'start_date': today - timedelta(days=60),
                    'end_date': today + timedelta(days=30),
                    'status': 'in_progress',
                    'budget_amount': 35000.00,
                    'members': [
                        {'user': dev_user, 'role': 'Backend Developer'},
                        {'user': tester_user, 'role': 'Integration Tester'}
                    ]
                },
                {
                    'project_code': 'UPG-2024-001',
                    'name': 'Database Upgrade',
                    'description': 'Upgrade legacy database system to modern architecture',
                    'project_manager_id': admin_user.id if admin_user else None,
                    'start_date': today - timedelta(days=120),
                    'end_date': today - timedelta(days=30),
                    'status': 'completed',
                    'budget_amount': 25000.00,
                    'members': [
                        {'user': dev_user, 'role': 'Database Developer'},
                        {'user': tester_user, 'role': 'Data Migration Tester'}
                    ]
                },
                {
                    'project_code': 'RES-2024-001',
                    'name': 'Research & Development',
                    'description': 'Research new technologies and development methodologies',
                    'project_manager_id': None,  # No project manager assigned
                    'start_date': today,
                    'end_date': today + timedelta(days=365),
                    'status': 'on_hold',
                    'budget_amount': 15000.00,
                    'members': [
                        {'user': dev_user, 'role': 'Research Developer'}
                    ]
                }
            ]
            
            created_projects = []
            for project_data in projects_data:
                # Check if project already exists
                existing_project = Project.query.filter_by(project_code=project_data['project_code']).first()
                if not existing_project:
                    # Extract member data before creating project
                    member_assignments = project_data.pop('members', [])
                    
                    project = Project(**project_data)
                    db.session.add(project)
                    db.session.flush()  # Get the project ID
                    created_projects.append(project)
                    print(f"  📁 Created project: {project_data['project_code']} - {project_data['name']}")
                    
                    # Assign team members
                    for member_data in member_assignments:
                        user = member_data['user']
                        role = member_data['role']
                        if user:
                            project_member = ProjectMember(
                                project_id=project.id,
                                user_id=user.id,
                                role_in_project=role
                            )
                            db.session.add(project_member)
                            print(f"    👥 Assigned {user.email} as {role}")
                else:
                    created_projects.append(existing_project)
                    print(f"  ⚠️  Project already exists: {project_data['project_code']}")
            
            db.session.commit()
            print("✅ Projects and teaming data seeded successfully!")
            
            # Print summary
            print("\n📊 Projects Summary:")
            print(f"  Projects: {Project.query.count()}")
            print(f"  Project Members: {ProjectMember.query.count()}")
            
            return True
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error seeding projects data: {e}")
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
                seed_master_data()
                seed_projects_data()
        elif command == 'seed':
            seed_sample_data()
            seed_master_data()
            seed_projects_data()
        elif command == 'seed-users':
            seed_sample_data()
        elif command == 'seed-master':
            seed_master_data()
        elif command == 'seed-projects':
            seed_projects_data()
        elif command == 'create':
            create_tables()
        else:
            print("❌ Unknown command. Available commands:")
            print("  create         - Create tables only")
            print("  seed           - Seed with all sample data")
            print("  seed-users     - Seed with user data only")
            print("  seed-master    - Seed with master data only")
            print("  seed-projects  - Seed with projects data only")
            print("  reset          - Drop and recreate tables with all sample data")
    else:
        # Default: create tables and seed all data
        if create_tables():
            seed_sample_data()
            seed_master_data()
            seed_projects_data()
    
    print("\n🎉 Database initialization complete!")
    print("You can now start the Flask application with: python3 app.py")

if __name__ == '__main__':
    main()