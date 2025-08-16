# init_db.py - Database initialization script
from app import app, db, Project, Sprint, Epic, UserStory, Risk
import json

def init_database():
    """Initialize database with sample data from the project plan"""
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Clear existing data
        db.session.query(UserStory).delete()
        db.session.query(Epic).delete()
        db.session.query(Sprint).delete()
        db.session.query(Risk).delete()
        db.session.query(Project).delete()
        db.session.commit()
        
        # Create the main project
        project = Project(
            name="CRM Assistant Project",
            description="Build a comprehensive CRM assistant with MCP server, backend API, and chat interface",
            status="active"
        )
        db.session.add(project)
        db.session.commit()
        
        # Sprint 1: Foundation & Setup
        sprint1 = Sprint(
            project_id=project.id,
            name="Sprint 1: Foundation & Setup",
            goal="Establish project foundation with development environment and Railway infrastructure",
            duration="3 Days (Days 1-3)",
            status="completed",
            story_points=33
        )
        db.session.add(sprint1)
        db.session.commit()
        
        # Epic 1.1: Development Environment Setup
        epic1_1 = Epic(
            sprint_id=sprint1.id,
            epic_id="1.1",
            name="Development Environment Setup",
            goal="Create a robust development environment for the team"
        )
        db.session.add(epic1_1)
        db.session.commit()
        
        # User Stories for Epic 1.1
        stories_1_1 = [
            {
                "story_id": "US-001",
                "title": "Repository Creation",
                "description": "As a developer, I want a centralized GitHub repository so that the team can collaborate effectively",
                "acceptance_criteria": [
                    "GitHub repository created with appropriate permissions",
                    "README.md with project overview",
                    "Initial branch protection rules configured",
                    "Team members have appropriate access levels"
                ],
                "story_points": 2,
                "status": "done"
            },
            {
                "story_id": "US-002",
                "title": "Local Development Environment",
                "description": "As a developer, I want a standardized local development setup so that all team members work in consistent environments",
                "acceptance_criteria": [
                    "Node.js 20+ installed and verified",
                    "Package manager (npm/yarn) configured",
                    "Environment works on Windows, Mac, and Linux",
                    "Setup documentation created"
                ],
                "story_points": 3,
                "status": "done"
            },
            {
                "story_id": "US-003",
                "title": "Railway CLI Setup",
                "description": "As a developer, I want Railway CLI configured so that I can deploy and manage cloud infrastructure",
                "acceptance_criteria": [
                    "Railway CLI installed and authenticated",
                    "Access to Railway projects verified",
                    "Deployment commands documented",
                    "Team accounts configured"
                ],
                "story_points": 2,
                "status": "done"
            },
            {
                "story_id": "US-004",
                "title": "Environment Configuration",
                "description": "As a developer, I want environment variable management so that sensitive data is handled securely",
                "acceptance_criteria": [
                    ".env.example file created with all required variables",
                    "Environment variable documentation",
                    "Local and production environment separation",
                    "Security best practices documented"
                ],
                "story_points": 2,
                "status": "done"
            },
            {
                "story_id": "US-005",
                "title": "Code Quality Tools",
                "description": "As a developer, I want automated code quality checks so that code remains consistent and maintainable",
                "acceptance_criteria": [
                    "ESLint configuration for TypeScript",
                    "Prettier configuration for formatting",
                    "Pre-commit hooks configured",
                    "CI integration for quality checks"
                ],
                "story_points": 3,
                "status": "done"
            },
            {
                "story_id": "US-006",
                "title": "Git Workflow",
                "description": "As a developer, I want a standardized git workflow so that code integration is smooth and traceable",
                "acceptance_criteria": [
                    "Git flow branching strategy documented",
                    "Branch naming conventions established",
                    "Pull request templates created",
                    "Code review process defined"
                ],
                "story_points": 2,
                "status": "done"
            }
        ]
        
        for story_data in stories_1_1:
            story = UserStory(
                epic_id=epic1_1.id,
                story_id=story_data["story_id"],
                title=story_data["title"],
                description=story_data["description"],
                acceptance_criteria=json.dumps(story_data["acceptance_criteria"]),
                story_points=story_data["story_points"],
                status=story_data["status"]
            )
            db.session.add(story)
        
        # Epic 1.2: Project Architecture
        epic1_2 = Epic(
            sprint_id=sprint1.id,
            epic_id="1.2",
            name="Project Architecture",
            goal="Define and implement the overall project structure"
        )
        db.session.add(epic1_2)
        db.session.commit()
        
        # User Stories for Epic 1.2
        stories_1_2 = [
            {
                "story_id": "US-007",
                "title": "Monorepo Structure",
                "description": "As a developer, I want a clear project structure so that different components are organized logically",
                "acceptance_criteria": [
                    "/mcp-server, /backend, /frontend directories created",
                    "Each component has its own package.json",
                    "Shared dependencies managed efficiently",
                    "Build scripts for each component"
                ],
                "story_points": 3,
                "status": "done"
            },
            {
                "story_id": "US-008",
                "title": "TypeScript Configuration",
                "description": "As a developer, I want TypeScript setup so that code is type-safe and maintainable",
                "acceptance_criteria": [
                    "TypeScript configuration for each component",
                    "Shared types/interfaces directory",
                    "Build process configured",
                    "Type checking in CI pipeline"
                ],
                "story_points": 2,
                "status": "done"
            },
            {
                "story_id": "US-009",
                "title": "Package Management",
                "description": "As a developer, I want efficient dependency management so that builds are fast and reliable",
                "acceptance_criteria": [
                    "npm workspaces configured",
                    "Dependency hoisting working correctly",
                    "Lock files managed properly",
                    "Scripts for installing dependencies"
                ],
                "story_points": 2,
                "status": "done"
            }
        ]
        
        for story_data in stories_1_2:
            story = UserStory(
                epic_id=epic1_2.id,
                story_id=story_data["story_id"],
                title=story_data["title"],
                description=story_data["description"],
                acceptance_criteria=json.dumps(story_data["acceptance_criteria"]),
                story_points=story_data["story_points"],
                status=story_data["status"]
            )
            db.session.add(story)
        
        # Epic 1.3: Railway Infrastructure
        epic1_3 = Epic(
            sprint_id=sprint1.id,
            epic_id="1.3",
            name="Railway Infrastructure",
            goal="Set up cloud hosting and deployment pipeline"
        )
        db.session.add(epic1_3)
        db.session.commit()
        
        # User Stories for Epic 1.3
        stories_1_3 = [
            {
                "story_id": "US-010",
                "title": "Railway Project Setup",
                "description": "As a DevOps engineer, I want Railway projects configured so that applications can be hosted in the cloud",
                "acceptance_criteria": [
                    "Railway project for MCP server created",
                    "Railway project for backend API created",
                    "Basic deployment configuration",
                    "Resource limits configured"
                ],
                "story_points": 3,
                "status": "done"
            },
            {
                "story_id": "US-011",
                "title": "Environment Variables",
                "description": "As a DevOps engineer, I want secure environment variable management so that sensitive data is protected",
                "acceptance_criteria": [
                    "Environment variables configured in Railway dashboard",
                    "Staging and production environments separated",
                    "API keys and secrets properly managed",
                    "Documentation for variable management"
                ],
                "story_points": 2,
                "status": "done"
            },
            {
                "story_id": "US-012",
                "title": "Deployment Pipeline",
                "description": "As a developer, I want automated deployments so that code changes reach production efficiently",
                "acceptance_criteria": [
                    "GitHub integration configured",
                    "Automatic deployments from main branch",
                    "Manual deployment triggers available",
                    "Rollback capability implemented"
                ],
                "story_points": 5,
                "status": "done"
            }
        ]
        
        for story_data in stories_1_3:
            story = UserStory(
                epic_id=epic1_3.id,
                story_id=story_data["story_id"],
                title=story_data["title"],
                description=story_data["description"],
                acceptance_criteria=json.dumps(story_data["acceptance_criteria"]),
                story_points=story_data["story_points"],
                status=story_data["status"]
            )
            db.session.add(story)
        
        # Sprint 2: MCP Server Foundation
        sprint2 = Sprint(
            project_id=project.id,
            name="Sprint 2: MCP Server Foundation",
            goal="Build the core MCP server with basic functionality and Spark CRM integration",
            duration="5 Days (Days 4-8)",
            status="in-progress",
            story_points=39
        )
        db.session.add(sprint2)
        db.session.commit()
        
        # Epic 2.1: MCP Server Core
        epic2_1 = Epic(
            sprint_id=sprint2.id,
            epic_id="2.1",
            name="MCP Server Core",
            goal="Implement the foundational MCP server infrastructure"
        )
        db.session.add(epic2_1)
        db.session.commit()
        
        # User Stories for Epic 2.1
        stories_2_1 = [
            {
                "story_id": "US-013",
                "title": "MCP Server Framework",
                "description": "As a system architect, I want a robust MCP server foundation so that tools can be built reliably",
                "acceptance_criteria": [
                    "@modelcontextprotocol/sdk integrated",
                    "Server initialization logic implemented",
                    "Configuration management system",
                    "Server starts without errors"
                ],
                "story_points": 5,
                "status": "in-progress"
            },
            {
                "story_id": "US-014",
                "title": "Error Handling System",
                "description": "As a developer, I want comprehensive error handling so that the system fails gracefully",
                "acceptance_criteria": [
                    "Global error handler implemented",
                    "Structured logging system",
                    "Error categorization and reporting",
                    "Graceful degradation for failures"
                ],
                "story_points": 3,
                "status": "todo"
            },
            {
                "story_id": "US-015",
                "title": "Health Monitoring",
                "description": "As a DevOps engineer, I want health check endpoints so that system status can be monitored",
                "acceptance_criteria": [
                    "Health check endpoint returns system status",
                    "Dependency health checks (database, API)",
                    "Metrics collection for monitoring",
                    "Alerting integration ready"
                ],
                "story_points": 3,
                "status": "todo"
            },
            {
                "story_id": "US-016",
                "title": "Server Lifecycle",
                "description": "As a system administrator, I want proper server lifecycle management so that deployments are smooth",
                "acceptance_criteria": [
                    "Graceful shutdown handling",
                    "Process signal handling",
                    "Resource cleanup on shutdown",
                    "Start/stop scripts created"
                ],
                "story_points": 2,
                "status": "todo"
            }
        ]
        
        for story_data in stories_2_1:
            story = UserStory(
                epic_id=epic2_1.id,
                story_id=story_data["story_id"],
                title=story_data["title"],
                description=story_data["description"],
                acceptance_criteria=json.dumps(story_data["acceptance_criteria"]),
                story_points=story_data["story_points"],
                status=story_data["status"]
            )
            db.session.add(story)
        
        # Add more sprints here...
        # For brevity, I'm including just the first two sprints
        # You can add Sprint 3-7 following the same pattern
        
        # Add Risks
        risks_data = [
            {
                "title": "Claude API tool definitions",
                "description": "Complex integration with Claude API for tool definitions may require significant technical research and prototyping",
                "severity": "high",
                "mitigation": "Early prototyping and technical spikes"
            },
            {
                "title": "WebSocket real-time updates",
                "description": "Technical complexity in implementing real-time WebSocket communication may impact timeline",
                "severity": "high",
                "mitigation": "Technical spikes for unknown areas"
            },
            {
                "title": "Load testing",
                "description": "Performance requirements may be challenging to meet under expected load",
                "severity": "high",
                "mitigation": "Regular performance monitoring and optimization"
            },
            {
                "title": "CI/CD pipeline",
                "description": "Deployment dependencies may cause delays in release schedule",
                "severity": "high",
                "mitigation": "Contingency planning for critical features"
            }
        ]
        
        for risk_data in risks_data:
            risk = Risk(
                project_id=project.id,
                title=risk_data["title"],
                description=risk_data["description"],
                severity=risk_data["severity"],
                mitigation=risk_data["mitigation"],
                status="open"
            )
            db.session.add(risk)
        
        db.session.commit()
        print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()