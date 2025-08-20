# app.py - Enhanced Flask Application with Prompt-Based Project Generation and Template Management
import os
import csv
import re
import io
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
    project_type = db.Column(db.String(50), default='general')  # crm, ecommerce, mobile, web, etc
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_from_template = db.Column(db.Integer, db.ForeignKey('project_template.id'))
    
    sprints = db.relationship('Sprint', backref='project', lazy=True, cascade='all, delete-orphan')

class Sprint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    goal = db.Column(db.Text)
    duration = db.Column(db.String(100))
    status = db.Column(db.String(50), default='planned')
    story_points = db.Column(db.Integer, default=0)
    sprint_order = db.Column(db.Integer, default=1)
    
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
    acceptance_criteria = db.Column(db.Text)  # This stores the task prompt
    story_points = db.Column(db.Integer, default=1)
    status = db.Column(db.String(50), default='todo')
    assignee = db.Column(db.String(100))
    priority = db.Column(db.String(20), default='medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Risk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(50), default='medium')
    mitigation = db.Column(db.Text)
    status = db.Column(db.String(50), default='open')

class ProjectTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    project_type = db.Column(db.String(50), nullable=False)
    template_data = db.Column(db.Text)  # JSON structure of sprints/epics/stories
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100), default='system')
    is_public = db.Column(db.Boolean, default=True)
    usage_count = db.Column(db.Integer, default=0)

# Enhanced project generation functions
def detect_project_type(description):
    """Detect project type from description"""
    description = description.lower()
    
    if any(word in description for word in ['crm', 'customer', 'sales', 'lead', 'contact']):
        return 'crm'
    elif any(word in description for word in ['ecommerce', 'shop', 'store', 'cart', 'payment', 'product']):
        return 'ecommerce'
    elif any(word in description for word in ['mobile', 'app', 'ios', 'android', 'react native']):
        return 'mobile'
    elif any(word in description for word in ['web', 'website', 'frontend', 'backend', 'api']):
        return 'web'
    elif any(word in description for word in ['analytics', 'dashboard', 'reporting', 'data']):
        return 'analytics'
    elif any(word in description for word in ['ai', 'machine learning', 'ml', 'artificial intelligence']):
        return 'ai'
    else:
        return 'general'

def generate_project_structure(project_type, description, project_name):
    """Generate sprint structure based on project type"""
    
    if project_type == 'crm':
        return {
            'sprints': [
                {
                    'name': 'Sprint 1: Foundation & Setup',
                    'goal': 'Establish project foundation and database structure',
                    'duration': '2 weeks',
                    'epics': [
                        {
                            'epic_id': 'FND',
                            'name': 'Foundation',
                            'goal': 'Project foundation and infrastructure',
                            'stories': [
                                {'title': 'Database Schema Design', 'description': 'Design database schema for contacts, leads, and activities', 'points': 8, 'priority': 'high', 'prompt': 'Create a comprehensive database schema that supports contact management, lead tracking, and activity logging with proper relationships and indexing'},
                                {'title': 'User Authentication System', 'description': 'Implement secure user login and registration', 'points': 5, 'priority': 'high', 'prompt': 'Build a secure authentication system with password hashing, session management, and role-based access control'},
                                {'title': 'Basic UI Framework', 'description': 'Set up responsive UI framework', 'points': 5, 'priority': 'medium', 'prompt': 'Create a responsive UI framework using modern CSS and JavaScript that will serve as the foundation for all CRM interfaces'},
                                {'title': 'Development Environment', 'description': 'Configure development and deployment environment', 'points': 3, 'priority': 'high', 'prompt': 'Set up development environment with proper tooling, testing framework, and deployment pipeline for efficient development workflow'}
                            ]
                        }
                    ]
                },
                {
                    'name': 'Sprint 2: Core CRM Features',
                    'goal': 'Implement essential CRM functionality',
                    'duration': '3 weeks',
                    'epics': [
                        {
                            'epic_id': 'CRM',
                            'name': 'Core CRM',
                            'goal': 'Essential CRM features for contact and lead management',
                            'stories': [
                                {'title': 'Contact Management', 'description': 'Create, read, update, delete contacts with detailed information', 'points': 13, 'priority': 'high', 'prompt': 'Implement comprehensive contact management with fields for personal info, company details, contact preferences, and custom fields'},
                                {'title': 'Lead Tracking System', 'description': 'Track leads through sales pipeline stages', 'points': 8, 'priority': 'high', 'prompt': 'Build a lead tracking system with customizable pipeline stages, lead scoring, and conversion tracking'},
                                {'title': 'Activity Logging', 'description': 'Log calls, emails, meetings, and other interactions', 'points': 8, 'priority': 'medium', 'prompt': 'Create an activity logging system that captures all customer interactions with timestamps, notes, and follow-up reminders'},
                                {'title': 'Search and Filtering', 'description': 'Advanced search and filtering capabilities', 'points': 5, 'priority': 'medium', 'prompt': 'Implement advanced search functionality with filters for contact properties, lead status, and activity history'}
                            ]
                        }
                    ]
                },
                {
                    'name': 'Sprint 3: Communication Tools',
                    'goal': 'Add communication and follow-up features',
                    'duration': '2 weeks',
                    'epics': [
                        {
                            'epic_id': 'COM',
                            'name': 'Communication',
                            'goal': 'Communication tools and automation',
                            'stories': [
                                {'title': 'Email Integration', 'description': 'Send and track emails directly from CRM', 'points': 8, 'priority': 'high', 'prompt': 'Integrate email functionality with template support, tracking, and automatic logging of sent emails'},
                                {'title': 'Task Management', 'description': 'Create and manage follow-up tasks', 'points': 5, 'priority': 'medium', 'prompt': 'Build a task management system for follow-ups, reminders, and action items with due dates and priority levels'},
                                {'title': 'Notification System', 'description': 'Real-time notifications and alerts', 'points': 5, 'priority': 'medium', 'prompt': 'Create a notification system for important events, overdue tasks, and system alerts'},
                                {'title': 'Reporting Dashboard', 'description': 'Basic analytics and reporting', 'points': 8, 'priority': 'low', 'prompt': 'Build a reporting dashboard with key metrics, charts, and exportable reports for sales performance analysis'}
                            ]
                        }
                    ]
                }
            ]
        }
    
    elif project_type == 'ecommerce':
        return {
            'sprints': [
                {
                    'name': 'Sprint 1: Core Commerce Setup',
                    'goal': 'Basic ecommerce foundation with product catalog',
                    'duration': '3 weeks',
                    'epics': [
                        {
                            'epic_id': 'PRD',
                            'name': 'Product Management',
                            'goal': 'Product catalog and inventory management',
                            'stories': [
                                {'title': 'Product Catalog Schema', 'description': 'Design product database with categories, variants, and pricing', 'points': 8, 'priority': 'high', 'prompt': 'Create a flexible product catalog schema supporting multiple variants, categories, pricing tiers, and inventory tracking'},
                                {'title': 'Product CRUD Operations', 'description': 'Create, read, update, delete products', 'points': 8, 'priority': 'high', 'prompt': 'Implement full CRUD operations for products with image upload, SEO fields, and variant management'},
                                {'title': 'Category Management', 'description': 'Hierarchical product categories', 'points': 5, 'priority': 'medium', 'prompt': 'Build a hierarchical category system with nested categories, category images, and SEO optimization'},
                                {'title': 'Inventory Tracking', 'description': 'Track product inventory and stock levels', 'points': 5, 'priority': 'medium', 'prompt': 'Implement inventory tracking with stock alerts, reorder points, and automatic stock level updates'}
                            ]
                        }
                    ]
                },
                {
                    'name': 'Sprint 2: Shopping Experience',
                    'goal': 'Customer-facing shopping features',
                    'duration': '3 weeks',
                    'epics': [
                        {
                            'epic_id': 'SHOP',
                            'name': 'Shopping Features',
                            'goal': 'Core shopping cart and checkout functionality',
                            'stories': [
                                {'title': 'Product Display Pages', 'description': 'Product listing and detail pages', 'points': 8, 'priority': 'high', 'prompt': 'Create responsive product pages with image galleries, detailed descriptions, reviews, and related products'},
                                {'title': 'Shopping Cart', 'description': 'Add to cart, modify quantities, and cart persistence', 'points': 8, 'priority': 'high', 'prompt': 'Build a shopping cart system with quantity updates, item removal, cart persistence, and guest checkout support'},
                                {'title': 'User Registration', 'description': 'Customer account creation and management', 'points': 5, 'priority': 'medium', 'prompt': 'Implement customer registration with profile management, order history, and wishlist functionality'},
                                {'title': 'Search and Filters', 'description': 'Product search with filtering options', 'points': 8, 'priority': 'medium', 'prompt': 'Create advanced product search with filters for price, category, brand, ratings, and other attributes'}
                            ]
                        }
                    ]
                },
                {
                    'name': 'Sprint 3: Payment & Orders',
                    'goal': 'Complete the purchase flow',
                    'duration': '2 weeks',
                    'epics': [
                        {
                            'epic_id': 'PAY',
                            'name': 'Payment Processing',
                            'goal': 'Secure payment processing and order management',
                            'stories': [
                                {'title': 'Payment Gateway Integration', 'description': 'Integrate with Stripe or similar payment processor', 'points': 13, 'priority': 'high', 'prompt': 'Integrate secure payment processing with support for credit cards, digital wallets, and fraud protection'},
                                {'title': 'Order Management', 'description': 'Process and track customer orders', 'points': 8, 'priority': 'high', 'prompt': 'Build order management system with status tracking, order history, and customer notifications'},
                                {'title': 'Shipping Calculator', 'description': 'Calculate shipping costs and delivery options', 'points': 5, 'priority': 'medium', 'prompt': 'Implement shipping cost calculation with multiple carrier options and delivery time estimates'},
                                {'title': 'Order Confirmation', 'description': 'Email confirmations and receipts', 'points': 3, 'priority': 'medium', 'prompt': 'Create automated order confirmation emails with receipt details and tracking information'}
                            ]
                        }
                    ]
                }
            ]
        }
    
    elif project_type == 'mobile':
        return {
            'sprints': [
                {
                    'name': 'Sprint 1: Mobile App Foundation',
                    'goal': 'Set up mobile development environment and core structure',
                    'duration': '2 weeks',
                    'epics': [
                        {
                            'epic_id': 'MOB',
                            'name': 'Mobile Foundation',
                            'goal': 'Mobile app foundation and core components',
                            'stories': [
                                {'title': 'React Native Setup', 'description': 'Initialize React Native project with navigation', 'points': 5, 'priority': 'high', 'prompt': 'Set up React Native development environment with navigation, state management, and development tools'},
                                {'title': 'UI Component Library', 'description': 'Create reusable UI components', 'points': 8, 'priority': 'high', 'prompt': 'Build a comprehensive UI component library with consistent styling, theming, and responsive design'},
                                {'title': 'Authentication Screens', 'description': 'Login, registration, and onboarding flows', 'points': 8, 'priority': 'high', 'prompt': 'Create authentication screens with form validation, biometric login options, and smooth onboarding experience'},
                                {'title': 'Data Storage Setup', 'description': 'Local storage and API integration setup', 'points': 5, 'priority': 'medium', 'prompt': 'Implement local data storage with offline capabilities and API integration for data synchronization'}
                            ]
                        }
                    ]
                },
                {
                    'name': 'Sprint 2: Core App Features',
                    'goal': 'Implement main application functionality',
                    'duration': '3 weeks',
                    'epics': [
                        {
                            'epic_id': 'CORE',
                            'name': 'Core Features',
                            'goal': 'Main application functionality and user interactions',
                            'stories': [
                                {'title': 'Main Dashboard', 'description': 'Central hub with key information and actions', 'points': 8, 'priority': 'high', 'prompt': 'Design and implement a main dashboard with widgets, quick actions, and personalized content'},
                                {'title': 'Data Management', 'description': 'CRUD operations for main app entities', 'points': 13, 'priority': 'high', 'prompt': 'Implement comprehensive data management with offline support and conflict resolution'},
                                {'title': 'Push Notifications', 'description': 'Local and remote push notification system', 'points': 8, 'priority': 'medium', 'prompt': 'Set up push notification system with scheduling, deep linking, and user preferences'},
                                {'title': 'Settings and Preferences', 'description': 'User settings and app configuration', 'points': 5, 'priority': 'low', 'prompt': 'Create settings interface for user preferences, app configuration, and account management'}
                            ]
                        }
                    ]
                },
                {
                    'name': 'Sprint 3: Polish and Deployment',
                    'goal': 'Testing, optimization, and app store deployment',
                    'duration': '2 weeks',
                    'epics': [
                        {
                            'epic_id': 'DEPLOY',
                            'name': 'Deployment',
                            'goal': 'App optimization, testing, and store deployment',
                            'stories': [
                                {'title': 'Performance Optimization', 'description': 'Optimize app performance and bundle size', 'points': 8, 'priority': 'high', 'prompt': 'Optimize app performance with code splitting, image optimization, and memory management'},
                                {'title': 'Testing Suite', 'description': 'Unit tests, integration tests, and E2E testing', 'points': 8, 'priority': 'medium', 'prompt': 'Implement comprehensive testing with unit tests, integration tests, and automated UI testing'},
                                {'title': 'App Store Preparation', 'description': 'Prepare for iOS and Android app store submission', 'points': 5, 'priority': 'high', 'prompt': 'Prepare app store assets, compliance documentation, and deployment configuration for both iOS and Android'},
                                {'title': 'Analytics Integration', 'description': 'User analytics and crash reporting', 'points': 3, 'priority': 'low', 'prompt': 'Integrate analytics tools for user behavior tracking and crash reporting for ongoing app improvement'}
                            ]
                        }
                    ]
                }
            ]
        }
    
    else:  # general/web/other types
        return {
            'sprints': [
                {
                    'name': 'Sprint 1: Project Foundation',
                    'goal': 'Establish project structure and core infrastructure',
                    'duration': '2 weeks',
                    'epics': [
                        {
                            'epic_id': 'FND',
                            'name': 'Foundation',
                            'goal': 'Project setup and infrastructure',
                            'stories': [
                                {'title': 'Project Setup', 'description': 'Initialize project structure and dependencies', 'points': 5, 'priority': 'high', 'prompt': 'Set up project structure with proper tooling, dependencies, and development environment configuration'},
                                {'title': 'Database Design', 'description': 'Design and implement data models', 'points': 8, 'priority': 'high', 'prompt': 'Design database schema with proper relationships, constraints, and indexing for optimal performance'},
                                {'title': 'Authentication System', 'description': 'User authentication and authorization', 'points': 8, 'priority': 'medium', 'prompt': 'Implement secure user authentication with session management and role-based access control'},
                                {'title': 'Basic UI Framework', 'description': 'Set up frontend framework and styling', 'points': 5, 'priority': 'medium', 'prompt': 'Create a responsive UI framework with consistent styling, component library, and accessibility features'}
                            ]
                        }
                    ]
                },
                {
                    'name': 'Sprint 2: Core Functionality',
                    'goal': 'Implement main application features',
                    'duration': '3 weeks',
                    'epics': [
                        {
                            'epic_id': 'CORE',
                            'name': 'Core Features',
                            'goal': 'Main application functionality',
                            'stories': [
                                {'title': 'Data Management', 'description': 'CRUD operations for main entities', 'points': 13, 'priority': 'high', 'prompt': 'Implement comprehensive data management with validation, error handling, and data integrity checks'},
                                {'title': 'User Interface', 'description': 'Main user interface screens and interactions', 'points': 13, 'priority': 'high', 'prompt': 'Create intuitive user interfaces with responsive design, form validation, and user-friendly interactions'},
                                {'title': 'Business Logic', 'description': 'Core business rules and processes', 'points': 8, 'priority': 'high', 'prompt': 'Implement business logic with proper validation, workflow management, and business rule enforcement'},
                                {'title': 'Search and Filtering', 'description': 'Search functionality and data filtering', 'points': 5, 'priority': 'medium', 'prompt': 'Add search capabilities with advanced filtering, sorting, and pagination for better data discovery'}
                            ]
                        }
                    ]
                },
                {
                    'name': 'Sprint 3: Enhancement and Integration',
                    'goal': 'Add advanced features and third-party integrations',
                    'duration': '2 weeks',
                    'epics': [
                        {
                            'epic_id': 'ENH',
                            'name': 'Enhancements',
                            'goal': 'Advanced features and integrations',
                            'stories': [
                                {'title': 'API Integration', 'description': 'Integrate with external APIs and services', 'points': 8, 'priority': 'medium', 'prompt': 'Integrate with external APIs for enhanced functionality with proper error handling and rate limiting'},
                                {'title': 'Reporting Features', 'description': 'Analytics and reporting capabilities', 'points': 8, 'priority': 'medium', 'prompt': 'Build reporting features with data visualization, export capabilities, and scheduled reports'},
                                {'title': 'Performance Optimization', 'description': 'Optimize application performance', 'points': 5, 'priority': 'low', 'prompt': 'Optimize application performance with caching, database optimization, and frontend performance improvements'},
                                {'title': 'Testing and Documentation', 'description': 'Comprehensive testing and documentation', 'points': 5, 'priority': 'low', 'prompt': 'Create comprehensive test suite and documentation for maintainability and future development'}
                            ]
                        }
                    ]
                }
            ]
        }

def create_project_from_prompt(name, description):
    """Create a complete project structure from a text prompt"""
    project_type = detect_project_type(description)
    structure = generate_project_structure(project_type, description, name)
    
    # Create project
    project = Project(
        name=name,
        description=description,
        project_type=project_type,
        status='active'
    )
    db.session.add(project)
    db.session.flush()
    
    # Create sprints, epics, and user stories
    for i, sprint_data in enumerate(structure['sprints'], 1):
        sprint = Sprint(
            project=project,
            name=sprint_data['name'],
            goal=sprint_data['goal'],
            duration=sprint_data['duration'],
            status='planned',
            sprint_order=i,
            story_points=0  # Will be calculated
        )
        db.session.add(sprint)
        db.session.flush()
        
        total_sprint_points = 0
        
        for epic_data in sprint_data['epics']:
            epic = Epic(
                sprint=sprint,
                epic_id=epic_data['epic_id'],
                name=epic_data['name'],
                goal=epic_data['goal']
            )
            db.session.add(epic)
            db.session.flush()
            
            for j, story_data in enumerate(epic_data['stories'], 1):
                user_story = UserStory(
                    epic=epic,
                    story_id=f"{epic_data['epic_id']}-{j:03d}",
                    title=story_data['title'],
                    description=story_data['description'],
                    acceptance_criteria=story_data['prompt'],  # Store the task prompt
                    story_points=story_data['points'],
                    priority=story_data['priority'],
                    status='todo',
                    created_at=datetime.utcnow()
                )
                db.session.add(user_story)
                total_sprint_points += story_data['points']
        
        # Update sprint points
        sprint.story_points = total_sprint_points
    
    db.session.commit()
    return project

def save_project_as_template(project):
    """Save an existing project as a reusable template"""
    template_data = {
        'sprints': []
    }
    
    for sprint in project.sprints:
        sprint_data = {
            'name': sprint.name,
            'goal': sprint.goal,
            'duration': sprint.duration,
            'epics': []
        }
        
        for epic in sprint.epics:
            epic_data = {
                'epic_id': epic.epic_id,
                'name': epic.name,
                'goal': epic.goal,
                'stories': []
            }
            
            for story in epic.user_stories:
                story_data = {
                    'title': story.title,
                    'description': story.description,
                    'points': story.story_points,
                    'priority': story.priority,
                    'prompt': story.acceptance_criteria
                }
                epic_data['stories'].append(story_data)
            
            sprint_data['epics'].append(epic_data)
        
        template_data['sprints'].append(sprint_data)
    
    template = ProjectTemplate(
        name=f"{project.name} Template",
        description=f"Template based on {project.name} project structure",
        project_type=project.project_type,
        template_data=json.dumps(template_data),
        created_at=datetime.utcnow()
    )
    
    db.session.add(template)
    db.session.commit()
    return template

def create_project_from_template(template, name, description=None):
    """Create a new project from a template"""
    template_data = json.loads(template.template_data)
    
    project = Project(
        name=name,
        description=description or template.description,
        project_type=template.project_type,
        status='active',
        created_from_template=template.id
    )
    db.session.add(project)
    db.session.flush()
    
    # Increment template usage count
    template.usage_count += 1
    
    # Create sprints, epics, and user stories from template
    for i, sprint_data in enumerate(template_data['sprints'], 1):
        sprint = Sprint(
            project=project,
            name=sprint_data['name'],
            goal=sprint_data['goal'],
            duration=sprint_data['duration'],
            status='planned',
            sprint_order=i,
            story_points=0
        )
        db.session.add(sprint)
        db.session.flush()
        
        total_sprint_points = 0
        
        for epic_data in sprint_data['epics']:
            epic = Epic(
                sprint=sprint,
                epic_id=epic_data['epic_id'],
                name=epic_data['name'],
                goal=epic_data['goal']
            )
            db.session.add(epic)
            db.session.flush()
            
            for j, story_data in enumerate(epic_data['stories'], 1):
                user_story = UserStory(
                    epic=epic,
                    story_id=f"{epic_data['epic_id']}-{j:03d}",
                    title=story_data['title'],
                    description=story_data['description'],
                    acceptance_criteria=story_data['prompt'],
                    story_points=story_data['points'],
                    priority=story_data['priority'],
                    status='todo',
                    created_at=datetime.utcnow()
                )
                db.session.add(user_story)
                total_sprint_points += story_data['points']
        
        sprint.story_points = total_sprint_points
    
    db.session.commit()
    return project

# Legacy import functions (keeping for backward compatibility)
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

# Initialize database and sample data
def init_app():
    """Initialize app with database and sample data"""
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created")
            
            if not Project.query.first():
                # Create a sample project using the new prompt-based system
                sample_project = create_project_from_prompt(
                    "CRM Assistant Project",
                    "Build a comprehensive CRM assistant with contact management, lead tracking, communication tools, and sales pipeline automation"
                )
                print("✅ Sample CRM project created using prompt generation")
                
                # Create some default templates
                crm_template_data = generate_project_structure('crm', 'CRM system', 'Template')
                crm_template = ProjectTemplate(
                    name="Standard CRM Template",
                    description="Complete CRM system with contact management, lead tracking, and communication tools",
                    project_type="crm",
                    template_data=json.dumps(crm_template_data),
                    created_by="system",
                    is_public=True
                )
                db.session.add(crm_template)
                
                ecommerce_template_data = generate_project_structure('ecommerce', 'Online store', 'Template')
                ecommerce_template = ProjectTemplate(
                    name="E-commerce Store Template",
                    description="Complete e-commerce solution with product catalog, shopping cart, and payment processing",
                    project_type="ecommerce",
                    template_data=json.dumps(ecommerce_template_data),
                    created_by="system",
                    is_public=True
                )
                db.session.add(ecommerce_template)
                
                mobile_template_data = generate_project_structure('mobile', 'Mobile app', 'Template')
                mobile_template = ProjectTemplate(
                    name="Mobile App Template",
                    description="Mobile application development with React Native",
                    project_type="mobile",
                    template_data=json.dumps(mobile_template_data),
                    created_by="system",
                    is_public=True
                )
                db.session.add(mobile_template)
                
                db.session.commit()
                print("✅ Default templates created")
                
            else:
                print("✅ Database already has data")
                
        except Exception as e:
            print(f"❌ Database initialization error: {e}")

# Main Routes

@app.route('/')
def dashboard():
    try:
        projects = Project.query.all()
        templates = ProjectTemplate.query.filter_by(is_public=True).limit(5).all()
        return render_template('dashboard.html', projects=projects, templates=templates)
    except Exception as e:
        print(f"Dashboard error: {e}")
        init_app()
        projects = Project.query.all()
        templates = ProjectTemplate.query.filter_by(is_public=True).limit(5).all()
        return render_template('dashboard.html', projects=projects, templates=templates)

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

# Prompt-based project creation routes

@app.route('/create-from-prompt')
def create_from_prompt_form():
    """Show form to create project from prompt"""
    return render_template('create_from_prompt.html')

@app.route('/create-from-prompt', methods=['POST'])
def create_from_prompt():
    """Create project from text prompt"""
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name or not description:
            flash('Project name and description are required', 'error')
            return redirect(url_for('create_from_prompt_form'))
        
        # Check if project name already exists
        existing = Project.query.filter_by(name=name).first()
        if existing:
            flash(f'Project "{name}" already exists', 'error')
            return redirect(url_for('create_from_prompt_form'))
        
        project = create_project_from_prompt(name, description)
        flash(f'Project "{project.name}" created successfully with {len(project.sprints)} sprints!', 'success')
        
        return redirect(url_for('project_detail', project_id=project.id))
        
    except Exception as e:
        flash(f'Error creating project: {str(e)}', 'error')
        return redirect(url_for('create_from_prompt_form'))

# Task prompt editing routes

@app.route('/user-story/<int:story_id>/edit-prompt')
def edit_story_prompt(story_id):
    """Show form to edit user story prompt"""
    story = UserStory.query.get_or_404(story_id)
    return render_template('edit_story_prompt.html', story=story)

@app.route('/user-story/<int:story_id>/edit-prompt', methods=['POST'])
def update_story_prompt(story_id):
    """Update user story prompt"""
    try:
        story = UserStory.query.get_or_404(story_id)
        new_prompt = request.form.get('prompt', '').strip()
        
        if not new_prompt:
            flash('Prompt cannot be empty', 'error')
            return redirect(url_for('edit_story_prompt', story_id=story_id))
        
        story.acceptance_criteria = new_prompt
        story.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Task prompt updated successfully!', 'success')
        return redirect(url_for('user_story_detail', story_id=story_id))
        
    except Exception as e:
        flash(f'Error updating prompt: {str(e)}', 'error')
        return redirect(url_for('edit_story_prompt', story_id=story_id))

# Template management routes

@app.route('/templates')
def template_list():
    """Show all available templates"""
    public_templates = ProjectTemplate.query.filter_by(is_public=True).order_by(ProjectTemplate.usage_count.desc()).all()
    return render_template('template_list.html', templates=public_templates)

@app.route('/template/<int:template_id>')
def template_detail(template_id):
    """Show template details"""
    template = ProjectTemplate.query.get_or_404(template_id)
    template_data = json.loads(template.template_data)
    return render_template('template_detail.html', template=template, template_data=template_data)

@app.route('/project/<int:project_id>/save-as-template')
def save_as_template_form(project_id):
    """Show form to save project as template"""
    project = Project.query.get_or_404(project_id)
    return render_template('save_as_template.html', project=project)

@app.route('/project/<int:project_id>/save-as-template', methods=['POST'])
def save_as_template(project_id):
    """Save project as template"""
    try:
        project = Project.query.get_or_404(project_id)
        template_name = request.form.get('template_name', '').strip()
        template_description = request.form.get('template_description', '').strip()
        is_public = request.form.get('is_public') == 'on'
        
        if not template_name:
            flash('Template name is required', 'error')
            return redirect(url_for('save_as_template_form', project_id=project_id))
        
        # Check if template name already exists
        existing = ProjectTemplate.query.filter_by(name=template_name).first()
        if existing:
            flash(f'Template "{template_name}" already exists', 'error')
            return redirect(url_for('save_as_template_form', project_id=project_id))
        
        template_data = {
            'sprints': []
        }
        
        for sprint in project.sprints:
            sprint_data = {
                'name': sprint.name,
                'goal': sprint.goal,
                'duration': sprint.duration,
                'epics': []
            }
            
            for epic in sprint.epics:
                epic_data = {
                    'epic_id': epic.epic_id,
                    'name': epic.name,
                    'goal': epic.goal,
                    'stories': []
                }
                
                for story in epic.user_stories:
                    story_data = {
                        'title': story.title,
                        'description': story.description,
                        'points': story.story_points,
                        'priority': story.priority,
                        'prompt': story.acceptance_criteria
                    }
                    epic_data['stories'].append(story_data)
                
                sprint_data['epics'].append(epic_data)
            
            template_data['sprints'].append(sprint_data)
        
        template = ProjectTemplate(
            name=template_name,
            description=template_description,
            project_type=project.project_type,
            template_data=json.dumps(template_data),
            is_public=is_public,
            created_at=datetime.utcnow()
        )
        
        db.session.add(template)
        db.session.commit()
        
        flash(f'Template "{template_name}" created successfully!', 'success')
        return redirect(url_for('template_detail', template_id=template.id))
        
    except Exception as e:
        flash(f'Error creating template: {str(e)}', 'error')
        return redirect(url_for('save_as_template_form', project_id=project_id))

@app.route('/create-from-template/<int:template_id>')
def create_from_template_form(template_id):
    """Show form to create project from template"""
    template = ProjectTemplate.query.get_or_404(template_id)
    return render_template('create_from_template.html', template=template)

@app.route('/create-from-template/<int:template_id>', methods=['POST'])
def create_from_template_post(template_id):
    """Create project from template"""
    try:
        template = ProjectTemplate.query.get_or_404(template_id)
        project_name = request.form.get('project_name', '').strip()
        project_description = request.form.get('project_description', '').strip()
        
        if not project_name:
            flash('Project name is required', 'error')
            return redirect(url_for('create_from_template_form', template_id=template_id))
        
        # Check if project name already exists
        existing = Project.query.filter_by(name=project_name).first()
        if existing:
            flash(f'Project "{project_name}" already exists', 'error')
            return redirect(url_for('create_from_template_form', template_id=template_id))
        
        project = create_project_from_template(template, project_name, project_description)
        
        flash(f'Project "{project.name}" created from template successfully!', 'success')
        return redirect(url_for('project_detail', project_id=project.id))
        
    except Exception as e:
        flash(f'Error creating project from template: {str(e)}', 'error')
        return redirect(url_for('create_from_template_form', template_id=template_id))

# Existing legacy routes (keeping for backward compatibility)

@app.route('/import-ringlypro')
def import_ringlypro_project():
    """Import RinglyPro CRM Enhancement project with full roadmap"""
    try:
        # Create or get the RinglyPro project
        project = Project.query.filter_by(name='RinglyPro CRM Enhancement').first()
        if not project:
            project = Project(
                name="RinglyPro CRM Enhancement",
                description="Comprehensive CRM system enhancement with database integration, communication tracking, and advanced features",
                status="active",
                project_type="crm"
            )
            db.session.add(project)
            db.session.flush()

        # Define sprint structure based on the roadmap
        sprint_data = [
            {
                "name": "Priority 1: Database Integration",
                "goal": "Move from In-Memory to PostgreSQL for production-ready data persistence",
                "duration": "2 weeks",
                "status": "planned",
                "epics": [
                    {
                        "epic_id": "DB1",
                        "name": "Database Models & Migration",
                        "goal": "Implement core database models with relationships",
                        "stories": [
                            {"title": "Implement Contact Model", "description": "Create Contact model with full database persistence, including fields for contact information, status, and metadata", "points": 8, "status": "todo", "priority": "high"},
                            {"title": "Create Appointment Model", "description": "Build Appointment model with foreign key relationships to contacts and proper scheduling fields", "points": 5, "status": "todo", "priority": "high"},
                            {"title": "Add Message/Call History Models", "description": "Design and implement models for tracking SMS messages and call logs with full history", "points": 8, "status": "todo", "priority": "medium"},
                            {"title": "Database Migration Scripts", "description": "Create migration scripts for production deployment and data conversion", "points": 5, "status": "todo", "priority": "medium"},
                            {"title": "Update API Endpoints", "description": "Refactor all API endpoints to use database instead of in-memory arrays", "points": 13, "status": "todo", "priority": "high"},
                        ]
                    }
                ]
            },
            # Additional sprint data would go here (truncated for brevity)
        ]
        
        # Create sprints, epics, and user stories
        stories_created = 0
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
                        priority=story_info["priority"],
                        created_at=datetime.utcnow()
                    )
                    db.session.add(user_story)
                    total_sprint_points += story_info["points"]
                    stories_created += 1
            
            # Update sprint points
            sprint.story_points = total_sprint_points
        
        db.session.commit()
        
        return f"✅ RinglyPro CRM Enhancement project imported successfully!<br>" \
               f"Created 1 sprint with {stories_created} user stories!<br>" \
               f"Total story points: {sum(sprint.story_points for sprint in project.sprints)}<br>" \
               f"<a href='/'>← Back to Dashboard</a>"
               
    except Exception as e:
        db.session.rollback()
        return f"❌ Error importing RinglyPro project: {e} <br><a href='/'>← Back to Dashboard</a>"

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

@app.route('/reset-and-import')
def reset_and_import():
    """Reset database and import sample stories with real user stories"""
    try:
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        # Create sample project using prompt generation
        project = create_project_from_prompt(
            "CRM Assistant Project", 
            "Build a comprehensive CRM assistant with contact management, lead tracking, communication tools, and sales pipeline automation"
        )
        
        # Count actual user stories created
        total_stories = UserStory.query.count()
        
        return f"✅ Database reset complete!<br>" \
               f"Created {len(project.sprints)} sprints with {total_stories} real user stories!<br>" \
               f"<a href='/'>← Back to Dashboard</a>"
               
    except Exception as e:
        db.session.rollback()
        return f"❌ Error: {e} <br><a href='/'>← Back to Dashboard</a>"

# API Routes

@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'status': p.status,
        'project_type': p.project_type,
        'sprint_count': len(p.sprints),
        'total_story_points': sum(s.story_points for s in p.sprints),
        'created_from_template': p.created_from_template
    } for p in projects])

@app.route('/api/projects', methods=['POST'])
def create_project_api():
    data = request.get_json()
    project = Project(
        name=data['name'],
        description=data.get('description', ''),
        status=data.get('status', 'active'),
        project_type=data.get('project_type', 'general')
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
    project.project_type = data.get('project_type', project.project_type)
    
    db.session.commit()
    return jsonify({'message': 'Project updated successfully'})

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted successfully'})

@app.route('/api/user-stories/<int:story_id>/prompt', methods=['PUT'])
def update_story_prompt_api(story_id):
    """API endpoint to update user story prompt"""
    try:
        story = UserStory.query.get_or_404(story_id)
        data = request.get_json()
        
        new_prompt = data.get('prompt', '').strip()
        if not new_prompt:
            return jsonify({'error': 'Prompt cannot be empty'}), 400
        
        story.acceptance_criteria = new_prompt
        story.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Task prompt updated successfully',
            'story_id': story.id,
            'updated_at': story.updated_at.isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates', methods=['GET'])
def get_templates():
    """API endpoint to get all templates"""
    templates = ProjectTemplate.query.filter_by(is_public=True).all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'description': t.description,
        'project_type': t.project_type,
        'usage_count': t.usage_count,
        'created_at': t.created_at.isoformat()
    } for t in templates])

@app.route('/api/templates/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    """API endpoint to delete a template"""
    try:
        template = ProjectTemplate.query.get_or_404(template_id)
        db.session.delete(template)
        db.session.commit()
        return jsonify({'message': 'Template deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        'average_points_per_sprint': round(total_story_points / total_sprints, 2) if total_sprints > 0 else 0,
        'project_type': project.project_type
    })

# Run app
if __name__ == '__main__':
    init_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')
