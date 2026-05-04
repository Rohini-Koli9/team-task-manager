from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Database configuration - use PostgreSQL on Railway, SQLite locally
print("=== ENVIRONMENT VARIABLES ===")
for key, value in os.environ.items():
    if 'database' in key.lower() or 'postgres' in key.lower() or 'sql' in key.lower():
        # Mask password for security
        masked = value[:30] + '...' if len(value) > 30 else value
        print(f"{key}: {masked}")
print("===========================")

database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    # Railway uses postgres:// but SQLAlchemy requires postgresql://
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
    print(f"Converted postgres:// to postgresql://")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///teamtask.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)

# ==================== MODELS ====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    projects = db.relationship('ProjectMember', back_populates='user', cascade='all, delete-orphan')
    created_tasks = db.relationship('Task', foreign_keys='Task.created_by', back_populates='creator')
    assigned_tasks = db.relationship('Task', foreign_keys='Task.assigned_to', back_populates='assignee')
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'created_at': self.created_at.isoformat()
        }

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    members = db.relationship('ProjectMember', back_populates='project', cascade='all, delete-orphan')
    tasks = db.relationship('Task', back_populates='project', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by
        }

class ProjectMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), default='member')  # 'admin' or 'member'
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', back_populates='members')
    user = db.relationship('User', back_populates='projects')
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'user': self.user.to_dict(),
            'role': self.role,
            'joined_at': self.joined_at.isoformat()
        }

class Task(db.Model):
    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    
    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default=STATUS_PENDING)
    priority = db.Column(db.String(20), default=PRIORITY_MEDIUM)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', back_populates='tasks')
    assignee = db.relationship('User', foreign_keys=[assigned_to], back_populates='assigned_tasks')
    creator = db.relationship('User', foreign_keys=[created_by], back_populates='created_tasks')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'project_id': self.project_id,
            'assigned_to': self.assigned_to,
            'assignee': self.assignee.to_dict() if self.assignee else None,
            'created_by': self.created_by,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_overdue': self.due_date and self.due_date < datetime.utcnow() and self.status != self.STATUS_COMPLETED
        }

# ==================== AUTHENTICATION ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validation
    if not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'error': 'Email, password, and name are required'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    if len(data['password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    # Create user
    hashed_password = generate_password_hash(data['password'])
    user = User(
        email=data['email'],
        password=hashed_password,
        name=data['name']
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Create token
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'User registered successfully',
        'token': access_token,
        'user': user.to_dict()
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'Login successful',
        'token': access_token,
        'user': user.to_dict()
    }), 200

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200

# ==================== PROJECTS ====================

@app.route('/api/projects', methods=['GET'])
@jwt_required()
def get_projects():
    try:
        user_id = get_jwt_identity()
        
        # Get projects where user is a member
        member_projects = ProjectMember.query.filter_by(user_id=user_id).all()
        project_ids = [mp.project_id for mp in member_projects]
        
        if not project_ids:
            return jsonify({'projects': []}), 200
        
        projects = Project.query.filter(Project.id.in_(project_ids)).all()
        
        result = []
        for project in projects:
            p_dict = project.to_dict()
            # Get user's role in this project
            membership = ProjectMember.query.filter_by(project_id=project.id, user_id=user_id).first()
            p_dict['my_role'] = membership.role if membership else 'member'
            p_dict['member_count'] = len(project.members)
            result.append(p_dict)
        
        return jsonify({'projects': result}), 200
    except Exception as e:
        import traceback
        print(f"GET PROJECTS ERROR: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects', methods=['POST'])
@jwt_required()
def create_project():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({'error': 'Project name is required'}), 400
        
        # Create project
        project = Project(
            name=data['name'],
            description=data.get('description', ''),
            created_by=user_id
        )
        
        db.session.add(project)
        db.session.flush()  # Get project.id
        
        # Add creator as admin
        member = ProjectMember(
            project_id=project.id,
            user_id=user_id,
            role='admin'
        )
        db.session.add(member)
        db.session.commit()
        
        return jsonify({
            'message': 'Project created successfully',
            'project': project.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"CREATE PROJECT ERROR: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    user_id = get_jwt_identity()
    
    # Check membership
    membership = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
    if not membership:
        return jsonify({'error': 'Access denied or project not found'}), 403
    
    project = Project.query.get_or_404(project_id)
    
    result = project.to_dict()
    result['my_role'] = membership.role
    result['members'] = [m.to_dict() for m in project.members]
    result['tasks'] = [t.to_dict() for t in project.tasks]
    
    return jsonify({'project': result}), 200

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    user_id = get_jwt_identity()
    
    # Check admin access
    membership = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
    if not membership or membership.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    if data.get('name'):
        project.name = data['name']
    if data.get('description') is not None:
        project.description = data['description']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Project updated successfully',
        'project': project.to_dict()
    }), 200

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    user_id = get_jwt_identity()
    
    # Check admin access
    membership = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
    if not membership or membership.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    project = Project.query.get_or_404(project_id)
    
    db.session.delete(project)
    db.session.commit()
    
    return jsonify({'message': 'Project deleted successfully'}), 200

# ==================== PROJECT MEMBERS ====================

@app.route('/api/projects/<int:project_id>/members', methods=['POST'])
@jwt_required()
def add_member(project_id):
    user_id = get_jwt_identity()
    
    # Check admin access
    membership = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
    if not membership or membership.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    
    if not data.get('email'):
        return jsonify({'error': 'Email is required'}), 400
    
    # Find user by email
    new_member = User.query.filter_by(email=data['email']).first()
    if not new_member:
        return jsonify({'error': 'User not found with this email'}), 404
    
    # Check if already a member
    existing = ProjectMember.query.filter_by(project_id=project_id, user_id=new_member.id).first()
    if existing:
        return jsonify({'error': 'User is already a member'}), 409
    
    member = ProjectMember(
        project_id=project_id,
        user_id=new_member.id,
        role=data.get('role', 'member')
    )
    
    db.session.add(member)
    db.session.commit()
    
    return jsonify({
        'message': 'Member added successfully',
        'member': member.to_dict()
    }), 201

@app.route('/api/projects/<int:project_id>/members/<int:member_id>', methods=['DELETE'])
@jwt_required()
def remove_member(project_id, member_id):
    user_id = get_jwt_identity()
    
    # Check admin access
    membership = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
    if not membership or membership.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    member = ProjectMember.query.filter_by(id=member_id, project_id=project_id).first_or_404()
    
    db.session.delete(member)
    db.session.commit()
    
    return jsonify({'message': 'Member removed successfully'}), 200

# ==================== TASKS ====================

@app.route('/api/projects/<int:project_id>/tasks', methods=['GET'])
@jwt_required()
def get_tasks(project_id):
    user_id = get_jwt_identity()
    
    # Check membership
    membership = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
    if not membership:
        return jsonify({'error': 'Access denied'}), 403
    
    # Filter options
    status = request.args.get('status')
    assigned_to = request.args.get('assigned_to')
    
    query = Task.query.filter_by(project_id=project_id)
    
    if status:
        query = query.filter_by(status=status)
    if assigned_to:
        query = query.filter_by(assigned_to=assigned_to)
    
    tasks = query.order_by(Task.created_at.desc()).all()
    
    return jsonify({'tasks': [t.to_dict() for t in tasks]}), 200

@app.route('/api/projects/<int:project_id>/tasks', methods=['POST'])
@jwt_required()
def create_task(project_id):
    user_id = get_jwt_identity()
    
    # Check membership
    membership = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
    if not membership:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    if not data.get('title'):
        return jsonify({'error': 'Task title is required'}), 400
    
    # Parse due date
    due_date = None
    if data.get('due_date'):
        try:
            due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00')).replace(tzinfo=None)
        except:
            return jsonify({'error': 'Invalid due date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
    
    task = Task(
        title=data['title'],
        description=data.get('description', ''),
        status=data.get('status', Task.STATUS_PENDING),
        priority=data.get('priority', Task.PRIORITY_MEDIUM),
        project_id=project_id,
        assigned_to=data.get('assigned_to'),
        created_by=user_id,
        due_date=due_date
    )
    
    db.session.add(task)
    db.session.commit()
    
    return jsonify({
        'message': 'Task created successfully',
        'task': task.to_dict()
    }), 201

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    user_id = get_jwt_identity()
    
    task = Task.query.get_or_404(task_id)
    
    # Check membership
    membership = ProjectMember.query.filter_by(project_id=task.project_id, user_id=user_id).first()
    if not membership:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({'task': task.to_dict()}), 200

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    user_id = get_jwt_identity()
    
    task = Task.query.get_or_404(task_id)
    
    # Check membership
    membership = ProjectMember.query.filter_by(project_id=task.project_id, user_id=user_id).first()
    if not membership:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    # Only admin or task creator can update all fields
    can_edit_all = membership.role == 'admin' or task.created_by == user_id
    
    if can_edit_all:
        if data.get('title'):
            task.title = data['title']
        if data.get('description') is not None:
            task.description = data['description']
        if data.get('priority'):
            task.priority = data['priority']
        if data.get('assigned_to') is not None:
            task.assigned_to = data['assigned_to']
        if data.get('due_date'):
            try:
                task.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00')).replace(tzinfo=None)
            except:
                return jsonify({'error': 'Invalid due date format'}), 400
    
    # Anyone can update status (for collaboration)
    if data.get('status'):
        valid_statuses = [Task.STATUS_PENDING, Task.STATUS_IN_PROGRESS, Task.STATUS_COMPLETED]
        if data['status'] not in valid_statuses:
            return jsonify({'error': f'Status must be one of: {valid_statuses}'}), 400
        task.status = data['status']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Task updated successfully',
        'task': task.to_dict()
    }), 200

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    user_id = get_jwt_identity()
    
    task = Task.query.get_or_404(task_id)
    
    # Check admin or creator
    membership = ProjectMember.query.filter_by(project_id=task.project_id, user_id=user_id).first()
    if not membership:
        return jsonify({'error': 'Access denied'}), 403
    
    if membership.role != 'admin' and task.created_by != user_id:
        return jsonify({'error': 'Only admin or task creator can delete'}), 403
    
    db.session.delete(task)
    db.session.commit()
    
    return jsonify({'message': 'Task deleted successfully'}), 200

# ==================== DASHBOARD ====================

@app.route('/api/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    try:
        user_id = get_jwt_identity()
        
        # Get user's project IDs
        memberships = ProjectMember.query.filter_by(user_id=user_id).all()
        project_ids = [m.project_id for m in memberships]
        
        if not project_ids:
            return jsonify({
                'stats': {
                    'total_projects': 0,
                    'total_tasks': 0,
                    'pending_tasks': 0,
                    'in_progress_tasks': 0,
                    'completed_tasks': 0,
                    'overdue_tasks': 0,
                    'tasks_assigned_to_me': 0
                },
                'recent_tasks': [],
                'overdue_tasks': []
            }), 200
        
        # Calculate stats
        all_tasks = Task.query.filter(Task.project_id.in_(project_ids)).all()
        
        total_tasks = len(all_tasks)
        pending = sum(1 for t in all_tasks if t.status == Task.STATUS_PENDING)
        in_progress = sum(1 for t in all_tasks if t.status == Task.STATUS_IN_PROGRESS)
        completed = sum(1 for t in all_tasks if t.status == Task.STATUS_COMPLETED)
        overdue = sum(1 for t in all_tasks if t.due_date and t.due_date < datetime.utcnow() and t.status != Task.STATUS_COMPLETED)
        my_tasks = sum(1 for t in all_tasks if t.assigned_to == user_id)
        
        # Recent tasks (last 10)
        recent_tasks = Task.query.filter(
            Task.project_id.in_(project_ids)
        ).order_by(Task.created_at.desc()).limit(10).all()
        
        # Overdue tasks list
        overdue_tasks_list = [t for t in all_tasks if t.due_date and t.due_date < datetime.utcnow() and t.status != Task.STATUS_COMPLETED]
        overdue_tasks_list.sort(key=lambda x: x.due_date)
        
        return jsonify({
            'stats': {
                'total_projects': len(project_ids),
                'total_tasks': total_tasks,
                'pending_tasks': pending,
                'in_progress_tasks': in_progress,
                'completed_tasks': completed,
                'overdue_tasks': overdue,
                'tasks_assigned_to_me': my_tasks
            },
            'recent_tasks': [t.to_dict() for t in recent_tasks],
            'overdue_tasks': [t.to_dict() for t in overdue_tasks_list[:10]]
        }), 200
    except Exception as e:
        import traceback
        print(f"Dashboard error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': 'Failed to load dashboard'}), 500

# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200

@app.route('/')
def index():
    return app.send_static_file('index.html')

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': f'Internal server error: {str(error)}'}), 500

@app.errorhandler(422)
def unprocessable_entity(error):
    return jsonify({'error': f'Unprocessable entity: {str(error)}'}), 422

# ==================== INIT DATABASE ====================

with app.app_context():
    try:
        print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
        db.create_all()
        print("Database tables created successfully!")
    except Exception as e:
        import traceback
        print(f"DATABASE INIT ERROR: {str(e)}")
        print(traceback.format_exc())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
