from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DECIMAL, Date, DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime, date

# Create Blueprint for projects and teaming
projects_teaming_bp = Blueprint('projects_teaming', __name__)

# Database instance (will be initialized from main app)
db = None

def init_projects_teaming(database):
    """Initialize the projects teaming module with database instance"""
    global db, Project, ProjectMember
    db = database
    
    # =============================================
    # SQLAlchemy Models
    # =============================================
    
    class Project(db.Model):
        __tablename__ = 'projects'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        project_code = Column(String(40), nullable=False, unique=True)
        name = Column(String(180), nullable=False)
        description = Column(Text, nullable=True)
        project_manager_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
        start_date = Column(Date, nullable=True)
        end_date = Column(Date, nullable=True)
        status = Column(Enum('planned', 'in_progress', 'completed', 'on_hold', 'cancelled', name='project_status'), 
                       nullable=False, default='planned')
        budget_amount = Column(DECIMAL(12, 2), nullable=True)
        created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
        updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        # Relationships
        project_manager = relationship('User', foreign_keys=[project_manager_id])
        members = relationship('ProjectMember', back_populates='project', cascade='all, delete-orphan')
        
        def to_dict(self, include_manager=False, include_members=False):
            project_data = {
                'id': self.id,
                'project_code': self.project_code,
                'name': self.name,
                'description': self.description,
                'project_manager_id': self.project_manager_id,
                'start_date': self.start_date.isoformat() if self.start_date else None,
                'end_date': self.end_date.isoformat() if self.end_date else None,
                'status': self.status,
                'budget_amount': float(self.budget_amount) if self.budget_amount else None,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }
            
            if include_manager and self.project_manager:
                project_data['project_manager'] = {
                    'id': self.project_manager.id,
                    'email': self.project_manager.email,
                    'full_name': self.project_manager.full_name,
                    'hourly_rate': float(self.project_manager.hourly_rate)
                }
            
            if include_members:
                project_data['members'] = [
                    {
                        'user_id': pm.user_id,
                        'user': {
                            'id': pm.user.id,
                            'email': pm.user.email,
                            'full_name': pm.user.full_name,
                            'hourly_rate': float(pm.user.hourly_rate)
                        },
                        'role_in_project': pm.role_in_project,
                        'added_at': pm.added_at.isoformat() if pm.added_at else None
                    } for pm in self.members
                ]
                project_data['member_count'] = len(self.members)
            
            return project_data

    class ProjectMember(db.Model):
        __tablename__ = 'project_members'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
        user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
        role_in_project = Column(String(80), nullable=True)
        added_at = Column(DateTime, nullable=False, default=datetime.utcnow)
        
        __table_args__ = (UniqueConstraint('project_id', 'user_id', name='uq_project_user'),)
        
        # Relationships
        project = relationship('Project', back_populates='members')
        user = relationship('User')
        
        def to_dict(self):
            return {
                'id': self.id,
                'project_id': self.project_id,
                'user_id': self.user_id,
                'role_in_project': self.role_in_project,
                'added_at': self.added_at.isoformat() if self.added_at else None,
                'project': {
                    'id': self.project.id,
                    'project_code': self.project.project_code,
                    'name': self.project.name,
                    'status': self.project.status
                } if self.project else None,
                'user': {
                    'id': self.user.id,
                    'email': self.user.email,
                    'full_name': self.user.full_name
                } if self.user else None
            }
    
    return Project, ProjectMember

# =============================================
# Helper Functions
# =============================================

def validate_project_status(status):
    """Validate project status"""
    valid_statuses = ['planned', 'in_progress', 'completed', 'on_hold', 'cancelled']
    return status in valid_statuses

def validate_date_string(date_string):
    """Validate and parse date string"""
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("Invalid date format. Use YYYY-MM-DD")

def handle_error(error, message="An error occurred"):
    """Standard error handler"""
    if isinstance(error, IntegrityError):
        if 'Duplicate entry' in str(error.orig):
            return jsonify({'error': 'Duplicate entry', 'details': 'Project code already exists or user already assigned'}), 400
        elif 'foreign key constraint fails' in str(error.orig):
            return jsonify({'error': 'Reference error', 'details': 'Referenced user or project does not exist'}), 400
        return jsonify({'error': 'Data integrity error', 'details': str(error.orig)}), 400
    elif isinstance(error, SQLAlchemyError):
        return jsonify({'error': 'Database error', 'details': str(error)}), 500
    else:
        return jsonify({'error': message, 'details': str(error)}), 500

# =============================================
# PROJECT CRUD Operations
# =============================================

@projects_teaming_bp.route('/projects', methods=['GET'])
def get_all_projects():
    """Get all projects with optional filtering"""
    try:
        # Get query parameters
        status = request.args.get('status')
        search = request.args.get('search')
        include_manager = request.args.get('include_manager', 'false').lower() == 'true'
        include_members = request.args.get('include_members', 'false').lower() == 'true'
        
        query = Project.query
        
        # Filter by status if provided
        if status and validate_project_status(status):
            query = query.filter(Project.status == status)
        
        # Search by name or project code if provided
        if search:
            query = query.filter(
                db.or_(
                    Project.name.ilike(f'%{search}%'),
                    Project.project_code.ilike(f'%{search}%')
                )
            )
        
        projects = query.all()
        
        return jsonify({
            'status': 'success',
            'data': [project.to_dict(include_manager=include_manager, include_members=include_members) 
                    for project in projects],
            'count': len(projects),
            'filters': {
                'status': status,
                'search': search
            }
        }), 200
    except Exception as e:
        return handle_error(e, "Failed to fetch projects")

@projects_teaming_bp.route('/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Get single project by ID with manager and members"""
    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        return jsonify({
            'status': 'success',
            'data': project.to_dict(include_manager=True, include_members=True)
        }), 200
    except Exception as e:
        return handle_error(e, "Failed to fetch project")

@projects_teaming_bp.route('/projects', methods=['POST'])
def create_project():
    """Create new project"""
    try:
        data = request.get_json()
        
        if not data or 'project_code' not in data or 'name' not in data:
            return jsonify({'error': 'Project code and name are required'}), 400
        
        # Validate status if provided
        status = data.get('status', 'planned')
        if not validate_project_status(status):
            return jsonify({'error': 'Invalid status. Must be: planned, in_progress, completed, on_hold, or cancelled'}), 400
        
        # Validate dates if provided
        start_date = None
        end_date = None
        
        try:
            if data.get('start_date'):
                start_date = validate_date_string(data['start_date'])
            if data.get('end_date'):
                end_date = validate_date_string(data['end_date'])
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        # Validate date logic
        if start_date and end_date and start_date > end_date:
            return jsonify({'error': 'End date must be after start date'}), 400
        
        # Validate budget if provided
        budget_amount = data.get('budget_amount')
        if budget_amount is not None:
            try:
                budget_amount = float(budget_amount)
                if budget_amount < 0:
                    return jsonify({'error': 'Budget amount must be non-negative'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid budget amount format'}), 400
        
        # Check if project manager exists (if provided)
        project_manager_id = data.get('project_manager_id')
        if project_manager_id:
            from user_management import User
            manager = User.query.get(project_manager_id)
            if not manager:
                return jsonify({'error': 'Project manager not found'}), 404
        
        project = Project(
            project_code=data['project_code'],
            name=data['name'],
            description=data.get('description'),
            project_manager_id=project_manager_id,
            start_date=start_date,
            end_date=end_date,
            status=status,
            budget_amount=budget_amount
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Project created successfully',
            'data': project.to_dict(include_manager=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to create project")

@projects_teaming_bp.route('/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """Update existing project"""
    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update fields if provided
        if 'project_code' in data:
            # Check if project code already exists for another project
            existing_project = Project.query.filter_by(project_code=data['project_code']).first()
            if existing_project and existing_project.id != project_id:
                return jsonify({'error': 'Project code already exists'}), 400
            project.project_code = data['project_code']
        
        if 'name' in data:
            project.name = data['name']
        
        if 'description' in data:
            project.description = data['description']
        
        if 'project_manager_id' in data:
            if data['project_manager_id']:
                from user_management import User
                manager = User.query.get(data['project_manager_id'])
                if not manager:
                    return jsonify({'error': 'Project manager not found'}), 404
            project.project_manager_id = data['project_manager_id']
        
        if 'status' in data:
            if not validate_project_status(data['status']):
                return jsonify({'error': 'Invalid status. Must be: planned, in_progress, completed, on_hold, or cancelled'}), 400
            project.status = data['status']
        
        if 'start_date' in data:
            try:
                project.start_date = validate_date_string(data['start_date'])
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        
        if 'end_date' in data:
            try:
                project.end_date = validate_date_string(data['end_date'])
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        
        # Validate date logic if both dates are set
        if project.start_date and project.end_date and project.start_date > project.end_date:
            return jsonify({'error': 'End date must be after start date'}), 400
        
        if 'budget_amount' in data:
            if data['budget_amount'] is not None:
                try:
                    budget_amount = float(data['budget_amount'])
                    if budget_amount < 0:
                        return jsonify({'error': 'Budget amount must be non-negative'}), 400
                    project.budget_amount = budget_amount
                except (ValueError, TypeError):
                    return jsonify({'error': 'Invalid budget amount format'}), 400
            else:
                project.budget_amount = None
        
        project.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Project updated successfully',
            'data': project.to_dict(include_manager=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to update project")

@projects_teaming_bp.route('/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete project"""
    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Get member count before deletion
        member_count = len(project.members)
        
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Project deleted successfully (removed {member_count} member assignments)'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to delete project")

# =============================================
# PROJECT MEMBER Operations
# =============================================

@projects_teaming_bp.route('/projects/<int:project_id>/members', methods=['GET'])
def get_project_members(project_id):
    """Get all members of a project"""
    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        members = ProjectMember.query.filter_by(project_id=project_id).all()
        
        return jsonify({
            'status': 'success',
            'data': [member.to_dict() for member in members],
            'count': len(members),
            'project': {
                'id': project.id,
                'project_code': project.project_code,
                'name': project.name,
                'status': project.status
            }
        }), 200
        
    except Exception as e:
        return handle_error(e, "Failed to fetch project members")

@projects_teaming_bp.route('/projects/<int:project_id>/members', methods=['POST'])
def assign_member_to_project(project_id):
    """Assign a user to a project"""
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data:
            return jsonify({'error': 'user_id is required'}), 400
        
        user_id = data['user_id']
        
        # Check if project exists
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Check if user exists
        from user_management import User
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if assignment already exists
        existing_assignment = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
        if existing_assignment:
            return jsonify({'error': 'User is already assigned to this project'}), 400
        
        project_member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role_in_project=data.get('role_in_project')
        )
        
        db.session.add(project_member)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Member assigned successfully',
            'data': project_member.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to assign member")

@projects_teaming_bp.route('/projects/<int:project_id>/members/<int:user_id>', methods=['PUT'])
def update_project_member(project_id, user_id):
    """Update project member role"""
    try:
        project_member = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
        if not project_member:
            return jsonify({'error': 'Project member assignment not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if 'role_in_project' in data:
            project_member.role_in_project = data['role_in_project']
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Member role updated successfully',
            'data': project_member.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to update member")

@projects_teaming_bp.route('/projects/<int:project_id>/members/<int:user_id>', methods=['DELETE'])
def remove_member_from_project(project_id, user_id):
    """Remove a user from a project"""
    try:
        project_member = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
        if not project_member:
            return jsonify({'error': 'Project member assignment not found'}), 404
        
        db.session.delete(project_member)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Member removed from project successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to remove member")

# =============================================
# Additional Endpoints
# =============================================

@projects_teaming_bp.route('/users/<int:user_id>/projects', methods=['GET'])
def get_user_projects(user_id):
    """Get all projects a user is involved in"""
    try:
        from user_management import User
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get projects where user is a member
        member_projects = db.session.query(Project).join(ProjectMember).filter(ProjectMember.user_id == user_id).all()
        
        # Get projects where user is project manager
        managed_projects = Project.query.filter_by(project_manager_id=user_id).all()
        
        # Combine and remove duplicates
        all_projects = list({p.id: p for p in member_projects + managed_projects}.values())
        
        return jsonify({
            'status': 'success',
            'data': {
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name
                },
                'projects': [project.to_dict(include_manager=True) for project in all_projects],
                'managed_projects': len(managed_projects),
                'member_projects': len(member_projects),
                'total_projects': len(all_projects)
            }
        }), 200
        
    except Exception as e:
        return handle_error(e, "Failed to fetch user projects")

@projects_teaming_bp.route('/project-members', methods=['GET'])
def get_all_project_members():
    """Get all project member assignments"""
    try:
        project_id = request.args.get('project_id')
        user_id = request.args.get('user_id')
        
        query = ProjectMember.query
        
        if project_id:
            query = query.filter(ProjectMember.project_id == project_id)
        
        if user_id:
            query = query.filter(ProjectMember.user_id == user_id)
        
        members = query.all()
        
        return jsonify({
            'status': 'success',
            'data': [member.to_dict() for member in members],
            'count': len(members)
        }), 200
        
    except Exception as e:
        return handle_error(e, "Failed to fetch project members")

@projects_teaming_bp.route('/projects/stats', methods=['GET'])
def get_project_statistics():
    """Get project statistics"""
    try:
        total_projects = Project.query.count()
        planned_projects = Project.query.filter_by(status='planned').count()
        in_progress_projects = Project.query.filter_by(status='in_progress').count()
        completed_projects = Project.query.filter_by(status='completed').count()
        on_hold_projects = Project.query.filter_by(status='on_hold').count()
        cancelled_projects = Project.query.filter_by(status='cancelled').count()
        
        total_assignments = ProjectMember.query.count()
        projects_with_members = db.session.query(ProjectMember.project_id).distinct().count()
        
        return jsonify({
            'status': 'success',
            'data': {
                'projects': {
                    'total': total_projects,
                    'by_status': {
                        'planned': planned_projects,
                        'in_progress': in_progress_projects,
                        'completed': completed_projects,
                        'on_hold': on_hold_projects,
                        'cancelled': cancelled_projects
                    }
                },
                'assignments': {
                    'total_assignments': total_assignments,
                    'projects_with_members': projects_with_members,
                    'projects_without_members': total_projects - projects_with_members
                }
            }
        }), 200
        
    except Exception as e:
        return handle_error(e, "Failed to fetch statistics")