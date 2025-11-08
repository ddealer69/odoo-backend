#!/usr/bin/env python3
"""
Database initialization script for User Management System
Creates tables and optionally seeds with sample data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Role, User, UserRole, Partner, Product, Project, ProjectMember, Task, TaskAssignment, TaskComment, TaskAttachment, SalesOrder, SalesOrderLine

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

def seed_tasks_data():
    """Seed database with tasks and collaboration data"""
    try:
        with app.app_context():
            print("🌱 Seeding tasks and collaboration data...")
            
            # Get existing data
            projects = Project.query.all()
            if not projects:
                print("  ⚠️  No projects found. Please seed projects first.")
                return False
            
            users = User.query.all()
            if not users:
                print("  ⚠️  No users found. Please seed users first.")
                return False
            
            from datetime import date, timedelta
            today = date.today()
            
            # Create sample tasks for first project (E-commerce Website)
            if len(projects) >= 1:
                project1 = projects[0]
                
                tasks_data = [
                    {
                        'project': project1,
                        'title': 'Design Homepage Mockup',
                        'description': 'Create wireframes and mockups for the new homepage design',
                        'priority': 'high',
                        'state': 'done',
                        'due_date': today - timedelta(days=5),
                        'created_by': users[1].id if len(users) > 1 else users[0].id,
                        'assignees': [users[3].id] if len(users) > 3 else [],
                        'comments': [
                            {'user_id': users[1].id if len(users) > 1 else None, 'comment': 'Please use our brand colors'},
                            {'user_id': users[3].id if len(users) > 3 else None, 'comment': 'Mockups completed and shared'}
                        ],
                        'attachments': [
                            {'file_name': 'homepage_mockup_v1.pdf', 'file_url': 'https://example.com/files/homepage_mockup_v1.pdf', 'uploaded_by': users[3].id if len(users) > 3 else None}
                        ]
                    },
                    {
                        'project': project1,
                        'title': 'Implement Product Catalog API',
                        'description': 'Develop RESTful API endpoints for product listing and filtering',
                        'priority': 'urgent',
                        'state': 'in_progress',
                        'due_date': today + timedelta(days=3),
                        'created_by': users[1].id if len(users) > 1 else users[0].id,
                        'assignees': [users[2].id] if len(users) > 2 else [],
                        'comments': [
                            {'user_id': users[2].id if len(users) > 2 else None, 'comment': 'API structure designed, now implementing'},
                            {'user_id': users[1].id if len(users) > 1 else None, 'comment': 'Great! Please add pagination support'}
                        ],
                        'attachments': []
                    },
                    {
                        'project': project1,
                        'title': 'Setup Payment Gateway Integration',
                        'description': 'Integrate Stripe payment gateway for checkout process',
                        'priority': 'high',
                        'state': 'blocked',
                        'due_date': today + timedelta(days=7),
                        'created_by': users[1].id if len(users) > 1 else users[0].id,
                        'assignees': [users[2].id] if len(users) > 2 else [],
                        'comments': [
                            {'user_id': users[2].id if len(users) > 2 else None, 'comment': 'Waiting for Stripe API credentials from client'}
                        ],
                        'attachments': []
                    },
                    {
                        'project': project1,
                        'title': 'Write Unit Tests for Cart Module',
                        'description': 'Create comprehensive unit tests for shopping cart functionality',
                        'priority': 'medium',
                        'state': 'new',
                        'due_date': today + timedelta(days=10),
                        'created_by': users[1].id if len(users) > 1 else users[0].id,
                        'assignees': [users[4].id] if len(users) > 4 else [],
                        'comments': [],
                        'attachments': []
                    },
                    {
                        'project': project1,
                        'title': 'Optimize Database Queries',
                        'description': 'Review and optimize slow database queries identified in performance testing',
                        'priority': 'low',
                        'state': 'new',
                        'due_date': today + timedelta(days=14),
                        'created_by': users[1].id if len(users) > 1 else users[0].id,
                        'assignees': [],
                        'comments': [],
                        'attachments': []
                    }
                ]
                
                for task_data in tasks_data:
                    assignees = task_data.pop('assignees', [])
                    comments_data = task_data.pop('comments', [])
                    attachments_data = task_data.pop('attachments', [])
                    project = task_data.pop('project')
                    
                    task = Task(
                        project_id=project.id,
                        title=task_data['title'],
                        description=task_data['description'],
                        priority=task_data['priority'],
                        state=task_data['state'],
                        due_date=task_data['due_date'],
                        created_by=task_data['created_by']
                    )
                    
                    db.session.add(task)
                    db.session.flush()
                    print(f"  📋 Created task: {task.title}")
                    
                    # Add assignees
                    for user_id in assignees:
                        assignment = TaskAssignment(task_id=task.id, user_id=user_id)
                        db.session.add(assignment)
                        print(f"    👤 Assigned user {user_id} to task")
                    
                    # Add comments
                    for comment_data in comments_data:
                        comment = TaskComment(
                            task_id=task.id,
                            user_id=comment_data['user_id'],
                            comment=comment_data['comment']
                        )
                        db.session.add(comment)
                        print(f"    💬 Added comment to task")
                    
                    # Add attachments
                    for attachment_data in attachments_data:
                        attachment = TaskAttachment(
                            task_id=task.id,
                            uploaded_by=attachment_data['uploaded_by'],
                            file_name=attachment_data['file_name'],
                            file_url=attachment_data['file_url']
                        )
                        db.session.add(attachment)
                        print(f"    📎 Added attachment to task")
            
            # Create sample tasks for second project (Mobile App) if exists
            if len(projects) >= 2:
                project2 = projects[1]
                
                mobile_tasks = [
                    {
                        'project': project2,
                        'title': 'Setup React Native Project',
                        'description': 'Initialize React Native project with required dependencies',
                        'priority': 'urgent',
                        'state': 'done',
                        'due_date': today - timedelta(days=10),
                        'created_by': users[1].id if len(users) > 1 else users[0].id,
                        'assignees': [users[2].id] if len(users) > 2 else []
                    },
                    {
                        'project': project2,
                        'title': 'Design Mobile App UI',
                        'description': 'Create UI designs for all mobile app screens',
                        'priority': 'high',
                        'state': 'in_progress',
                        'due_date': today + timedelta(days=5),
                        'created_by': users[1].id if len(users) > 1 else users[0].id,
                        'assignees': [users[3].id] if len(users) > 3 else []
                    },
                    {
                        'project': project2,
                        'title': 'Implement User Authentication',
                        'description': 'Add login and registration functionality',
                        'priority': 'high',
                        'state': 'new',
                        'due_date': today + timedelta(days=15),
                        'created_by': users[1].id if len(users) > 1 else users[0].id,
                        'assignees': []
                    }
                ]
                
                for task_data in mobile_tasks:
                    assignees = task_data.pop('assignees', [])
                    project = task_data.pop('project')
                    
                    task = Task(
                        project_id=project.id,
                        title=task_data['title'],
                        description=task_data['description'],
                        priority=task_data['priority'],
                        state=task_data['state'],
                        due_date=task_data['due_date'],
                        created_by=task_data['created_by']
                    )
                    
                    db.session.add(task)
                    db.session.flush()
                    print(f"  📋 Created task: {task.title}")
                    
                    for user_id in assignees:
                        assignment = TaskAssignment(task_id=task.id, user_id=user_id)
                        db.session.add(assignment)
            
            db.session.commit()
            print("✅ Tasks and collaboration data seeded successfully!")
            
            # Print summary
            print("\n📊 Tasks Summary:")
            print(f"  Tasks: {Task.query.count()}")
            print(f"  Task Assignments: {TaskAssignment.query.count()}")
            print(f"  Task Comments: {TaskComment.query.count()}")
            print(f"  Task Attachments: {TaskAttachment.query.count()}")
            
            return True
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error seeding tasks data: {e}")
        import traceback
        traceback.print_exc()
        return False

def seed_sales_orders_data():
    """Seed database with sales orders data"""
    try:
        with app.app_context():
            print("🌱 Seeding sales orders data...")
            
            # Get existing data
            projects = Project.query.all()
            if not projects:
                print("  ⚠️  No projects found. Please seed projects first.")
                return False
            
            customers = Partner.query.filter(Partner.type.in_(['customer', 'both'])).all()
            if not customers:
                print("  ⚠️  No customers found. Please seed partners first.")
                return False
            
            products = Product.query.all()
            
            from datetime import date, timedelta
            today = date.today()
            
            # Create sample sales orders
            sales_orders_data = [
                {
                    'so_number': 'SO-2024-001',
                    'project': projects[0] if len(projects) > 0 else None,
                    'customer': customers[0] if len(customers) > 0 else None,
                    'order_date': today - timedelta(days=30),
                    'status': 'confirmed',
                    'currency': 'INR',
                    'notes': 'Initial order for website development',
                    'lines': [
                        {
                            'product': products[0] if len(products) > 0 else None,
                            'description': 'Website Design & Development',
                            'quantity': 1.0,
                            'unit_price': 50000.00,
                            'milestone_flag': True
                        },
                        {
                            'product': products[1] if len(products) > 1 else None,
                            'description': 'SEO Optimization',
                            'quantity': 1.0,
                            'unit_price': 10000.00,
                            'milestone_flag': False
                        },
                        {
                            'product': None,
                            'description': 'Content Writing (10 pages)',
                            'quantity': 10.0,
                            'unit_price': 500.00,
                            'milestone_flag': False
                        }
                    ]
                },
                {
                    'so_number': 'SO-2024-002',
                    'project': projects[1] if len(projects) > 1 else projects[0],
                    'customer': customers[1] if len(customers) > 1 else customers[0],
                    'order_date': today - timedelta(days=15),
                    'status': 'confirmed',
                    'currency': 'USD',
                    'notes': 'Mobile app development contract',
                    'lines': [
                        {
                            'product': None,
                            'description': 'Mobile App Development - iOS',
                            'quantity': 1.0,
                            'unit_price': 30000.00,
                            'milestone_flag': True
                        },
                        {
                            'product': None,
                            'description': 'Mobile App Development - Android',
                            'quantity': 1.0,
                            'unit_price': 30000.00,
                            'milestone_flag': True
                        },
                        {
                            'product': None,
                            'description': 'API Integration',
                            'quantity': 1.0,
                            'unit_price': 8000.00,
                            'milestone_flag': False
                        }
                    ]
                },
                {
                    'so_number': 'SO-2024-003',
                    'project': projects[2] if len(projects) > 2 else projects[0],
                    'customer': customers[0] if len(customers) > 0 else None,
                    'order_date': today - timedelta(days=5),
                    'status': 'draft',
                    'currency': 'INR',
                    'notes': 'Pending approval from management',
                    'lines': [
                        {
                            'product': products[2] if len(products) > 2 else None,
                            'description': 'System Integration Services',
                            'quantity': 1.0,
                            'unit_price': 25000.00,
                            'milestone_flag': False
                        }
                    ]
                },
                {
                    'so_number': 'SO-2024-004',
                    'project': projects[0] if len(projects) > 0 else None,
                    'customer': customers[1] if len(customers) > 1 else customers[0],
                    'order_date': today - timedelta(days=60),
                    'status': 'closed',
                    'currency': 'INR',
                    'notes': 'Completed and delivered',
                    'lines': [
                        {
                            'product': products[3] if len(products) > 3 else None,
                            'description': 'Database Upgrade & Optimization',
                            'quantity': 1.0,
                            'unit_price': 15000.00,
                            'milestone_flag': True
                        },
                        {
                            'product': None,
                            'description': 'Training Sessions (5 hours)',
                            'quantity': 5.0,
                            'unit_price': 2000.00,
                            'milestone_flag': False
                        }
                    ]
                },
                {
                    'so_number': 'SO-2024-005',
                    'project': projects[1] if len(projects) > 1 else projects[0],
                    'customer': customers[0] if len(customers) > 0 else None,
                    'order_date': today,
                    'status': 'draft',
                    'currency': 'EUR',
                    'notes': 'New order - awaiting confirmation',
                    'lines': [
                        {
                            'product': None,
                            'description': 'Cloud Migration Services',
                            'quantity': 1.0,
                            'unit_price': 40000.00,
                            'milestone_flag': True
                        },
                        {
                            'product': None,
                            'description': 'Post-Migration Support (3 months)',
                            'quantity': 3.0,
                            'unit_price': 5000.00,
                            'milestone_flag': False
                        }
                    ]
                }
            ]
            
            for so_data in sales_orders_data:
                lines_data = so_data.pop('lines', [])
                project = so_data.pop('project')
                customer = so_data.pop('customer')
                
                if not project or not customer:
                    continue
                
                sales_order = SalesOrder(
                    so_number=so_data['so_number'],
                    project_id=project.id,
                    customer_id=customer.id,
                    order_date=so_data['order_date'],
                    status=so_data['status'],
                    currency=so_data['currency'],
                    notes=so_data['notes']
                )
                
                db.session.add(sales_order)
                db.session.flush()
                print(f"  💼 Created sales order: {so_data['so_number']}")
                
                # Add order lines
                total_amount = 0
                for line_data in lines_data:
                    product = line_data.pop('product', None)
                    
                    order_line = SalesOrderLine(
                        sales_order_id=sales_order.id,
                        product_id=product.id if product else None,
                        description=line_data['description'],
                        quantity=line_data['quantity'],
                        unit_price=line_data['unit_price'],
                        milestone_flag=line_data['milestone_flag']
                    )
                    
                    db.session.add(order_line)
                    line_total = float(line_data['quantity']) * float(line_data['unit_price'])
                    total_amount += line_total
                    print(f"    📝 Added line: {line_data['description']} - {line_data['quantity']} x {line_data['unit_price']} = {line_total}")
                
                print(f"    💰 Total order amount: {total_amount} {so_data['currency']}")
            
            db.session.commit()
            print("✅ Sales orders data seeded successfully!")
            
            # Print summary
            print("\n📊 Sales Orders Summary:")
            print(f"  Sales Orders: {SalesOrder.query.count()}")
            print(f"  Sales Order Lines: {SalesOrderLine.query.count()}")
            
            return True
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error seeding sales orders data: {e}")
        import traceback
        traceback.print_exc()
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
                seed_tasks_data()
                seed_sales_orders_data()
        elif command == 'seed':
            seed_sample_data()
            seed_master_data()
            seed_projects_data()
            seed_tasks_data()
            seed_sales_orders_data()
        elif command == 'seed-users':
            seed_sample_data()
        elif command == 'seed-master':
            seed_master_data()
        elif command == 'seed-projects':
            seed_projects_data()
        elif command == 'seed-tasks':
            seed_tasks_data()
        elif command == 'seed-sales':
            seed_sales_orders_data()
        elif command == 'create':
            create_tables()
        else:
            print("❌ Unknown command. Available commands:")
            print("  create         - Create tables only")
            print("  seed           - Seed with all sample data")
            print("  seed-users     - Seed with user data only")
            print("  seed-master    - Seed with master data only")
            print("  seed-projects  - Seed with projects data only")
            print("  seed-tasks     - Seed with tasks data only")
            print("  seed-sales     - Seed with sales orders data only")
            print("  reset          - Drop and recreate tables with all sample data")
    else:
        # Default: create tables and seed all data
        if create_tables():
            seed_sample_data()
            seed_master_data()
            seed_projects_data()
            seed_tasks_data()
            seed_sales_orders_data()
    
    print("\n🎉 Database initialization complete!")
    print("You can now start the Flask application with: python3 app.py")

if __name__ == '__main__':
    main()