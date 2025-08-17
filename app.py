# app.py - Simplified Flask Application with Import Function
import os
import csv
import re
import io
from flask import Flask, render_template, request, jsonify, redirect, url_for
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

# Import Functions
def extract_epic_info(summary, description):
    """Extract epic name from summary and description"""
    epic_match = re.match(r'\[([^\]]+)\]', summary)
    if epic_match:
        return epic_match.group(1)
    
    epic_match = re.search(r'EPIC:\s*([^.]+)', description)
    if epic_match:
        return epic_match.group(1).strip()
    
    return "General"

def extract_sprint_info(labels):
    """Extract sprint information from labels"""
    sprint_match = re.search(r'sprint(\d+)', labels)
    if sprint_match:
        return int(sprint_match.group(1))
    return 1

def get_or_create_sprint(project, sprint_num, sprint_data):
    """Get or create sprint based on sprint number"""
    existing_sprint = Sprint.query.filter_by(project_id=project.id, name=sprint_data['name']).first()
    if existing_sprint:
        return existing_sprint
    
    sprint = Sprint(
        project=project,
        name=sprint_data['name'],
        goal=sprint_data['goal'],
        duration=sprint_data['duration'],
        status=sprint_data['status'],
        story_points=0
    )
    db.session.add(sprint)
    return sprint

def get_or_create_epic(sprint, epic_name, epic_data):
    """Get or create epic based on name"""
    existing_epic = Epic.query.filter_by(sprint_id=sprint.id, name=epic_data['name']).first()
    if existing_epic:
        return existing_epic
    
    epic = Epic(
        sprint=sprint,
        epic_id=epic_data['epic_id'],
        name=epic_data['name'],
        goal=epic_data['goal']
    )
    db.session.add(epic)
    return epic

def calculate_story_points(summary, description, priority):
    """Calculate story points based on complexity indicators"""
    text = (summary + " " + description).lower()
    
    priority_points = {'High': 5, 'Medium': 3, 'Low': 2}
    base_points = priority_points.get(priority, 3)
    
    complexity_keywords = {
        'setup': 2, 'configuration': 2, 'framework': 3, 'integration': 3,
        'authentication': 3, 'security': 3, 'testing': 2, 'deployment': 3,
        'monitoring': 2, 'documentation': 1, 'api': 2, 'database': 3
    }
    
    complexity_bonus = 0
    for keyword, points in complexity_keywords.items():
        if keyword in text:
            complexity_bonus += points
            break
    
    return min(base_points + complexity_bonus, 13)

def import_user_stories():
    """Import user stories from CSV data"""
    
    sprint_definitions = {
        1: {'name': 'Sprint 1: Foundation & Infrastructure', 'goal': 'Establish project foundation with development environment and infrastructure', 'duration': '2 weeks', 'status': 'completed'},
        2: {'name': 'Sprint 2: MCP Server Core', 'goal': 'Build the core MCP server with basic functionality', 'duration': '2 weeks', 'status': 'in-progress'},
        3: {'name': 'Sprint 3: Core MCP Tools', 'goal': 'Implement essential MCP tools for CRM operations', 'duration': '2 weeks', 'status': 'planned'},
        4: {'name': 'Sprint 4: Claude Integration & Backend', 'goal': 'Integrate Claude AI and build backend services', 'duration': '2 weeks', 'status': 'planned'},
        5: {'name': 'Sprint 5: Frontend Development', 'goal': 'Build React frontend for user interactions', 'duration': '2 weeks', 'status': 'planned'},
        6: {'name': 'Sprint 6: Testing & Quality Assurance', 'goal': 'Comprehensive testing and quality assurance', 'duration': '2 weeks', 'status': 'planned'},
        7: {'name': 'Sprint 7: Deployment & Documentation', 'goal': 'Production deployment and documentation', 'duration': '1 week', 'status': 'planned'}
    }
    
    epic_definitions = {
        'Foundation': {'epic_id': 'FND', 'name': 'Foundation & Infrastructure', 'goal': 'Establish project foundation with development environment and infrastructure setup'},
        'MCP Core': {'epic_id': 'MCP', 'name': 'MCP Server Core', 'goal': 'Build the core MCP server framework with essential functionality'},
        'Core MCP Tools': {'epic_id': 'MCT', 'name': 'Core MCP Tools', 'goal': 'Implement essential MCP tools for CRM operations and member management'},
        'Claude Integration & Backend': {'epic_id': 'CIB', 'name': 'Claude Integration & Backend', 'goal': 'Integrate Claude AI and build robust backend services'},
        'Frontend Development': {'epic_id': 'FED', 'name': 'Frontend Development', 'goal': 'Build React frontend for user interactions and chat interface'},
        'Testing & Quality Assurance': {'epic_id': 'TQA', 'name': 'Testing & Quality Assurance', 'goal': 'Comprehensive testing and quality assurance across all components'},
        'Deployment & Documentation': {'epic_id': 'DD', 'name': 'Deployment & Documentation', 'goal': 'Production deployment and comprehensive documentation'}
    }

    try:
        project = Project.query.filter_by(name='CRM Assistant Project').first()
        if not project:
            project = Project(
                name='CRM Assistant Project',
                description='Build a comprehensive CRM assistant with MCP server, backend API, and chat interface',
                status='active'
            )
            db.session.add(project)
            db.session.flush()
        
        # CSV data (truncated for brevity - you'll need the full data)
        csv_data = '''Issue Type,Summary,Description,Priority,Labels
Story,[Foundation] Repository Creation,"EPIC: Foundation & Infrastructure. As a developer, I want a centralized GitHub repository so that the team can collaborate effectively. Acceptance Criteria: GitHub repository created with appropriate permissions, README.md with project overview, Initial branch protection rules configured, Team members have appropriate access levels",High,"git,repository,sprint1,foundation"
Story,[Foundation] Local Development Environment,"EPIC: Foundation & Infrastructure. As a developer, I want a standardized local development setup so that all team members work in consistent environments. Acceptance Criteria: Node.js 20+ installed and verified, Package manager configured, Environment works on Windows/Mac/Linux, Setup documentation created",High,"setup,nodejs,sprint1,foundation"
Story,[MCP Core] MCP Server Framework,"EPIC: MCP Server Core. As a system architect, I want a robust MCP server foundation so that tools can be built reliably. Acceptance Criteria: @modelcontextprotocol/sdk integrated, Server initialization logic implemented, Configuration management system, Server starts without errors",High,"mcp,framework,sprint2,mcp-core"
Story,[Frontend] React App Initialization,"EPIC: Frontend Development. As a frontend developer, I want a modern React setup so that development is efficient and maintainable. Acceptance Criteria: Create React App with TypeScript template, Folder structure organized by features, Import alias configuration, Development server with hot reload",High,"react,setup,sprint5,frontend"'''
        
        csv_reader = csv.DictReader(io.StringIO(csv_data))
        
        stories_created = 0
        sprints_created = {}
        epics_created = {}
        
        for row in csv_reader:
            epic_name = extract_epic_info(row['Summary'], row['Description'])
            sprint_num = extract_sprint_info(row['Labels'])
            
            if sprint_num not in sprints_created:
                sprint_data = sprint_definitions.get(sprint_num, sprint_definitions[1])
                sprint = get_or_create_sprint(project, sprint_num, sprint_data)
                sprints_created[sprint_num] = sprint
                db.session.flush()
            else:
                sprint = sprints_created[sprint_num]
            
            epic_key = f"{sprint_num}-{epic_name}"
            if epic_key not in epics_created:
                epic_def_key = epic_name
                if 'Foundation' in epic_name:
                    epic_def_key = 'Foundation'
                elif 'MCP Core' in epic_name:
                    epic_def_key = 'MCP Core'
                elif 'Frontend' in epic_name:
                    epic_def_key = 'Frontend Development'
                
                epic_data = epic_definitions.get(epic_def_key, {
                    'epic_id': 'GEN',
                    'name': epic_name,
                    'goal': f'Epic for {epic_name} related stories'
                })
                
                epic = get_or_create_epic(sprint, epic_name, epic_data)
                epics_created[epic_key] = epic
                db.session.flush()
            else:
                epic = epics_created[epic_key]
            
            story_points = calculate_story_points(row['Summary'], row['Description'], row['Priority'])
            
            epic_prefix = epic.epic_id if epic.epic_id else 'GEN'
            story_count = len(epic.user_stories) + 1
            story_id = f"{epic_prefix}-{story_count:03d}"
            
            title = re.sub(r'^\[[^\]]+\]\s*', '', row['Summary'])
            
            user_story = UserStory(
                epic=epic,
                story_id=story_id,
                title=title,
                description=row['Description'],
                story_points=story_points,
                status='todo',
                created_at=datetime.utcnow()
            )
            
            db.session.add(user_story)
            stories_created += 1
        
        for sprint in sprints_created.values():
            total_points = 0
            for epic in sprint.epics:
                for story in epic.user_stories:
                    total_points += story.story_points or 0
            sprint.story_points = total_points
        
        db.session.commit()
        
        print(f"✅ Successfully imported {stories_created} user stories!")
        return stories_created
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error importing user stories: {e}")
        raise

# Initialize database and sample data
def init_app():
    """Initialize app with database and sample data"""
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created")
            
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
                
                # Import user stories
                print("🚀 Importing user stories...")
                import_user_stories()
                
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
        init_app()
        projects = Project.query.all()
        return render_template('dashboard.html', projects=projects)

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project_detail.html', project=project)

@app.route('/project/<int:project_id>/backlog')
def project_backlog(project_id):
    """Display project backlog with user stories"""
    try:
        project = Project.query.get_or_404(project_id)
        
        user_stories = []
        for sprint in project.sprints:
            for epic in sprint.epics:
                user_stories.extend(epic.user_stories)
        
        sprints = Sprint.query.filter_by(project_id=project_id).all()
        
        return render_template('backlog.html', 
                             project=project, 
                             user_stories=user_stories,
                             sprints=sprints)
    except Exception as e:
        print(f"Backlog error: {e}")
        return redirect(url_for('project_detail', project_id=project_id))

# Special route to trigger import manually
@app.route('/import-stories')
def trigger_import():
    """Manual trigger for importing stories"""
    try:
        count = import_user_stories()
        return f"✅ Successfully imported {count} user stories! <br><a href='/'>← Back to Dashboard</a>"
    except Exception as e:
        return f"❌ Error importing stories: {e} <br><a href='/'>← Back to Dashboard</a>"

# API Routes (keeping existing ones)
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
    
    total_stories = 0
    completed_stories = 0
    for sprint in project.sprints:
        for epic in sprint.epics:
            total_stories += len(epic.user_stories)
            completed_stories += len([story for story in epic.user_stories if story.status == 'Done'])
    
    completion_rate = round((completed_stories / total_stories * 100), 2) if total_stories > 0 else 0
    
    return jsonify({
        'total_sprints': total_sprints,
        'total_story_points': total_story_points,
        'total_stories': total_stories,
        'completed_stories': completed_stories,
        'completion_rate': completion_rate,
        'average_points_per_sprint': round(total_story_points / total_sprints, 2) if total_sprints > 0 else 0
    })

# Add these routes to your app.py file 
# Place them after your existing routes but before the API routes section
# (after the project_backlog route and before the trigger_import route)

@app.route('/projects')
def all_projects():
    """Show all projects"""
    projects = Project.query.all()
    return render_template('all_projects.html', projects=projects, title="All Projects")

@app.route('/projects/active')
def active_projects():
    """Show only active projects"""
    projects = Project.query.filter_by(status='active').all()
    return render_template('all_projects.html', projects=projects, title="Active Projects")

@app.route('/sprints')
def all_sprints():
    """Show all sprints across all projects"""
    sprints = Sprint.query.join(Project).all()
    return render_template('all_sprints.html', sprints=sprints)

@app.route('/sprint/<int:sprint_id>')
def sprint_detail(sprint_id):
    """Show sprint details with user stories"""
    sprint = Sprint.query.get_or_404(sprint_id)
    
    # Get all user stories for this sprint
    user_stories = []
    for epic in sprint.epics:
        user_stories.extend(epic.user_stories)
    
    return render_template('sprint_detail.html', sprint=sprint, user_stories=user_stories)

# Replace the existing all_user_stories route in your app.py with this fixed version:

# Replace your existing all_user_stories route with this:

@app.route('/user-stories')
def all_user_stories():
    """Show all user stories across all projects"""
    try:
        # Get all user stories with their relationships loaded
        user_stories = UserStory.query.options(
            db.joinedload(UserStory.epic).joinedload(Epic.sprint).joinedload(Sprint.project)
        ).all()
        
        return render_template('all_user_stories.html', user_stories=user_stories)
    except Exception as e:
        print(f"Error loading user stories: {e}")
        # Fallback: simple query
        user_stories = UserStory.query.all()
        return render_template('all_user_stories.html', user_stories=user_stories)
        

@app.route('/user-story/<int:story_id>')
def user_story_detail(story_id):
    """Show detailed user story information"""
    story = UserStory.query.get_or_404(story_id)
    return render_template('user_story_detail.html', story=story)
# Replace your existing reset-and-import route with this improved version:

@app.route('/reset-and-import')
def reset_and_import():
    """Reset database and import sample stories with real user stories"""
    try:
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        # Create project
        project = Project(
            name="CRM Assistant Project",
            description="Build a comprehensive CRM assistant with MCP server, backend API, and chat interface",
            status="active"
        )
        db.session.add(project)
        db.session.flush()
        
        # Create sprints with epics and user stories
        sprint_data = [
            {
                "name": "Sprint 1: Foundation & Infrastructure",
                "goal": "Establish project foundation",
                "duration": "2 weeks",
                "status": "completed",
                "epics": [
                    {
                        "epic_id": "FND",
                        "name": "Foundation & Infrastructure",
                        "goal": "Set up development environment and infrastructure",
                        "stories": [
                            {"title": "Repository Creation", "description": "Create GitHub repository with proper permissions", "points": 3, "status": "Done"},
                            {"title": "Development Environment", "description": "Set up local development environment", "points": 5, "status": "Done"},
                            {"title": "Railway CLI Setup", "description": "Configure Railway CLI for deployment", "points": 3, "status": "Done"},
                            {"title": "Environment Configuration", "description": "Set up environment variables", "points": 2, "status": "Done"},
                        ]
                    }
                ]
            },
            {
                "name": "Sprint 2: MCP Server Core",
                "goal": "Build the core MCP server",
                "duration": "2 weeks",
                "status": "in-progress",
                "epics": [
                    {
                        "epic_id": "MCP",
                        "name": "MCP Server Core",
                        "goal": "Build robust MCP server foundation",
                        "stories": [
                            {"title": "MCP Server Framework", "description": "Integrate @modelcontextprotocol/sdk", "points": 8, "status": "Done"},
                            {"title": "Error Handling System", "description": "Implement comprehensive error handling", "points": 5, "status": "in-progress"},
                            {"title": "Health Monitoring", "description": "Add health check endpoints", "points": 3, "status": "todo"},
                            {"title": "API Client Foundation", "description": "Build robust API client", "points": 5, "status": "todo"},
                        ]
                    }
                ]
            },
            {
                "name": "Sprint 3: Core MCP Tools",
                "goal": "Implement essential MCP tools",
                "duration": "2 weeks",
                "status": "planned",
                "epics": [
                    {
                        "epic_id": "MCT",
                        "name": "Core MCP Tools",
                        "goal": "Essential tools for CRM operations",
                        "stories": [
                            {"title": "Get Attendance Tool", "description": "Tool to check member attendance", "points": 5, "status": "todo"},
                            {"title": "Member Search Logic", "description": "Flexible member search functionality", "points": 3, "status": "todo"},
                            {"title": "Payment Status Checker", "description": "Check payment status for members", "points": 5, "status": "todo"},
                            {"title": "Email Update Tool", "description": "Update member email addresses", "points": 3, "status": "todo"},
                        ]
                    }
                ]
            },
            {
                "name": "Sprint 4: Claude Integration & Backend",
                "goal": "Integrate Claude AI and build backend",
                "duration": "2 weeks",
                "status": "planned",
                "epics": [
                    {
                        "epic_id": "CIB",
                        "name": "Claude Integration & Backend",
                        "goal": "Claude AI integration and backend services",
                        "stories": [
                            {"title": "Express Application Setup", "description": "Configure Express.js with TypeScript", "points": 5, "status": "todo"},
                            {"title": "Anthropic SDK Setup", "description": "Integrate Claude AI SDK", "points": 8, "status": "todo"},
                            {"title": "Tool Definitions for Claude", "description": "Define tool schemas for Claude", "points": 5, "status": "todo"},
                            {"title": "Main Chat Endpoint", "description": "Create chat API endpoint", "points": 8, "status": "todo"},
                        ]
                    }
                ]
            },
            {
                "name": "Sprint 5: Frontend Development",
                "goal": "Build React frontend",
                "duration": "2 weeks",
                "status": "planned",
                "epics": [
                    {
                        "epic_id": "FED",
                        "name": "Frontend Development",
                        "goal": "React frontend for user interactions",
                        "stories": [
                            {"title": "React App Initialization", "description": "Set up React with TypeScript", "points": 5, "status": "todo"},
                            {"title": "Chat Container Component", "description": "Design chat interface", "points": 8, "status": "todo"},
                            {"title": "Message List Component", "description": "Display conversation history", "points": 5, "status": "todo"},
                            {"title": "API Service Layer", "description": "Organize backend communication", "points": 3, "status": "todo"},
                        ]
                    }
                ]
            },
            {
                "name": "Sprint 6: Testing & Quality Assurance",
                "goal": "Comprehensive testing",
                "duration": "2 weeks",
                "status": "planned",
                "epics": [
                    {
                        "epic_id": "TQA",
                        "name": "Testing & Quality Assurance",
                        "goal": "Ensure system reliability",
                        "stories": [
                            {"title": "Backend Unit Tests", "description": "80%+ code coverage for backend", "points": 8, "status": "todo"},
                            {"title": "Frontend Unit Tests", "description": "Component testing with Testing Library", "points": 5, "status": "todo"},
                            {"title": "API Integration Tests", "description": "End-to-end API workflow testing", "points": 5, "status": "todo"},
                            {"title": "E2E Test Framework", "description": "Playwright test framework setup", "points": 8, "status": "todo"},
                        ]
                    }
                ]
            },
            {
                "name": "Sprint 7: Deployment & Documentation",
                "goal": "Production deployment",
                "duration": "1 week",
                "status": "planned",
                "epics": [
                    {
                        "epic_id": "DD",
                        "name": "Deployment & Documentation",
                        "goal": "Production deployment and documentation",
                        "stories": [
                            {"title": "Production Environment Setup", "description": "Railway production deployment", "points": 5, "status": "todo"},
                            {"title": "CI/CD Pipeline", "description": "GitHub Actions workflow", "points": 5, "status": "todo"},
                            {"title": "Technical Documentation", "description": "API and architecture docs", "points": 3, "status": "todo"},
                            {"title": "User Documentation", "description": "User guides and tutorials", "points": 3, "status": "todo"},
                        ]
                    }
                ]
            }
        ]
        
        # Create sprints, epics, and user stories
        for sprint_info in sprint_data:
            sprint = Sprint(
                project=project,
                name=sprint_info["name"],
                goal=sprint_info["goal"],
                duration=sprint_info["duration"],
                status=sprint_info["status"],
                story_points=0  # Will be calculated
            )
            db.session.add(sprint)
            db.session.flush()
            
            total_sprint_points = 0
            
            for epic_info in sprint_info["epics"]:
                epic = Epic(
                    sprint=sprint,
                    epic_id=epic_info["epic_id"],
                    name=epic_info["name"],
                    goal=epic_info["goal"]
                )
                db.session.add(epic)
                db.session.flush()
                
                for i, story_info in enumerate(epic_info["stories"], 1):
                    user_story = UserStory(
                        epic=epic,
                        story_id=f"{epic_info['epic_id']}-{i:03d}",
                        title=story_info["title"],
                        description=story_info["description"],
                        story_points=story_info["points"],
                        status=story_info["status"],
                        created_at=datetime.utcnow()
                    )
                    db.session.add(user_story)
                    total_sprint_points += story_info["points"]
            
            # Update sprint points
            sprint.story_points = total_sprint_points
        
        db.session.commit()
        
        # Count actual user stories created
        total_stories = UserStory.query.count()
        
        return f"✅ Database reset complete!<br>" \
               f"Created 7 sprints with {total_stories} real user stories!<br>" \
               f"<a href='/'>← Back to Dashboard</a>"
               
    except Exception as e:
        db.session.rollback()
        return f"❌ Error: {e} <br><a href='/'>← Back to Dashboard</a>"

# Run app
if __name__ == '__main__':
    init_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')
