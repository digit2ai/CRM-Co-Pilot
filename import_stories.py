# import_stories.py - Import user stories from CSV to database
import csv
import re
from app import app, db, Project, Sprint, Epic, UserStory
from datetime import datetime

def extract_epic_info(summary, description):
    """Extract epic name from summary and description"""
    # Extract epic name from summary like "[Foundation] Repository Creation"
    epic_match = re.match(r'\[([^\]]+)\]', summary)
    if epic_match:
        return epic_match.group(1)
    
    # Extract from description like "EPIC: Foundation & Infrastructure"
    epic_match = re.search(r'EPIC:\s*([^.]+)', description)
    if epic_match:
        return epic_match.group(1).strip()
    
    return "General"

def extract_sprint_info(labels):
    """Extract sprint information from labels"""
    sprint_match = re.search(r'sprint(\d+)', labels)
    if sprint_match:
        return int(sprint_match.group(1))
    return 1  # Default to sprint 1

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
        story_points=0  # Will be calculated later
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
    
    # Base points by priority
    priority_points = {
        'High': 5,
        'Medium': 3,
        'Low': 2
    }
    base_points = priority_points.get(priority, 3)
    
    # Complexity indicators
    complexity_keywords = {
        'setup': 2, 'configuration': 2, 'framework': 3, 'integration': 3,
        'authentication': 3, 'security': 3, 'testing': 2, 'deployment': 3,
        'monitoring': 2, 'documentation': 1, 'api': 2, 'database': 3
    }
    
    complexity_bonus = 0
    for keyword, points in complexity_keywords.items():
        if keyword in text:
            complexity_bonus += points
            break  # Only add one bonus
    
    return min(base_points + complexity_bonus, 13)  # Cap at 13 points

def import_user_stories():
    """Main function to import user stories"""
    
    # Sprint definitions based on the CSV data
    sprint_definitions = {
        1: {
            'name': 'Sprint 1: Foundation & Infrastructure',
            'goal': 'Establish project foundation with development environment and infrastructure',
            'duration': '2 weeks',
            'status': 'completed'
        },
        2: {
            'name': 'Sprint 2: MCP Server Core',
            'goal': 'Build the core MCP server with basic functionality',
            'duration': '2 weeks', 
            'status': 'in-progress'
        },
        3: {
            'name': 'Sprint 3: Core MCP Tools',
            'goal': 'Implement essential MCP tools for CRM operations',
            'duration': '2 weeks',
            'status': 'planned'
        },
        4: {
            'name': 'Sprint 4: Claude Integration & Backend',
            'goal': 'Integrate Claude AI and build backend services',
            'duration': '2 weeks',
            'status': 'planned'
        },
        5: {
            'name': 'Sprint 5: Frontend Development',
            'goal': 'Build React frontend for user interactions',
            'duration': '2 weeks',
            'status': 'planned'
        },
        6: {
            'name': 'Sprint 6: Testing & Quality Assurance',
            'goal': 'Comprehensive testing and quality assurance',
            'duration': '2 weeks',
            'status': 'planned'
        },
        7: {
            'name': 'Sprint 7: Deployment & Documentation',
            'goal': 'Production deployment and documentation',
            'duration': '1 week',
            'status': 'planned'
        }
    }
    
    # Epic definitions
    epic_definitions = {
        'Foundation': {
            'epic_id': 'FND',
            'name': 'Foundation & Infrastructure',
            'goal': 'Establish project foundation with development environment and infrastructure setup'
        },
        'MCP Core': {
            'epic_id': 'MCP',
            'name': 'MCP Server Core',
            'goal': 'Build the core MCP server framework with essential functionality'
        },
        'Core MCP Tools': {
            'epic_id': 'MCT',
            'name': 'Core MCP Tools', 
            'goal': 'Implement essential MCP tools for CRM operations and member management'
        },
        'Claude Integration & Backend': {
            'epic_id': 'CIB',
            'name': 'Claude Integration & Backend',
            'goal': 'Integrate Claude AI and build robust backend services'
        },
        'Frontend Development': {
            'epic_id': 'FED',
            'name': 'Frontend Development',
            'goal': 'Build React frontend for user interactions and chat interface'
        },
        'Testing & Quality Assurance': {
            'epic_id': 'TQA',
            'name': 'Testing & Quality Assurance',
            'goal': 'Comprehensive testing and quality assurance across all components'
        },
        'Deployment & Documentation': {
            'epic_id': 'DD',
            'name': 'Deployment & Documentation',
            'goal': 'Production deployment and comprehensive documentation'
        }
    }

    with app.app_context():
        try:
            # Get or create the CRM project
            project = Project.query.filter_by(name='CRM Assistant Project').first()
            if not project:
                project = Project(
                    name='CRM Assistant Project',
                    description='Build a comprehensive CRM assistant with MCP server, backend API, and chat interface',
                    status='active'
                )
                db.session.add(project)
                db.session.flush()
            
            # Clear existing sprints for clean import (optional - remove if you want to keep existing data)
            # Sprint.query.filter_by(project_id=project.id).delete()
            # db.session.flush()
            
            # CSV data as string (the data from your paste)
            csv_data = """Issue Type,Summary,Description,Priority,Labels
Story,[Foundation] Repository Creation,"EPIC: Foundation & Infrastructure. As a developer, I want a centralized GitHub repository so that the team can collaborate effectively. Acceptance Criteria: GitHub repository created with appropriate permissions, README.md with project overview, Initial branch protection rules configured, Team members have appropriate access levels",High,"git,repository,sprint1,foundation"
Story,[Foundation] Local Development Environment,"EPIC: Foundation & Infrastructure. As a developer, I want a standardized local development setup so that all team members work in consistent environments. Acceptance Criteria: Node.js 20+ installed and verified, Package manager configured, Environment works on Windows/Mac/Linux, Setup documentation created",High,"setup,nodejs,sprint1,foundation"
Story,[Foundation] Railway CLI Setup,"EPIC: Foundation & Infrastructure. As a developer, I want Railway CLI configured so that I can deploy and manage cloud infrastructure. Acceptance Criteria: Railway CLI installed and authenticated, Access to Railway projects verified, Deployment commands documented, Team accounts configured",High,"railway,cli,sprint1,foundation"
Story,[Foundation] Environment Configuration,"EPIC: Foundation & Infrastructure. As a developer, I want environment variable management so that sensitive data is handled securely. Acceptance Criteria: .env.example file created, Environment variable documentation, Local and production separation, Security best practices documented",High,"env,config,sprint1,foundation"
Story,[Foundation] Code Quality Tools,"EPIC: Foundation & Infrastructure. As a developer, I want automated code quality checks so that code remains consistent and maintainable. Acceptance Criteria: ESLint configuration for TypeScript, Prettier configuration, Pre-commit hooks configured, CI integration for quality checks",High,"eslint,prettier,sprint1,foundation"
Story,[Foundation] Git Workflow,"EPIC: Foundation & Infrastructure. As a developer, I want a standardized git workflow so that code integration is smooth and traceable. Acceptance Criteria: Git flow branching strategy documented, Branch naming conventions established, Pull request templates created, Code review process defined",High,"git,workflow,sprint1,foundation"
Story,[Foundation] Monorepo Structure,"EPIC: Foundation & Infrastructure. As a developer, I want a clear project structure so that different components are organized logically. Acceptance Criteria: /mcp-server /backend /frontend directories created, Each component has package.json, Shared dependencies managed efficiently, Build scripts for each component",High,"monorepo,structure,sprint1,foundation"
Story,[Foundation] TypeScript Configuration,"EPIC: Foundation & Infrastructure. As a developer, I want TypeScript setup so that code is type-safe and maintainable. Acceptance Criteria: TypeScript configuration for each component, Shared types/interfaces directory, Build process configured, Type checking in CI pipeline",High,"typescript,config,sprint1,foundation"
Story,[Foundation] Package Management,"EPIC: Foundation & Infrastructure. As a developer, I want efficient dependency management so that builds are fast and reliable. Acceptance Criteria: npm workspaces configured, Dependency hoisting working correctly, Lock files managed properly, Scripts for installing dependencies",High,"npm,packages,sprint1,foundation"
Story,[Foundation] Railway Project Setup,"EPIC: Foundation & Infrastructure. As a DevOps engineer, I want Railway projects configured so that applications can be hosted in the cloud. Acceptance Criteria: Railway project for MCP server created, Railway project for backend API created, Basic deployment configuration, Resource limits configured",High,"railway,hosting,sprint1,foundation"
Story,[Foundation] Environment Variables,"EPIC: Foundation & Infrastructure. As a DevOps engineer, I want secure environment variable management so that sensitive data is protected. Acceptance Criteria: Environment variables configured in Railway dashboard, Staging and production environments separated, API keys and secrets properly managed, Documentation for variable management",High,"env,secrets,sprint1,foundation"
Story,[Foundation] Deployment Pipeline,"EPIC: Foundation & Infrastructure. As a developer, I want automated deployments so that code changes reach production efficiently. Acceptance Criteria: GitHub integration configured, Automatic deployments from main branch, Manual deployment triggers available, Rollback capability implemented",High,"cicd,pipeline,sprint1,foundation"
Story,[MCP Core] MCP Server Framework,"EPIC: MCP Server Core. As a system architect, I want a robust MCP server foundation so that tools can be built reliably. Acceptance Criteria: @modelcontextprotocol/sdk integrated, Server initialization logic implemented, Configuration management system, Server starts without errors",High,"mcp,framework,sprint2,mcp-core"
Story,[MCP Core] Error Handling System,"EPIC: MCP Server Core. As a developer, I want comprehensive error handling so that the system fails gracefully. Acceptance Criteria: Global error handler implemented, Structured logging system, Error categorization and reporting, Graceful degradation for failures",High,"error,handling,sprint2,mcp-core"
Story,[MCP Core] Health Monitoring,"EPIC: MCP Server Core. As a DevOps engineer, I want health check endpoints so that system status can be monitored. Acceptance Criteria: Health check endpoint returns system status, Dependency health checks, Metrics collection for monitoring, Alerting integration ready",High,"health,monitoring,sprint2,mcp-core"
Story,[MCP Core] Server Lifecycle,"EPIC: MCP Server Core. As a system administrator, I want proper server lifecycle management so that deployments are smooth. Acceptance Criteria: Graceful shutdown handling, Process signal handling, Resource cleanup on shutdown, Start/stop scripts created",High,"lifecycle,management,sprint2,mcp-core"
Story,[MCP Core] API Client Foundation,"EPIC: MCP Server Core. As a developer, I want a robust API client so that communication with Spark CRM is reliable. Acceptance Criteria: HTTP client configured with proper timeouts, Authentication mechanism implemented, Base URL and endpoint configuration, Request/response logging",High,"api,client,sprint2,mcp-core"
Story,[MCP Core] Authentication System,"EPIC: MCP Server Core. As a security engineer, I want secure API authentication so that CRM data is protected. Acceptance Criteria: API key management system, Token refresh mechanism, Authentication failure handling, Security audit trail",High,"auth,api,sprint2,mcp-core"
Story,[MCP Core] Request Interceptors,"EPIC: MCP Server Core. As a developer, I want request/response interceptors so that API calls are logged and monitored. Acceptance Criteria: Request logging with correlation IDs, Response time measurement, Error response logging, Debug mode for development",High,"interceptors,logging,sprint2,mcp-core"
Story,[MCP Core] Resilience Features,"EPIC: MCP Server Core. As a system engineer, I want API resilience features so that temporary failures don't break the system. Acceptance Criteria: Retry logic with exponential backoff, Circuit breaker pattern implementation, Rate limiting handler, Fallback mechanisms",High,"resilience,retry,sprint2,mcp-core"
Story,[MCP Core] Mock API System,"EPIC: MCP Server Core. As a developer, I want mock API responses so that development can continue without CRM dependency. Acceptance Criteria: Mock response system for all endpoints, Realistic test data, Toggle between mock and real API, Mock data management tools",High,"mock,testing,sprint2,mcp-core"
Story,[MCP Core] Express Server Setup,"EPIC: MCP Server Core. As a developer, I want an HTTP interface so that the MCP server can be accessed via REST API. Acceptance Criteria: Express.js server configured, CORS middleware configured, Request validation middleware, Error handling middleware",High,"express,http,sprint2,mcp-core"
Story,[MCP Core] WebSocket Server,"EPIC: MCP Server Core. As a developer, I want real-time communication so that clients can receive immediate updates. Acceptance Criteria: WebSocket server implementation, Connection management, Message broadcasting, Connection authentication",High,"websocket,realtime,sprint2,mcp-core"
Story,[MCP Core] Request Logging,"EPIC: MCP Server Core. As a DevOps engineer, I want comprehensive request logging so that API usage can be monitored. Acceptance Criteria: Morgan logging middleware, Request correlation IDs, Performance metrics logging, Log aggregation ready",High,"logging,monitoring,sprint2,mcp-core"
Story,[MCP Tools] Get Attendance Tool,"EPIC: Core MCP Tools. As a gym staff member, I want to check member attendance so that I can track member engagement. Acceptance Criteria: Tool accepts member name/ID and date range, Returns formatted attendance records, Handles partial name matches, Provides clear error messages for no results",High,"attendance,tool,sprint3,mcp-tools"
Story,[MCP Tools] Member Search Logic,"EPIC: Core MCP Tools. As a gym staff member, I want flexible member search so that I can find members easily. Acceptance Criteria: Search by name/email/member ID, Fuzzy matching for misspelled names, Multiple match handling, Case-insensitive search",High,"search,members,sprint3,mcp-tools"
Story,[MCP Tools] Attendance Query Function,"EPIC: Core MCP Tools. As a developer, I want efficient attendance queries so that responses are fast. Acceptance Criteria: Optimized API calls to Spark CRM, Date range validation, Result caching for common queries, Pagination for large result sets",High,"query,performance,sprint3,mcp-tools"
Story,[MCP Tools] Payment Status Checker,"EPIC: Core MCP Tools. As a gym staff member, I want to check payment status so that I can help members with billing questions. Acceptance Criteria: Tool accepts member identifier, Returns current payment status, Shows upcoming payment dates, Handles multiple membership types",High,"payment,status,sprint3,mcp-tools"
Story,[MCP Tools] Multiple Member Handling,"EPIC: Core MCP Tools. As a gym staff member, I want to handle multiple members with similar names so that I check the right person. Acceptance Criteria: Disambiguation interface for multiple matches, Member details display for identification, Clear selection process, Error prevention for wrong member selection",High,"disambiguation,members,sprint3,mcp-tools"
Story,[MCP Tools] Payment History Display,"EPIC: Core MCP Tools. As a gym staff member, I want to see payment history so that I can track member payment patterns. Acceptance Criteria: Recent payment history display, Payment method information, Failed payment notifications, Date formatting in user-friendly format",High,"payment,history,sprint3,mcp-tools"
Story,[MCP Tools] Missing Attendance Report,"EPIC: Core MCP Tools. As a gym manager, I want missing attendance reports so that I can identify members who haven't visited recently. Acceptance Criteria: Tool accepts date range parameters, Generates clickable report URLs, Handles different date formats, Provides report descriptions",High,"report,attendance,sprint3,mcp-tools"
Story,[MCP Tools] MTD Collections Tool,"EPIC: Core MCP Tools. As a gym manager, I want month-to-date collection reports so that I can track revenue performance. Acceptance Criteria: Calculates current month-to-date automatically, Formats currency values properly, Compares to previous month, Provides percentage changes",High,"collections,mtd,sprint3,mcp-tools"
Story,[MCP Tools] Date Range Processing,"EPIC: Core MCP Tools. As a developer, I want robust date handling so that all date inputs are processed correctly. Acceptance Criteria: Multiple date format support, Timezone handling, Date validation, Relative date processing",High,"date,processing,sprint3,mcp-tools"
Story,[MCP Tools] Email Update Tool,"EPIC: Core MCP Tools. As a gym staff member, I want to update member emails so that members receive important communications. Acceptance Criteria: Email validation before update, Confirmation dialog for changes, Rollback capability if needed, Audit logging for all changes",High,"email,update,sprint3,mcp-tools"
Story,[MCP Tools] Update Validation System,"EPIC: Core MCP Tools. As a developer, I want comprehensive validation so that only valid data is saved. Acceptance Criteria: Email format validation, Duplicate email checking, Required field validation, Data sanitization",High,"validation,data,sprint3,mcp-tools"
Story,[MCP Tools] Audit Logging,"EPIC: Core MCP Tools. As a compliance officer, I want audit trails so that all data changes are tracked. Acceptance Criteria: All updates logged with timestamp, User identification in logs, Before/after value logging, Tamper-proof log storage",High,"audit,logging,sprint3,mcp-tools"
Story,[MCP Tools] Unit Test Suite,"EPIC: Core MCP Tools. As a developer, I want comprehensive unit tests so that tool reliability is ensured. Acceptance Criteria: 80%+ code coverage for all tools, Mock API integration for tests, Edge case testing, Performance benchmarking",High,"testing,unit,sprint3,mcp-tools"
Story,[MCP Tools] Integration Testing,"EPIC: Core MCP Tools. As a QA engineer, I want integration tests so that tool interactions work correctly. Acceptance Criteria: End-to-end tool execution tests, Error scenario testing, API failure simulation, Load testing for concurrent requests",High,"testing,integration,sprint3,mcp-tools"
Story,[Claude Backend] Express Application Setup,"EPIC: Claude Integration & Backend. As a backend developer, I want a well-configured Express app so that API development is efficient. Acceptance Criteria: Express.js with TypeScript configuration, Middleware stack properly configured, Build process and hot reload, Development vs production configurations",High,"express,setup,sprint4,claude-backend"
Story,[Claude Backend] API Middleware Stack,"EPIC: Claude Integration & Backend. As a security engineer, I want proper middleware so that the API is secure and reliable. Acceptance Criteria: CORS configuration for frontend access, Body parser for JSON requests, Request rate limiting, Security headers middleware",High,"middleware,security,sprint4,claude-backend"
Story,[Claude Backend] Error Handling Middleware,"EPIC: Claude Integration & Backend. As a developer, I want centralized error handling so that API errors are consistent. Acceptance Criteria: Global error handler, Error response standardization, Error logging and monitoring, Development vs production error details",High,"error,middleware,sprint4,claude-backend"
Story,[Claude Backend] API Documentation,"EPIC: Claude Integration & Backend. As a frontend developer, I want API documentation so that I can integrate effectively. Acceptance Criteria: Swagger/OpenAPI documentation, Interactive API explorer, Request/response examples, Authentication documentation",High,"api,docs,sprint4,claude-backend"
Story,[Claude Backend] Anthropic SDK Setup,"EPIC: Claude Integration & Backend. As a developer, I want Claude integration so that natural language queries can be processed. Acceptance Criteria: Anthropic SDK installed and configured, API key management, Rate limiting compliance, Error handling for API failures",High,"claude,sdk,sprint4,claude-backend"
Story,[Claude Backend] Tool Definitions for Claude,"EPIC: Claude Integration & Backend. As an AI engineer, I want tool definitions so that Claude can call MCP server functions. Acceptance Criteria: Tool schemas defined for all MCP tools, Parameter validation for tool calls, Tool descriptions for Claude understanding, Error handling for invalid tool calls",High,"tools,claude,sprint4,claude-backend"
Story,[Claude Backend] Conversation Context Manager,"EPIC: Claude Integration & Backend. As a user, I want conversation context so that follow-up questions work naturally. Acceptance Criteria: Conversation state management, Context window optimization, Memory cleanup for long conversations, Context persistence across sessions",High,"context,conversation,sprint4,claude-backend"
Story,[Claude Backend] Streaming Response Support,"EPIC: Claude Integration & Backend. As a user, I want real-time responses so that I see answers as they're generated. Acceptance Criteria: Server-sent events implementation, Streaming response parsing, Progress indicators for long operations, Error handling during streaming",High,"streaming,realtime,sprint4,claude-backend"
Story,[Claude Backend] Main Chat Endpoint,"EPIC: Claude Integration & Backend. As a user, I want a chat endpoint so that I can have conversations with the AI assistant. Acceptance Criteria: POST /api/chat endpoint created, Message parsing and validation, Claude API integration, Response formatting",High,"chat,endpoint,sprint4,claude-backend"
Story,[Claude Backend] Tool Execution Orchestration,"EPIC: Claude Integration & Backend. As a developer, I want tool execution orchestration so that Claude can call MCP tools seamlessly. Acceptance Criteria: Tool call parsing from Claude responses, MCP server communication, Tool result formatting for Claude, Error propagation to user",High,"orchestration,tools,sprint4,claude-backend"
Story,[Claude Backend] Conversation Retrieval,"EPIC: Claude Integration & Backend. As a user, I want to retrieve past conversations so that I can continue where I left off. Acceptance Criteria: GET /api/conversation/:id endpoint, Conversation storage system, Pagination for long conversations, Access control for conversation data",High,"conversation,retrieval,sprint4,claude-backend"
Story,[Claude Backend] Response Caching,"EPIC: Claude Integration & Backend. As a system engineer, I want response caching so that common queries are fast. Acceptance Criteria: Cache layer for frequent queries, Cache invalidation strategy, Performance improvement measurement, Cache hit rate monitoring",High,"caching,performance,sprint4,claude-backend"
Story,[Claude Backend] JWT Authentication,"EPIC: Claude Integration & Backend. As a security engineer, I want JWT authentication so that API access is controlled. Acceptance Criteria: JWT token generation and validation, Token expiration handling, Refresh token mechanism, Secure token storage recommendations",High,"jwt,auth,sprint4,claude-backend"
Story,[Claude Backend] Role-Based Access Control,"EPIC: Claude Integration & Backend. As an administrator, I want role-based access so that users only access appropriate features. Acceptance Criteria: User roles defined, Tool access permissions by role, Middleware for permission checking, Admin interface for role management",High,"rbac,permissions,sprint4,claude-backend"
Story,[Claude Backend] Session Management,"EPIC: Claude Integration & Backend. As a user, I want secure sessions so that my login state is maintained safely. Acceptance Criteria: Session creation and validation, Session timeout handling, Concurrent session management, Session cleanup processes",High,"session,management,sprint4,claude-backend"
Story,[Claude Backend] Permission Checking System,"EPIC: Claude Integration & Backend. As a security engineer, I want permission checks so that users can only execute authorized tools. Acceptance Criteria: Pre-execution permission validation, Tool-specific permission rules, Permission denial logging, Admin override capabilities",High,"permissions,security,sprint4,claude-backend"
Story,[Claude Backend] Confirmation Flow for Write Operations,"EPIC: Claude Integration & Backend. As a user, I want confirmation for data changes so that accidental modifications are prevented. Acceptance Criteria: Confirmation dialog for write operations, Change preview before execution, User confirmation tracking, Timeout for pending confirmations",High,"confirmation,safety,sprint4,claude-backend"
Story,[Claude Backend] Execution Audit Logging,"EPIC: Claude Integration & Backend. As a compliance officer, I want execution logs so that all system actions are tracked. Acceptance Criteria: All tool executions logged, User identification in logs, Execution results logging, Log retention policies",High,"audit,execution,sprint4,claude-backend"
Story,[Frontend] React App Initialization,"EPIC: Frontend Development. As a frontend developer, I want a modern React setup so that development is efficient and maintainable. Acceptance Criteria: Create React App with TypeScript template, Folder structure organized by features, Import alias configuration, Development server with hot reload",High,"react,setup,sprint5,frontend"
Story,[Frontend] Styling Framework Setup,"EPIC: Frontend Development. As a UI developer, I want Tailwind CSS so that I can style components efficiently. Acceptance Criteria: Tailwind CSS configured and working, Custom theme configuration, Responsive design utilities, Dark mode support ready",High,"tailwind,styling,sprint5,frontend"
Story,[Frontend] Routing Configuration,"EPIC: Frontend Development. As a user, I want proper navigation so that I can access different parts of the application. Acceptance Criteria: React Router configured, Route protection for authenticated users, Navigation components, Breadcrumb navigation",High,"routing,navigation,sprint5,frontend"
Story,[Frontend] State Management,"EPIC: Frontend Development. As a frontend developer, I want state management so that application state is predictable. Acceptance Criteria: Context API or Redux setup, State persistence for user preferences, Loading and error state management, Optimistic UI updates",High,"state,management,sprint5,frontend"
Story,[Frontend] Chat Container Component,"EPIC: Frontend Development. As a user, I want a well-designed chat interface so that conversations are pleasant. Acceptance Criteria: Responsive chat layout, Dark/light mode toggle, Resizable chat window, Fullscreen mode option",High,"chat,container,sprint5,frontend"
Story,[Frontend] Message List Component,"EPIC: Frontend Development. As a user, I want to see conversation history so that I can track our discussion. Acceptance Criteria: Message bubble components for user/AI, Auto-scroll to latest message, Message timestamps, Loading indicators for pending responses",High,"messages,list,sprint5,frontend"
Story,[Frontend] Input Component,"EPIC: Frontend Development. As a user, I want an intuitive input interface so that I can easily send messages. Acceptance Criteria: Auto-resizing text input, Send button with loading states, Keyboard shortcuts, Character count for long messages",High,"input,interface,sprint5,frontend"
Story,[Frontend] Confirmation Dialog Component,"EPIC: Frontend Development. As a user, I want confirmation dialogs so that I can approve actions before execution. Acceptance Criteria: Modal component for confirmations, Action details display, Confirm/cancel buttons, Keyboard navigation support",High,"confirmation,dialog,sprint5,frontend"
Story,[Frontend] API Service Layer,"EPIC: Frontend Development. As a frontend developer, I want an API service layer so that backend communication is organized. Acceptance Criteria: Axios or fetch API wrapper, Request/response interceptors, Error handling utilities, TypeScript interfaces for API data",High,"api,service,sprint5,frontend"
Story,[Frontend] WebSocket Integration,"EPIC: Frontend Development. As a user, I want real-time updates so that I see responses immediately. Acceptance Criteria: WebSocket connection management, Real-time message updates, Connection status indicators, Automatic reconnection handling",High,"websocket,realtime,sprint5,frontend"
Story,[Frontend] Authentication Integration,"EPIC: Frontend Development. As a user, I want seamless authentication so that I can access the system securely. Acceptance Criteria: JWT token management, Automatic token refresh, Login/logout functionality, Protected route handling",High,"auth,integration,sprint5,frontend"
Story,[Frontend] Error Handling & Retry Logic,"EPIC: Frontend Development. As a user, I want reliable communication so that temporary issues don't break my experience. Acceptance Criteria: Network error handling, Retry logic for failed requests, User-friendly error messages, Offline mode indicators",High,"error,retry,sprint5,frontend"
Story,[Frontend] Conversation Management,"EPIC: Frontend Development. As a user, I want to manage conversations so that I can organize my interactions. Acceptance Criteria: Save conversation history, Export conversations, Clear conversation option, Conversation search functionality",High,"conversation,management,sprint5,frontend"
Story,[Frontend] Quick Actions Menu,"EPIC: Frontend Development. As a user, I want quick actions so that I can perform common tasks efficiently. Acceptance Criteria: Suggested queries menu, Frequently used commands, Template responses, Keyboard shortcuts guide",High,"quickactions,menu,sprint5,frontend"
Story,[Frontend] Search Within Conversation,"EPIC: Frontend Development. As a user, I want to search conversations so that I can find specific information quickly. Acceptance Criteria: Search functionality within conversation, Highlight search results, Search history, Filter by message type",High,"search,conversation,sprint5,frontend"
Story,[Frontend] Accessibility Features,"EPIC: Frontend Development. As a user with accessibility needs, I want proper accessibility so that I can use the application effectively. Acceptance Criteria: ARIA labels and roles, Keyboard navigation support, Screen reader compatibility, High contrast mode",High,"accessibility,a11y,sprint5,frontend"
Story,[Frontend] Performance Optimization,"EPIC: Frontend Development. As a user, I want fast load times so that the application is responsive. Acceptance Criteria: Code splitting for reduced bundle size, Lazy loading for non-critical components, Image optimization, Performance monitoring setup",High,"performance,optimization,sprint5,frontend"
Story,[Frontend] Caching Strategy,"EPIC: Frontend Development. As a user, I want quick access to recent data so that repeated actions are fast. Acceptance Criteria: Browser cache utilization, API response caching, Offline data availability, Cache invalidation strategy",High,"caching,frontend,sprint5,frontend"
Story,[Testing] Backend Unit Tests,"EPIC: Testing & Quality Assurance. As a developer, I want comprehensive backend unit tests so that API reliability is ensured. Acceptance Criteria: 80%+ code coverage for backend, All MCP tools tested, Mock dependencies properly, Edge case testing",High,"testing,backend,sprint6,testing"
Story,[Testing] Frontend Unit Tests,"EPIC: Testing & Quality Assurance. As a frontend developer, I want component unit tests so that UI reliability is ensured. Acceptance Criteria: React component testing with Testing Library, Hook testing for custom hooks, Utility function testing, Snapshot testing for UI consistency",High,"testing,frontend,sprint6,testing"
Story,[Testing] Test Data Management,"EPIC: Testing & Quality Assurance. As a developer, I want test data factories so that tests are maintainable. Acceptance Criteria: Test data factories for all entities, Mock API response generators, Database seeding for tests, Test data cleanup processes",High,"testdata,factories,sprint6,testing"
Story,[Testing] API Integration Tests,"EPIC: Testing & Quality Assurance. As a QA engineer, I want API integration tests so that service interactions work correctly. Acceptance Criteria: End-to-end API workflow testing, Claude API integration testing, MCP server integration testing, Error scenario testing",High,"integration,api,sprint6,testing"
Story,[Testing] Database Integration Tests,"EPIC: Testing & Quality Assurance. As a developer, I want database integration tests so that data operations work correctly. Acceptance Criteria: Database connection testing, Transaction testing, Data consistency testing, Performance testing for queries",High,"integration,database,sprint6,testing"
Story,[Testing] E2E Test Framework,"EPIC: Testing & Quality Assurance. As a QA engineer, I want E2E testing so that user workflows are validated. Acceptance Criteria: Playwright test framework setup, Page object model implementation, Test data management for E2E, CI integration for E2E tests",High,"e2e,framework,sprint6,testing"
Story,[Testing] Critical User Journey Tests,"EPIC: Testing & Quality Assurance. As a user, I want reliable functionality so that core features always work. Acceptance Criteria: Login and authentication flow, Chat conversation flow, Tool execution flow, Confirmation workflow testing",High,"e2e,journeys,sprint6,testing"
Story,[Testing] Cross-Browser Testing,"EPIC: Testing & Quality Assurance. As a user, I want consistent experience so that the app works on my preferred browser. Acceptance Criteria: Chrome Firefox Safari testing, Mobile browser testing, Responsive design validation, Performance testing across browsers",High,"crossbrowser,testing,sprint6,testing"
Story,[Testing] Load Testing,"EPIC: Testing & Quality Assurance. As a system engineer, I want load testing so that the system handles expected traffic. Acceptance Criteria: 100 concurrent user simulation, API response time measurement, Database performance under load, Resource utilization monitoring",High,"load,testing,sprint6,testing"
Story,[Testing] Performance Optimization,"EPIC: Testing & Quality Assurance. As a user, I want fast responses so that my work is efficient. Acceptance Criteria: Database query optimization, API response caching, Frontend bundle optimization, CDN configuration for static assets",High,"performance,optimization,sprint6,testing"
Story,[Testing] Security Audit,"EPIC: Testing & Quality Assurance. As a security engineer, I want security validation so that user data is protected. Acceptance Criteria: Authentication flow security testing, Authorization bypass testing, Input validation testing, SQL injection prevention testing",High,"security,audit,sprint6,testing"
Story,[Testing] API Security Testing,"EPIC: Testing & Quality Assurance. As a security engineer, I want API security so that unauthorized access is prevented. Acceptance Criteria: API rate limiting testing, JWT token security validation, CORS configuration testing, API key management testing",High,"security,api,sprint6,testing"
Story,[Deployment] Production Environment Setup,"EPIC: Deployment & Documentation. As a DevOps engineer, I want production environment so that users can access the application. Acceptance Criteria: Railway production deployment, Environment variables configured, SSL certificates installed, Domain configuration complete",High,"production,setup,sprint7,deployment"
Story,[Deployment] CI/CD Pipeline,"EPIC: Deployment & Documentation. As a developer, I want automated deployment so that releases are reliable. Acceptance Criteria: GitHub Actions workflow, Automated testing in pipeline, Deployment approval process, Rollback capabilities",High,"cicd,automation,sprint7,deployment"
Story,[Deployment] Monitoring Setup,"EPIC: Deployment & Documentation. As a DevOps engineer, I want monitoring so that system health is tracked. Acceptance Criteria: Error tracking with Sentry, Performance monitoring setup, Log aggregation configured, Alert system implemented",High,"monitoring,health,sprint7,deployment"
Story,[Deployment] Technical Documentation,"EPIC: Deployment & Documentation. As a developer, I want technical documentation so that future development is efficient. Acceptance Criteria: API documentation complete, Architecture documentation, Deployment procedures documented, Troubleshooting guide created",High,"technical,docs,sprint7,deployment"
Story,[Deployment] User Documentation,"EPIC: Deployment & Documentation. As a user, I want clear documentation so that I can use the system effectively. Acceptance Criteria: User getting started guide, Common queries cookbook, FAQ document created, Video tutorial scripts",High,"user,docs,sprint7,deployment"
Story,[Deployment] Training Materials,"EPIC: Deployment & Documentation. As a trainer, I want training materials so that users can be onboarded effectively. Acceptance Criteria: Staff training program developed, Practice exercises created, Certification quiz designed, Onboarding checklist created",High,"training,materials,sprint7,deployment"
Story,[Deployment] Pre-Launch Testing,"EPIC: Deployment & Documentation. As a product manager, I want pre-launch validation so that launch is successful. Acceptance Criteria: Production environment testing, User acceptance testing, Performance validation, Security final review",High,"prelaunch,testing,sprint7,deployment"
Story,[Deployment] Launch Communications,"EPIC: Deployment & Documentation. As a product manager, I want launch communications so that users are informed. Acceptance Criteria: Launch announcement prepared, User communication plan, Support channel setup, Feedback collection system",High,"launch,communications,sprint7,deployment"
Story,[Deployment] Support Setup,"EPIC: Deployment & Documentation. As a support manager, I want support systems so that users get help when needed. Acceptance Criteria: Support ticket system, Knowledge base setup, Support team training, Escalation procedures",High,"support,setup,sprint7,deployment"
"""
            
            # Parse CSV data
            import io
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            
            stories_created = 0
            sprints_created = {}
            epics_created = {}
            
            for row in csv_reader:
                # Extract information
                epic_name = extract_epic_info(row['Summary'], row['Description'])
                sprint_num = extract_sprint_info(row['Labels'])
                
                # Create sprint if not exists
                if sprint_num not in sprints_created:
                    sprint_data = sprint_definitions.get(sprint_num, sprint_definitions[1])
                    sprint = get_or_create_sprint(project, sprint_num, sprint_data)
                    sprints_created[sprint_num] = sprint
                    db.session.flush()
                else:
                    sprint = sprints_created[sprint_num]
                
                # Create epic if not exists
                epic_key = f"{sprint_num}-{epic_name}"
                if epic_key not in epics_created:
                    # Map epic name to definitions
                    epic_def_key = epic_name
                    if 'Foundation' in epic_name:
                        epic_def_key = 'Foundation'
                    elif 'MCP Core' in epic_name:
                        epic_def_key = 'MCP Core'
                    elif 'MCP Tools' in epic_name:
                        epic_def_key = 'Core MCP Tools'
                    elif 'Claude' in epic_name:
                        epic_def_key = 'Claude Integration & Backend'
                    elif 'Frontend' in epic_name:
                        epic_def_key = 'Frontend Development'
                    elif 'Testing' in epic_name:
                        epic_def_key = 'Testing & Quality Assurance'
                    elif 'Deployment' in epic_name:
                        epic_def_key = 'Deployment & Documentation'
                    
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
                
                # Create user story
                story_points = calculate_story_points(row['Summary'], row['Description'], row['Priority'])
                
                # Generate story ID
                epic_prefix = epic.epic_id if epic.epic_id else 'GEN'
                story_count = len(epic.user_stories) + 1
                story_id = f"{epic_prefix}-{story_count:03d}"
                
                # Extract title from summary (remove epic prefix)
                title = re.sub(r'^\[[^\]]+\]\s*', '', row['Summary'])
                
                user_story = UserStory(
                    epic=epic,
                    story_id=story_id,
                    title=title,
                    description=row['Description'],
                    story_points=story_points,
                    status='todo',  # Default status
                    created_at=datetime.utcnow()
                )
                
                db.session.add(user_story)
                stories_created += 1
            
            # Update sprint story points
            for sprint in sprints_created.values():
                total_points = 0
                for epic in sprint.epics:
                    for story in epic.user_stories:
                        total_points += story.story_points or 0
                sprint.story_points = total_points
            
            # Commit all changes
            db.session.commit()
            
            print(f"✅ Successfully imported {stories_created} user stories!")
            print(f"✅ Created {len(sprints_created)} sprints")
            print(f"✅ Created {len(epics_created)} epics")
            
            # Print summary
            for sprint in sprints_created.values():
                epic_count = len(sprint.epics)
                story_count = sum(len(epic.user_stories) for epic in sprint.epics)
                print(f"   📋 {sprint.name}: {epic_count} epics, {story_count} stories, {sprint.story_points} points")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error importing user stories: {e}")
            raise

if __name__ == '__main__':
    import_user_stories()