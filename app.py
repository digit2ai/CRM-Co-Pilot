# app.py - Main Flask Application (Fixed for Flask 2.3+)
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import json

app = Flask(__name__)

# Production configuration
if os.environ.get('DATABASE_URL'):
    # Production (Render with PostgreSQL)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
else:
    # Development (Local with SQLite)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project_manager.db'

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Database Models
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sprints = db.relationship('Sprint', backref='project', lazy=True, cascade='all, delete-orphan')

class Sprint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    goal = db.Column(db.Text)
    duration = db.Column(db.String(100))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='planned')
    story_points = db.Column(db.Integer, default=0)
    
    epics = db.relationship('Epic', backref='sprint', lazy=True, cascade='all, delete-orphan')

class Epic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sprint_id = db.Column(db.Integer, db.ForeignKey('sprint.id'), nullable=False)
    epic_id = db.Column(db.String(10))  # e.g., "1.1"
    name = db.Column(db.String(200), nullable=False)
    goal = db.Column(db.Text)
    
    user_stories = db.relationship('UserStory', backref='epic', lazy=True, cascade='all, delete-orphan')

class UserStory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    epic_id = db.Column(db.Integer, db.ForeignKey('epic.id'), nullable=False)
    story_id = db.Column(db.String(20))  # e.g., "US-001"
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    acceptance_criteria = db.Column(db.Text)  # JSON string
    story_points = db.Column(db.Integer, default=1)
    status = db.Column(db.String(50), default='todo')
    assignee = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Risk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(50), default='medium')
    mitigation = db.Column(db.Text)
    status = db.Column(db.String(50), default='open')

# Routes
@app.route('/')
def dashboard():
    projects = Project.query.all()
    return render_template('dashboard.html', projects=projects)

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project_detail.html', project=project)

# API Routes for CRUD operations

# Projects
@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'status': p.status,
        'start_date': p.start_date.isoformat() if p.start_date else None,
        'end_date': p.end_date.isoformat() if p.end_date else None,
        'sprint_count': len(p.sprints),
        'total_story_points': sum(s.story_points for s in p.sprints)
    } for p in projects])

@app.route('/api/projects', methods=['POST'])
def create_project():
    data = request.get_json()
    project = Project(
        name=data['name'],
        description=data.get('description', ''),
        status=data.get('status', 'active')
    )
    db.session.add(project)
    db.session.commit()
    return jsonify({'id': project.id, 'message': 'Project created successfully'}), 201

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    project.name = data.get('name', project.name)
    project.description = data.get('description', project.description)
    project.status = data.get('status', project.status)
    
    db.session.commit()
    return jsonify({'message': 'Project updated successfully'})

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted successfully'})

# Sprints
@app.route('/api/projects/<int:project_id>/sprints', methods=['GET'])
def get_sprints(project_id):
    sprints = Sprint.query.filter_by(project_id=project_id).all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'goal': s.goal,
        'duration': s.duration,
        'status': s.status,
        'story_points': s.story_points,
        'epic_count': len(s.epics),
        'start_date': s.start_date.isoformat() if s.start_date else None,
        'end_date': s.end_date.isoformat() if s.end_date else None
    } for s in sprints])

@app.route('/api/sprints', methods=['POST'])
def create_sprint():
    data = request.get_json()
    sprint = Sprint(
        project_id=data['project_id'],
        name=data['name'],
        goal=data.get('goal', ''),
        duration=data.get('duration', ''),
        status=data.get('status', 'planned'),
        story_points=data.get('story_points', 0)
    )
    db.session.add(sprint)
    db.session.commit()
    return jsonify({'id': sprint.id, 'message': 'Sprint created successfully'}), 201

@app.route('/api/sprints/<int:sprint_id>', methods=['PUT'])
def update_sprint(sprint_id):
    sprint = Sprint.query.get_or_404(sprint_id)
    data = request.get_json()
    
    sprint.name = data.get('name', sprint.name)
    sprint.goal = data.get('goal', sprint.goal)
    sprint.duration = data.get('duration', sprint.duration)
    sprint.status = data.get('status', sprint.status)
    sprint.story_points = data.get('story_points', sprint.story_points)
    
    db.session.commit()
    return jsonify({'message': 'Sprint updated successfully'})

@app.route('/api/sprints/<int:sprint_id>', methods=['DELETE'])
def delete_sprint(sprint_id):
    sprint = Sprint.query.get_or_404(sprint_id)
    db.session.delete(sprint)
    db.session.commit()
    return jsonify({'message': 'Sprint deleted successfully'})

# Epics
@app.route('/api/sprints/<int:sprint_id>/epics', methods=['GET'])
def get_epics(sprint_id):
    epics = Epic.query.filter_by(sprint_id=sprint_id).all()
    return jsonify([{
        'id': e.id,
        'epic_id': e.epic_id,
        'name': e.name,
        'goal': e.goal,
        'story_count': len(e.user_stories),
        'total_points': sum(us.story_points for us in e.user_stories)
    } for e in epics])

@app.route('/api/epics', methods=['POST'])
def create_epic():
    data = request.get_json()
    epic = Epic(
        sprint_id=data['sprint_id'],
        epic_id=data.get('epic_id', ''),
        name=data['name'],
        goal=data.get('goal', '')
    )
    db.session.add(epic)
    db.session.commit()
    return jsonify({'id': epic.id, 'message': 'Epic created successfully'}), 201

@app.route('/api/epics/<int:epic_id>', methods=['PUT'])
def update_epic(epic_id):
    epic = Epic.query.get_or_404(epic_id)
    data = request.get_json()
    
    epic.epic_id = data.get('epic_id', epic.epic_id)
    epic.name = data.get('name', epic.name)
    epic.goal = data.get('goal', epic.goal)
    
    db.session.commit()
    return jsonify({'message': 'Epic updated successfully'})

@app.route('/api/epics/<int:epic_id>', methods=['DELETE'])
def delete_epic(epic_id):
    epic = Epic.query.get_or_404(epic_id)
    db.session.delete(epic)
    db.session.commit()
    return jsonify({'message': 'Epic deleted successfully'})

# User Stories
@app.route('/api/epics/<int:epic_id>/stories', methods=['GET'])
def get_user_stories(epic_id):
    stories = UserStory.query.filter_by(epic_id=epic_id).all()
    return jsonify([{
        'id': us.id,
        'story_id': us.story_id,
        'title': us.title,
        'description': us.description,
        'acceptance_criteria': json.loads(us.acceptance_criteria) if us.acceptance_criteria else [],
        'story_points': us.story_points,
        'status': us.status,
        'assignee': us.assignee,
        'created_at': us.created_at.isoformat()
    } for us in stories])

@app.route('/api/stories', methods=['POST'])
def create_user_story():
    data = request.get_json()
    user_story = UserStory(
        epic_id=data['epic_id'],
        story_id=data.get('story_id', ''),
        title=data['title'],
        description=data.get('description', ''),
        acceptance_criteria=json.dumps(data.get('acceptance_criteria', [])),
        story_points=data.get('story_points', 1),
        status=data.get('status', 'todo'),
        assignee=data.get('assignee', '')
    )
    db.session.add(user_story)
    db.session.commit()
    return jsonify({'id': user_story.id, 'message': 'User story created successfully'}), 201

@app.route('/api/stories/<int:story_id>', methods=['PUT'])
def update_user_story(story_id):
    story = UserStory.query.get_or_404(story_id)
    data = request.get_json()
    
    story.story_id = data.get('story_id', story.story_id)
    story.title = data.get('title', story.title)
    story.description = data.get('description', story.description)
    if 'acceptance_criteria' in data:
        story.acceptance_criteria = json.dumps(data['acceptance_criteria'])
    story.story_points = data.get('story_points', story.story_points)
    story.status = data.get('status', story.status)
    story.assignee = data.get('assignee', story.assignee)
    
    db.session.commit()
    return jsonify({'message': 'User story updated successfully'})

@app.route('/api/stories/<int:story_id>', methods=['DELETE'])
def delete_user_story(story_id):
    story = UserStory.query.get_or_404(story_id)
    db.session.delete(story)
    db.session.commit()
    return jsonify({'message': 'User story deleted successfully'})

# Risks
@app.route('/api/projects/<int:project_id>/risks', methods=['GET'])
def get_risks(project_id):
    risks = Risk.query.filter_by(project_id=project_id).all()
    return jsonify([{
        'id': r.id,
        'title': r.title,
        'description': r.description,
        'severity': r.severity,
        'mitigation': r.mitigation,
        'status': r.status
    } for r in risks])

@app.route('/api/risks', methods=['POST'])
def create_risk():
    data = request.get_json()
    risk = Risk(
        project_id=data['project_id'],
        title=data['title'],
        description=data.get('description', ''),
        severity=data.get('severity', 'medium'),
        mitigation=data.get('mitigation', ''),
        status=data.get('status', 'open')
    )
    db.session.add(risk)
    db.session.commit()
    return jsonify({'id': risk.id, 'message': 'Risk created successfully'}), 201

@app.route('/api/risks/<int:risk_id>', methods=['PUT'])
def update_risk(risk_id):
    risk = Risk.query.get_or_404(risk_id)
    data = request.get_json()
    
    risk.title = data.get('title', risk.title)
    risk.description = data.get('description', risk.description)
    risk.severity = data.get('severity', risk.severity)
    risk.mitigation = data.get('mitigation', risk.mitigation)
    risk.status = data.get('status', risk.status)
    
    db.session.commit()
    return jsonify({'message': 'Risk updated successfully'})

@app.route('/api/risks/<int:risk_id>', methods=['DELETE'])
def delete_risk(risk_id):
    risk = Risk.query.get_or_404(risk_id)
    db.session.delete(risk)
    db.session.commit()
    return jsonify({'message': 'Risk deleted successfully'})

# Search and Analytics
@app.route('/api/search')
def search():
    query = request.args.get('q', '')
    project_id = request.args.get('project_id')
    
    results = []
    
    if query:
        # Search user stories
        story_query = UserStory.query.filter(
            UserStory.title.contains(query) | 
            UserStory.description.contains(query)
        )
        
        if project_id:
            story_query = story_query.join(Epic).join(Sprint).filter(Sprint.project_id == project_id)
        
        stories = story_query.all()
        
        for story in stories:
            results.append({
                'type': 'story',
                'id': story.id,
                'title': story.title,
                'description': story.description,
                'story_id': story.story_id,
                'epic_name': story.epic.name,
                'sprint_name': story.epic.sprint.name
            })
    
    return jsonify(results)

@app.route('/api/analytics/<int:project_id>')
def get_analytics(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Calculate analytics
    total_sprints = len(project.sprints)
    total_story_points = sum(s.story_points for s in project.sprints)
    
    completed_stories = UserStory.query.join(Epic).join(Sprint).filter(
        Sprint.project_id == project_id,
        UserStory.status == 'done'
    ).count()
    
    total_stories = UserStory.query.join(Epic).join(Sprint).filter(
        Sprint.project_id == project_id
    ).count()
    
    completion_rate = (completed_stories / total_stories * 100) if total_stories > 0 else 0
    
    return jsonify({
        'total_sprints': total_sprints,
        'total_story_points': total_story_points,
        'total_stories': total_stories,
        'completed_stories': completed_stories,
        'completion_rate': round(completion_rate, 2),
        'average_points_per_sprint': round(total_story_points / total_sprints, 2) if total_sprints > 0 else 0
    })

# Initialize database function
def initialize_database():
    """Initialize database with sample data if it's empty"""
    try:
        if not Project.query.first():
            from init_db import init_database
            init_database()
            print("✅ Database initialized with sample data")
    except Exception as e:
        print(f"⚠️ Could not initialize sample data: {e}")

# Production initialization
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    with app.app_context():
        db.create_all()
        initialize_database()
    
    app.run(host='0.0.0.0', port=port, debug=debug)
