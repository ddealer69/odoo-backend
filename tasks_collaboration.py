from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime, date

# Create Blueprint for tasks and collaboration
tasks_collaboration_bp = Blueprint('tasks_collaboration', __name__)

# Database instance (will be initialized from main app)
db = None

def init_tasks_collaboration(database):
    """Initialize the tasks collaboration module with database instance"""
    global db, Task, TaskAssignment, TaskComment, TaskAttachment
    db = database
    
    # =============================================
    # SQLAlchemy Models
    # =============================================
    
    class Task(db.Model):
        __tablename__ = 'tasks'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
        title = Column(String(200), nullable=False)
        description = Column(Text, nullable=True)
        priority = Column(Enum('low', 'medium', 'high', 'urgent', name='task_priority'), 
                         nullable=False, default='medium')
        state = Column(Enum('new', 'in_progress', 'blocked', 'done', name='task_state'), 
                      nullable=False, default='new')
        due_date = Column(Date, nullable=True)
        created_by = Column(Integer, ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
        created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
        updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        # Relationships
        project = relationship('Project', foreign_keys=[project_id])
        creator = relationship('User', foreign_keys=[created_by])
        assignments = relationship('TaskAssignment', back_populates='task', cascade='all, delete-orphan')
        comments = relationship('TaskComment', back_populates='task', cascade='all, delete-orphan')
        attachments = relationship('TaskAttachment', back_populates='task', cascade='all, delete-orphan')
        
        def to_dict(self, include_relations=False):
            task_data = {
                'id': self.id,
                'project_id': self.project_id,
                'title': self.title,
                'description': self.description,
                'priority': self.priority,
                'state': self.state,
                'due_date': self.due_date.isoformat() if self.due_date else None,
                'created_by': self.created_by,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }
            
            if include_relations:
                task_data['project'] = {
                    'id': self.project.id,
                    'project_code': self.project.project_code,
                    'name': self.project.name
                } if self.project else None
                
                task_data['creator'] = {
                    'id': self.creator.id,
                    'email': self.creator.email,
                    'full_name': self.creator.full_name
                } if self.creator else None
                
                task_data['assignees'] = [
                    {
                        'user_id': assignment.user_id,
                        'user': {
                            'id': assignment.user.id,
                            'email': assignment.user.email,
                            'full_name': assignment.user.full_name
                        } if assignment.user else None,
                        'assigned_at': assignment.assigned_at.isoformat() if assignment.assigned_at else None
                    } for assignment in self.assignments
                ]
                
                task_data['comments'] = [
                    {
                        'id': comment.id,
                        'user': {
                            'id': comment.user.id,
                            'email': comment.user.email,
                            'full_name': comment.user.full_name
                        } if comment.user else None,
                        'comment': comment.comment,
                        'created_at': comment.created_at.isoformat() if comment.created_at else None
                    } for comment in self.comments
                ]
                
                task_data['attachments'] = [
                    {
                        'id': attachment.id,
                        'file_name': attachment.file_name,
                        'file_url': attachment.file_url,
                        'uploaded_by': {
                            'id': attachment.uploader.id,
                            'email': attachment.uploader.email,
                            'full_name': attachment.uploader.full_name
                        } if attachment.uploader else None,
                        'created_at': attachment.created_at.isoformat() if attachment.created_at else None
                    } for attachment in self.attachments
                ]
                
                task_data['stats'] = {
                    'assignees_count': len(self.assignments),
                    'comments_count': len(self.comments),
                    'attachments_count': len(self.attachments)
                }
            
            return task_data

    class TaskAssignment(db.Model):
        __tablename__ = 'task_assignments'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
        user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
        assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
        
        __table_args__ = (UniqueConstraint('task_id', 'user_id', name='uq_task_user'),)
        
        # Relationships
        task = relationship('Task', back_populates='assignments')
        user = relationship('User')
        
        def to_dict(self):
            return {
                'id': self.id,
                'task_id': self.task_id,
                'user_id': self.user_id,
                'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
                'task': {
                    'id': self.task.id,
                    'title': self.task.title,
                    'priority': self.task.priority,
                    'state': self.task.state
                } if self.task else None,
                'user': {
                    'id': self.user.id,
                    'email': self.user.email,
                    'full_name': self.user.full_name
                } if self.user else None
            }

    class TaskComment(db.Model):
        __tablename__ = 'task_comments'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
        user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
        comment = Column(Text, nullable=False)
        created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
        
        # Relationships
        task = relationship('Task', back_populates='comments')
        user = relationship('User')
        
        def to_dict(self):
            return {
                'id': self.id,
                'task_id': self.task_id,
                'user_id': self.user_id,
                'comment': self.comment,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'user': {
                    'id': self.user.id,
                    'email': self.user.email,
                    'full_name': self.user.full_name
                } if self.user else None
            }

    class TaskAttachment(db.Model):
        __tablename__ = 'task_attachments'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
        uploaded_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
        file_name = Column(String(255), nullable=False)
        file_url = Column(String(500), nullable=False)
        created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
        
        # Relationships
        task = relationship('Task', back_populates='attachments')
        uploader = relationship('User')
        
        def to_dict(self):
            return {
                'id': self.id,
                'task_id': self.task_id,
                'uploaded_by': self.uploaded_by,
                'file_name': self.file_name,
                'file_url': self.file_url,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'uploader': {
                    'id': self.uploader.id,
                    'email': self.uploader.email,
                    'full_name': self.uploader.full_name
                } if self.uploader else None
            }
    
    return Task, TaskAssignment, TaskComment, TaskAttachment

# =============================================
# Helper Functions
# =============================================

def validate_priority(priority):
    """Validate task priority"""
    valid_priorities = ['low', 'medium', 'high', 'urgent']
    return priority in valid_priorities

def validate_state(state):
    """Validate task state"""
    valid_states = ['new', 'in_progress', 'blocked', 'done']
    return state in valid_states

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
            return jsonify({'error': 'Duplicate entry', 'details': 'User already assigned to this task'}), 400
        elif 'foreign key constraint fails' in str(error.orig):
            return jsonify({'error': 'Reference error', 'details': 'Referenced task, user, or project does not exist'}), 400
        return jsonify({'error': 'Data integrity error', 'details': str(error.orig)}), 400
    elif isinstance(error, SQLAlchemyError):
        return jsonify({'error': 'Database error', 'details': str(error)}), 500
    else:
        return jsonify({'error': message, 'details': str(error)}), 500

# =============================================
# TASK CRUD Operations
# =============================================

@tasks_collaboration_bp.route('/tasks', methods=['GET'])
def get_all_tasks():
    """Get all tasks with optional filtering"""
    try:
        project_id = request.args.get('project_id')
        state = request.args.get('state')
        priority = request.args.get('priority')
        created_by = request.args.get('created_by')
        include_relations = request.args.get('include_relations', 'false').lower() == 'true'
        
        query = Task.query
        
        if project_id:
            query = query.filter(Task.project_id == project_id)
        
        if state and validate_state(state):
            query = query.filter(Task.state == state)
        
        if priority and validate_priority(priority):
            query = query.filter(Task.priority == priority)
        
        if created_by:
            query = query.filter(Task.created_by == created_by)
        
        tasks = query.all()
        
        return jsonify({
            'status': 'success',
            'data': [task.to_dict(include_relations=include_relations) for task in tasks],
            'count': len(tasks),
            'filters': {
                'project_id': project_id,
                'state': state,
                'priority': priority,
                'created_by': created_by
            }
        }), 200
    except Exception as e:
        return handle_error(e, "Failed to fetch tasks")

@tasks_collaboration_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Get single task by ID with all relations"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        return jsonify({
            'status': 'success',
            'data': task.to_dict(include_relations=True)
        }), 200
    except Exception as e:
        return handle_error(e, "Failed to fetch task")

@tasks_collaboration_bp.route('/tasks', methods=['POST'])
def create_task():
    """Create new task"""
    try:
        data = request.get_json()
        
        if not data or 'project_id' not in data or 'title' not in data or 'created_by' not in data:
            return jsonify({'error': 'project_id, title, and created_by are required'}), 400
        
        # Validate priority if provided
        priority = data.get('priority', 'medium')
        if not validate_priority(priority):
            return jsonify({'error': 'Invalid priority. Must be: low, medium, high, or urgent'}), 400
        
        # Validate state if provided
        state = data.get('state', 'new')
        if not validate_state(state):
            return jsonify({'error': 'Invalid state. Must be: new, in_progress, blocked, or done'}), 400
        
        # Validate due_date if provided
        due_date = None
        if data.get('due_date'):
            try:
                due_date = validate_date_string(data['due_date'])
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        
        # Check if project exists
        from projects_teaming import Project
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Check if creator exists
        from user_management import User
        creator = User.query.get(data['created_by'])
        if not creator:
            return jsonify({'error': 'Creator user not found'}), 404
        
        task = Task(
            project_id=data['project_id'],
            title=data['title'],
            description=data.get('description'),
            priority=priority,
            state=state,
            due_date=due_date,
            created_by=data['created_by']
        )
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Task created successfully',
            'data': task.to_dict(include_relations=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to create task")

@tasks_collaboration_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update existing task"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if 'title' in data:
            task.title = data['title']
        
        if 'description' in data:
            task.description = data['description']
        
        if 'priority' in data:
            if not validate_priority(data['priority']):
                return jsonify({'error': 'Invalid priority. Must be: low, medium, high, or urgent'}), 400
            task.priority = data['priority']
        
        if 'state' in data:
            if not validate_state(data['state']):
                return jsonify({'error': 'Invalid state. Must be: new, in_progress, blocked, or done'}), 400
            task.state = data['state']
        
        if 'due_date' in data:
            try:
                task.due_date = validate_date_string(data['due_date'])
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Task updated successfully',
            'data': task.to_dict(include_relations=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to update task")

@tasks_collaboration_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete task"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Get counts before deletion
        assignees_count = len(task.assignments)
        comments_count = len(task.comments)
        attachments_count = len(task.attachments)
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Task deleted successfully (removed {assignees_count} assignments, {comments_count} comments, {attachments_count} attachments)'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to delete task")

# =============================================
# TASK ASSIGNMENT Operations
# =============================================

@tasks_collaboration_bp.route('/tasks/<int:task_id>/assignments', methods=['GET'])
def get_task_assignments(task_id):
    """Get all assignments for a task"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        assignments = TaskAssignment.query.filter_by(task_id=task_id).all()
        
        return jsonify({
            'status': 'success',
            'data': [assignment.to_dict() for assignment in assignments],
            'count': len(assignments)
        }), 200
        
    except Exception as e:
        return handle_error(e, "Failed to fetch task assignments")

@tasks_collaboration_bp.route('/tasks/<int:task_id>/assignments', methods=['POST'])
def assign_user_to_task(task_id):
    """Assign a user to a task"""
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data:
            return jsonify({'error': 'user_id is required'}), 400
        
        user_id = data['user_id']
        
        # Check if task exists
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Check if user exists
        from user_management import User
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if assignment already exists
        existing_assignment = TaskAssignment.query.filter_by(task_id=task_id, user_id=user_id).first()
        if existing_assignment:
            return jsonify({'error': 'User is already assigned to this task'}), 400
        
        assignment = TaskAssignment(
            task_id=task_id,
            user_id=user_id
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'User assigned to task successfully',
            'data': assignment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to assign user to task")

@tasks_collaboration_bp.route('/tasks/<int:task_id>/assignments/<int:user_id>', methods=['DELETE'])
def remove_user_from_task(task_id, user_id):
    """Remove a user from a task"""
    try:
        assignment = TaskAssignment.query.filter_by(task_id=task_id, user_id=user_id).first()
        if not assignment:
            return jsonify({'error': 'Task assignment not found'}), 404
        
        db.session.delete(assignment)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'User removed from task successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to remove user from task")

# =============================================
# TASK COMMENT Operations
# =============================================

@tasks_collaboration_bp.route('/tasks/<int:task_id>/comments', methods=['GET'])
def get_task_comments(task_id):
    """Get all comments for a task"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        comments = TaskComment.query.filter_by(task_id=task_id).order_by(TaskComment.created_at.desc()).all()
        
        return jsonify({
            'status': 'success',
            'data': [comment.to_dict() for comment in comments],
            'count': len(comments)
        }), 200
        
    except Exception as e:
        return handle_error(e, "Failed to fetch task comments")

@tasks_collaboration_bp.route('/tasks/<int:task_id>/comments', methods=['POST'])
def add_task_comment(task_id):
    """Add a comment to a task"""
    try:
        data = request.get_json()
        
        if not data or 'comment' not in data:
            return jsonify({'error': 'comment is required'}), 400
        
        if not data['comment'].strip():
            return jsonify({'error': 'comment cannot be empty'}), 400
        
        # Check if task exists
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Check if user exists (optional)
        user_id = data.get('user_id')
        if user_id:
            from user_management import User
            user = User.query.get(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
        
        comment = TaskComment(
            task_id=task_id,
            user_id=user_id,
            comment=data['comment']
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Comment added successfully',
            'data': comment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to add comment")

@tasks_collaboration_bp.route('/tasks/<int:task_id>/comments/<int:comment_id>', methods=['DELETE'])
def delete_task_comment(task_id, comment_id):
    """Delete a comment from a task"""
    try:
        comment = TaskComment.query.filter_by(id=comment_id, task_id=task_id).first()
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        db.session.delete(comment)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Comment deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to delete comment")

# =============================================
# TASK ATTACHMENT Operations
# =============================================

@tasks_collaboration_bp.route('/tasks/<int:task_id>/attachments', methods=['GET'])
def get_task_attachments(task_id):
    """Get all attachments for a task"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        attachments = TaskAttachment.query.filter_by(task_id=task_id).order_by(TaskAttachment.created_at.desc()).all()
        
        return jsonify({
            'status': 'success',
            'data': [attachment.to_dict() for attachment in attachments],
            'count': len(attachments)
        }), 200
        
    except Exception as e:
        return handle_error(e, "Failed to fetch task attachments")

@tasks_collaboration_bp.route('/tasks/<int:task_id>/attachments', methods=['POST'])
def upload_task_attachment(task_id):
    """Upload an attachment to a task"""
    try:
        data = request.get_json()
        
        if not data or 'file_name' not in data or 'file_url' not in data:
            return jsonify({'error': 'file_name and file_url are required'}), 400
        
        # Check if task exists
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Check if user exists (optional)
        uploaded_by = data.get('uploaded_by')
        if uploaded_by:
            from user_management import User
            user = User.query.get(uploaded_by)
            if not user:
                return jsonify({'error': 'User not found'}), 404
        
        attachment = TaskAttachment(
            task_id=task_id,
            uploaded_by=uploaded_by,
            file_name=data['file_name'],
            file_url=data['file_url']
        )
        
        db.session.add(attachment)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Attachment uploaded successfully',
            'data': attachment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to upload attachment")

@tasks_collaboration_bp.route('/tasks/<int:task_id>/attachments/<int:attachment_id>', methods=['DELETE'])
def delete_task_attachment(task_id, attachment_id):
    """Delete an attachment from a task"""
    try:
        attachment = TaskAttachment.query.filter_by(id=attachment_id, task_id=task_id).first()
        if not attachment:
            return jsonify({'error': 'Attachment not found'}), 404
        
        db.session.delete(attachment)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Attachment deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to delete attachment")

# =============================================
# Additional Endpoints
# =============================================

@tasks_collaboration_bp.route('/projects/<int:project_id>/tasks', methods=['GET'])
def get_project_tasks(project_id):
    """Get all tasks for a project"""
    try:
        from projects_teaming import Project
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        state = request.args.get('state')
        priority = request.args.get('priority')
        
        query = Task.query.filter_by(project_id=project_id)
        
        if state and validate_state(state):
            query = query.filter(Task.state == state)
        
        if priority and validate_priority(priority):
            query = query.filter(Task.priority == priority)
        
        tasks = query.all()
        
        return jsonify({
            'status': 'success',
            'data': [task.to_dict(include_relations=True) for task in tasks],
            'count': len(tasks),
            'project': {
                'id': project.id,
                'project_code': project.project_code,
                'name': project.name
            }
        }), 200
        
    except Exception as e:
        return handle_error(e, "Failed to fetch project tasks")

@tasks_collaboration_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    """Get all tasks assigned to a user"""
    try:
        from user_management import User
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get tasks assigned to user
        assigned_tasks = db.session.query(Task).join(TaskAssignment).filter(TaskAssignment.user_id == user_id).all()
        
        # Get tasks created by user
        created_tasks = Task.query.filter_by(created_by=user_id).all()
        
        return jsonify({
            'status': 'success',
            'data': {
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name
                },
                'assigned_tasks': [task.to_dict(include_relations=False) for task in assigned_tasks],
                'created_tasks': [task.to_dict(include_relations=False) for task in created_tasks],
                'assigned_count': len(assigned_tasks),
                'created_count': len(created_tasks)
            }
        }), 200
        
    except Exception as e:
        return handle_error(e, "Failed to fetch user tasks")

@tasks_collaboration_bp.route('/tasks/stats', methods=['GET'])
def get_task_statistics():
    """Get task statistics"""
    try:
        total_tasks = Task.query.count()
        
        # Count by state
        new_tasks = Task.query.filter_by(state='new').count()
        in_progress_tasks = Task.query.filter_by(state='in_progress').count()
        blocked_tasks = Task.query.filter_by(state='blocked').count()
        done_tasks = Task.query.filter_by(state='done').count()
        
        # Count by priority
        low_priority = Task.query.filter_by(priority='low').count()
        medium_priority = Task.query.filter_by(priority='medium').count()
        high_priority = Task.query.filter_by(priority='high').count()
        urgent_priority = Task.query.filter_by(priority='urgent').count()
        
        total_assignments = TaskAssignment.query.count()
        total_comments = TaskComment.query.count()
        total_attachments = TaskAttachment.query.count()
        
        # Overdue tasks
        today = date.today()
        overdue_tasks = Task.query.filter(
            Task.due_date < today,
            Task.state != 'done'
        ).count()
        
        return jsonify({
            'status': 'success',
            'data': {
                'tasks': {
                    'total': total_tasks,
                    'by_state': {
                        'new': new_tasks,
                        'in_progress': in_progress_tasks,
                        'blocked': blocked_tasks,
                        'done': done_tasks
                    },
                    'by_priority': {
                        'low': low_priority,
                        'medium': medium_priority,
                        'high': high_priority,
                        'urgent': urgent_priority
                    },
                    'overdue': overdue_tasks
                },
                'collaboration': {
                    'total_assignments': total_assignments,
                    'total_comments': total_comments,
                    'total_attachments': total_attachments
                }
            }
        }), 200
        
    except Exception as e:
        return handle_error(e, "Failed to fetch statistics")
