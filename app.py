# app.py - Simplified Flask Application
import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

app = Flask(__name__)

# Database configuration
if os.environ.get('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project_manager.db'

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sprints = db.relationship('Sprint', backref='project', lazy=True, cascade='all, delete-orphan')

class Sprint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    goal = db.Column(db.Text)
    duration = db.Column(db.String(100))
    status = db.Column(db.String(50), default='planned')
    story_points = db.Column(db.Integer, default=0)
    
    epics = db.relationship('Epic', backref='sprint', lazy=True, cascade='all, delete-orphan')

class Epic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sprint_id = db.Column(db.Integer, db.ForeignKey('sprint.id'), nullable=False)
    epic_id = db.Column(db.String(10))
    name = db.Column(db.String(200), nullable=False)
    goal = db.Column(db.Text)
    
    user_stories = db.relationship('UserStory', backref='epic', lazy=True, cascade='all, delete-orphan')

class UserStory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    epic_id = db.Column(db.Integer, db.ForeignKey('epic.id'), nullable=False)
    story_id = db.Column(db.String(20))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    acceptance_criteria = db.Column(db.Text)
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

# Initialize database and sample data
def init_app():
    """Initialize app with database and sample data"""
    with app.app_context():
        try:
            # Create tables
            db.create_all()
            print("✅ Database tables created")
            
            # Add sample data if empty
            if not Project.query.first():
                project = Project(
                    name="CRM Assistant Project",
                    description="Build a comprehensive CRM assistant with MCP server, backend API, and chat interface",
                    status="active"
                )
                db.session.add(project)
                
                sprint1 = Sprint(
                    project=project,
                    name="Sprint 1: Foundation & Setup",
                    goal="Establish project foundation with development environment and Railway infrastructure",
                    duration="3 Days (Days 1-3)",
                    status="completed",
                    story_points=33
                )
                db.session.add(sprint1)
                
                sprint2 = Sprint(
                    project=project,
                    name="Sprint 2: MCP Server Foundation", 
                    goal="Build the core MCP server with basic functionality and Spark CRM integration",
                    duration="5 Days (Days 4-8)",
                    status="in-progress",
                    story_points=39
                )
                db.session.add(sprint2)
                
                db.session.commit()
                print("✅ Sample data added")
            else:
                print("✅ Database already has data")
                
        except Exception as e:
            print(f"❌ Database initialization error: {e}")

# Routes
@app.route('/')
def dashboard():
    try:
        projects = Project.query.all()
        return render_template('dashboard.html', projects=projects)
    except Exception as e:
        print(f"Dashboard error: {e}")
        # Initialize database if tables don't exist
        init_app()
        projects = Project.query.all()
        return render_template('dashboard.html', projects=projects)

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project_detail.html', project=project)

# API Routes
@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'status': p.status,
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
        'epic_count': len(s.epics)
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

@app.route('/api/analytics/<int:project_id>')
def get_analytics(project_id):
    project = Project.query.get_or_404(project_id)
    
    total_sprints = len(project.sprints)
    total_story_points = sum(s.story_points for s in project.sprints)
    
    return jsonify({
        'total_sprints': total_sprints,
        'total_story_points': total_story_points,
        'total_stories': 0,
        'completed_stories': 0,
        'completion_rate': 0,
        'average_points_per_sprint': round(total_story_points / total_sprints, 2) if total_sprints > 0 else 0
    })

# Run app
if __name__ == '__main__':
    init_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')
