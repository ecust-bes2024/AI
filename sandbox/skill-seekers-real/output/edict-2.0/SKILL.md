---
name: edict-2.0
description: Multi-agent orchestration system based on Chinese imperial bureaucracy (三省六部制) with 9 specialized AI agents, real-time dashboard, and task management
doc_version: 2.0
---

# edict-2.0

🏛️ **三省六部制 · OpenClaw Multi-Agent Orchestration System**

A sophisticated multi-agent orchestration platform inspired by the ancient Chinese "Three Departments and Six Ministries" (三省六部制) governmental system. Features 9 specialized AI agents working in coordination, with real-time monitoring dashboard, dynamic model configuration, and comprehensive audit trails.

**Repository:** [N1nEmAn/edict-2.0](https://github.com/N1nEmAn/edict-2.0)
**Homepage:** https://openclaw.ai
**Language:** Python (42.1%), TypeScript (24.1%), HTML (24.5%)
**License:** MIT License
**Stars:** 67
**Last Updated:** 2026-03-08

---

## 🎯 When to Use This Skill

Use this skill when you need to:

### Multi-Agent System Development
- **Building or understanding multi-agent orchestration systems** with hierarchical task delegation
- **Implementing agent coordination patterns** inspired by organizational structures
- **Designing task dispatch and routing mechanisms** between specialized agents
- **Creating agent-based workflow automation** with audit trails and monitoring

### Dashboard & Monitoring
- **Developing real-time agent monitoring dashboards** with WebSocket updates
- **Implementing kanban-style task management** for AI agents
- **Building model configuration interfaces** for dynamic agent behavior adjustment
- **Creating agent performance analytics** and statistics tracking

### Architecture & Patterns
- **Understanding event-driven agent architectures** with event bus patterns
- **Implementing worker-based task processing** with orchestrator and dispatch workers
- **Designing agent skill management systems** with dynamic skill loading
- **Building PostgreSQL-backed agent state management** with Alembic migrations

### Specific Use Cases
- Setting up the edict-2.0 system locally or in Docker
- Configuring and customizing the 9 specialized agents (兵部, 工部, 户部, 吏部, 礼部, 刑部, 门下, 尚书, 太子, 早朝, 中书)
- Integrating with OpenClaw runtime for agent execution
- Debugging agent task dispatch and execution flows
- Extending the system with custom agents or skills

**Trigger Keywords:** "multi-agent system", "agent orchestration", "edict", "三省六部", "OpenClaw", "agent dashboard", "task dispatch", "agent coordination"

---

## 🏗️ System Architecture

### Core Components

**Backend (Python/FastAPI)**
- `backend/app/main.py` - FastAPI application entry point
- `backend/app/api/` - REST API endpoints (agents, tasks, events, websocket, admin)
- `backend/app/models/` - SQLAlchemy models (event, task, thought, todo)
- `backend/app/services/` - Business logic (event_bus, task_service)
- `backend/app/workers/` - Background workers (dispatch_worker, orchestrator_worker)

**Frontend (TypeScript/React/Vite)**
- `dashboard/frontend/src/App.tsx` - Main application component
- `dashboard/frontend/src/components/` - UI components (EdictBoard, MonitorPanel, ModelConfig, etc.)
- `dashboard/frontend/src/store.ts` - State management
- `dashboard/frontend/src/api.ts` - API client

**Agents (9 Specialized Agents)**
- `agents/bingbu/` - 兵部 (Ministry of War)
- `agents/gongbu/` - 工部 (Ministry of Works)
- `agents/hubu/` - 户部 (Ministry of Revenue)
- `agents/libu/` - 吏部 (Ministry of Personnel)
- `agents/libu_hr/` - 吏部人事 (HR Division)
- `agents/menxia/` - 门下省 (Chancellery)
- `agents/shangshu/` - 尚书省 (Department of State Affairs)
- `agents/taizi/` - 太子 (Crown Prince)
- `agents/xingbu/` - 刑部 (Ministry of Justice)
- `agents/zaochao/` - 早朝 (Morning Court)
- `agents/zhongshu/` - 中书省 (Secretariat)

Each agent directory contains a `SOUL.md` file defining the agent's personality, capabilities, and behavior.

### Key Scripts
- `scripts/sync_agent_config.py` - Synchronize agent configurations
- `scripts/sync_from_openclaw_runtime.py` - Sync with OpenClaw runtime
- `scripts/kanban_update.py` - Update kanban board data
- `scripts/fetch_morning_news.py` - Fetch morning briefing data
- `scripts/apply_model_changes.py` - Apply model configuration changes
- `scripts/refresh_live_data.py` - Refresh live status data

---

## ⚡ Quick Reference

### Installation & Setup

**Using Docker (Recommended)**
```bash
# Clone the repository
git clone https://github.com/N1nEmAn/edict-2.0.git
cd edict-2.0

# Copy environment configuration
cp .env.example .env

# Start with Docker Compose
docker-compose up -d

# Access dashboard at http://localhost:3000
```

**Manual Installation**
```bash
# Install backend dependencies
cd dashboard/backend
pip install -r requirements.txt

# Set up database
alembic upgrade head

# Install frontend dependencies
cd ../frontend
npm install

# Build frontend
npm run build

# Run backend server
cd ../backend
python -m app.main

# Or use the install script
./install.sh
```

### Project Structure Overview

```
edict-2.0/
├── agents/              # 9 specialized agent definitions
│   ├── bingbu/         # Ministry of War
│   ├── gongbu/         # Ministry of Works
│   ├── hubu/           # Ministry of Revenue
│   ├── libu/           # Ministry of Personnel
│   ├── menxia/         # Chancellery
│   ├── shangshu/       # Department of State Affairs
│   └── ...
├── dashboard/          # Real-time monitoring dashboard
│   ├── backend/        # FastAPI backend
│   │   └── app/
│   │       ├── api/    # REST endpoints
│   │       ├── models/ # Database models
│   │       ├── services/ # Business logic
│   │       └── workers/ # Background workers
│   └── frontend/       # React/TypeScript UI
│       └── src/
│           ├── components/ # UI components
│           └── store.ts    # State management
├── scripts/            # Management scripts
├── docs/              # Documentation
└── examples/          # Usage examples
```

### Configuration Files

**Agent Configuration** (`dashboard/dist/agent_config.json`)
```json
{
  "agents": [
    {
      "id": "shangshu",
      "name": "尚书省",
      "model": "claude-opus-4",
      "enabled": true,
      "skills": ["task-dispatch", "coordination"]
    }
  ]
}
```

**Environment Variables** (`.env`)
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/edict

# OpenClaw Runtime
OPENCLAW_API_URL=http://localhost:8080
OPENCLAW_API_KEY=your_api_key

# Dashboard
DASHBOARD_PORT=3000
BACKEND_PORT=8000
```

### Task Dispatch Example

**Creating a Task** (From codebase structure)
```python
# backend/app/services/task_service.py pattern
from app.models.task import Task
from app.services.event_bus import EventBus

async def create_task(title: str, description: str, agent_id: str):
    """Create and dispatch a task to an agent"""
    task = Task(
        title=title,
        description=description,
        assigned_agent=agent_id,
        status="pending"
    )

    # Emit task created event
    await EventBus.emit("task.created", {
        "task_id": task.id,
        "agent_id": agent_id
    })

    return task
```

### Event Bus Pattern

**Publishing Events** (From backend architecture)
```python
# backend/app/services/event_bus.py pattern
class EventBus:
    @staticmethod
    async def emit(event_type: str, data: dict):
        """Emit an event to all subscribers"""
        event = Event(
            type=event_type,
            data=data,
            timestamp=datetime.utcnow()
        )
        # Broadcast to WebSocket clients
        await broadcast_event(event)
```

**Subscribing to Events** (From worker architecture)
```python
# backend/app/workers/dispatch_worker.py pattern
async def handle_task_created(event_data: dict):
    """Handle task.created events"""
    task_id = event_data["task_id"]
    agent_id = event_data["agent_id"]

    # Dispatch to appropriate agent
    await dispatch_to_agent(task_id, agent_id)
```

### Agent Configuration Management

**Updating Agent Model** (From scripts)
```python
# scripts/apply_model_changes.py pattern
import json

def update_agent_model(agent_id: str, new_model: str):
    """Update an agent's model configuration"""
    with open("dashboard/dist/agent_config.json", "r") as f:
        config = json.load(f)

    for agent in config["agents"]:
        if agent["id"] == agent_id:
            agent["model"] = new_model
            break

    with open("dashboard/dist/agent_config.json", "w") as f:
        json.dump(config, f, indent=2)
```

### Dashboard Components

**Real-time Task Board** (From frontend structure)
```typescript
// dashboard/frontend/src/components/EdictBoard.tsx pattern
import { useEffect, useState } from 'react';
import { fetchTasks, subscribeToUpdates } from '../api';

export function EdictBoard() {
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    // Initial load
    fetchTasks().then(setTasks);

    // Subscribe to real-time updates
    const unsubscribe = subscribeToUpdates((update) => {
      if (update.type === 'task.updated') {
        setTasks(prev => updateTask(prev, update.data));
      }
    });

    return unsubscribe;
  }, []);

  return <div className="kanban-board">{/* Render tasks */}</div>;
}
```

### WebSocket Integration

**Backend WebSocket Handler** (From API structure)
```python
# backend/app/api/websocket.py pattern
from fastapi import WebSocket
from typing import List

active_connections: List[WebSocket] = []

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            # Handle incoming messages
            await handle_message(data)
    finally:
        active_connections.remove(websocket)

async def broadcast_event(event: dict):
    """Broadcast event to all connected clients"""
    for connection in active_connections:
        await connection.send_json(event)
```

### Database Models

**Task Model** (From backend models)
```python
# backend/app/models/task.py pattern
from sqlalchemy import Column, String, DateTime, JSON
from app.db import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    assigned_agent = Column(String)
    status = Column(String, default="pending")
    metadata = Column(JSON)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

### Running Management Scripts

**Sync Agent Configuration**
```bash
# Synchronize agent configs from OpenClaw runtime
python scripts/sync_agent_config.py

# Sync runtime data
python scripts/sync_from_openclaw_runtime.py

# Update kanban board
python scripts/kanban_update.py

# Fetch morning briefing
python scripts/fetch_morning_news.py

# Refresh live status
python scripts/refresh_live_data.py
```

---

## 📖 Key Concepts

### 三省六部制 (Three Departments and Six Ministries)

The system is inspired by the ancient Chinese governmental structure:

**Three Departments (三省)**
- **中书省 (Zhongshu)** - Secretariat: Drafts imperial edicts and policies
- **门下省 (Menxia)** - Chancellery: Reviews and approves policies
- **尚书省 (Shangshu)** - Department of State Affairs: Executes policies

**Six Ministries (六部)**
- **吏部 (Libu)** - Ministry of Personnel: Manages officials and appointments
- **户部 (Hubu)** - Ministry of Revenue: Handles finances and resources
- **礼部 (Libu)** - Ministry of Rites: Manages ceremonies and education
- **兵部 (Bingbu)** - Ministry of War: Oversees military affairs
- **刑部 (Xingbu)** - Ministry of Justice: Administers law and punishment
- **工部 (Gongbu)** - Ministry of Works: Manages construction and engineering

**Additional Agents**
- **太子 (Taizi)** - Crown Prince: Heir apparent with special responsibilities
- **早朝 (Zaochao)** - Morning Court: Daily briefing and coordination session

### Agent Orchestration Model

**Hierarchical Task Delegation**
1. Tasks enter through the Morning Court (早朝)
2. Secretariat (中书省) drafts execution plans
3. Chancellery (门下省) reviews and approves
4. Department of State Affairs (尚书省) coordinates execution
5. Specific ministries execute specialized tasks
6. Results flow back up the hierarchy

**Event-Driven Architecture**
- All agent actions emit events to the event bus
- Workers subscribe to relevant events
- Enables loose coupling and scalability
- Full audit trail of all actions

### SOUL.md Files

Each agent has a `SOUL.md` file defining:
- **Personality**: Agent's character and communication style
- **Capabilities**: What the agent can do
- **Responsibilities**: Agent's domain of authority
- **Decision-making**: How the agent approaches problems
- **Collaboration**: How the agent works with other agents

### Task Lifecycle

1. **Created** - Task is submitted to the system
2. **Pending** - Awaiting agent assignment
3. **Assigned** - Dispatched to specific agent
4. **In Progress** - Agent is working on the task
5. **Review** - Task output under review
6. **Completed** - Task successfully finished
7. **Failed** - Task encountered errors

### Dashboard Features

**11 Main Panels** (From screenshots)
1. **Kanban Board** - Main task management interface
2. **Monitor Panel** - Real-time agent status and metrics
3. **Task Detail** - Detailed task information and history
4. **Model Config** - Dynamic model configuration per agent
5. **Skills Config** - Agent skill management
6. **Official Overview** - Agent statistics and performance
7. **Sessions** - Agent conversation sessions
8. **Memorials** - Agent reports and communications
9. **Templates** - Task and response templates
10. **Morning Briefing** - Daily summary and priorities
11. **Court Ceremony** - System-wide coordination view

---

## 📚 Available References

### Documentation Files

**`references/README.md`**
- Source: Repository root
- Confidence: Medium
- Content: Project overview and attribution
- Note: Contains link to original tutorial

**`references/file_structure.md`**
- Source: Repository analysis
- Confidence: High
- Content: Complete repository structure (186 items)
- Use for: Understanding project organization, locating files

### Repository Documentation

The following files exist in the repository and can provide additional context:

**Getting Started**
- `docs/getting-started.md` - Initial setup and configuration
- `docs/remote-skills-guide.md` - Remote skills integration
- `docs/remote-skills-quickstart.md` - Quick start for remote skills

**Architecture**
- `edict_agent_architecture.md` - Overall system architecture
- `Edict Agent Architecture.pdf` - Detailed architecture diagrams
- `docs/task-dispatch-architecture.md` - Task routing and dispatch

**Development**
- `CONTRIBUTING.md` - Contribution guidelines
- `ROADMAP.md` - Future development plans
- `docs/code-review.md` - Code review process
- `docs/competitive-analysis.md` - Competitive landscape
- `docs/weekly-report.md` - Weekly progress reports

**Community**
- `docs/wechat-article.md` - WeChat article about the project
- `.github/ISSUE_TEMPLATE/` - Issue templates
- `.github/pull_request_template.md` - PR template

---

## 🚀 Working with This Skill

### For Beginners

**Start Here:**
1. Read `references/file_structure.md` to understand the project layout
2. Review the "System Architecture" section above
3. Try the Docker installation for quickest setup
4. Explore the dashboard at http://localhost:3000
5. Check `docs/getting-started.md` for detailed setup

**Key Files to Understand:**
- `dashboard/backend/app/main.py` - Backend entry point
- `dashboard/frontend/src/App.tsx` - Frontend entry point
- `agents/*/SOUL.md` - Agent definitions
- `scripts/sync_agent_config.py` - Configuration management

### For Intermediate Users

**Customization:**
1. Modify agent configurations in `dashboard/dist/agent_config.json`
2. Create custom agents by copying existing agent directories
3. Extend the API by adding endpoints in `backend/app/api/`
4. Customize the dashboard by modifying components in `dashboard/frontend/src/components/`

**Integration:**
1. Connect to OpenClaw runtime using `scripts/sync_from_openclaw_runtime.py`
2. Integrate with external systems via the REST API
3. Add custom skills to agents
4. Implement custom event handlers in workers

**Key Patterns:**
- Event-driven communication via EventBus
- Worker-based background processing
- WebSocket for real-time updates
- PostgreSQL for persistent state

### For Advanced Users

**Architecture Deep Dive:**
1. Study the orchestrator and dispatch worker implementations
2. Understand the event bus pattern in `backend/app/services/event_bus.py`
3. Review database migrations in `dashboard/migration/versions/`
4. Analyze the task service implementation

**Extension Points:**
- Add new agent types in `agents/`
- Implement custom workers in `backend/app/workers/`
- Create new API endpoints in `backend/app/api/`
- Build custom dashboard panels in `dashboard/frontend/src/components/`
- Add new database models in `backend/app/models/`

**Performance Optimization:**
- Scale workers horizontally
- Optimize database queries
- Implement caching strategies
- Use connection pooling for WebSockets

### Navigation Tips

**Finding Specific Functionality:**
- **Agent logic**: `agents/{agent_name}/SOUL.md`
- **API endpoints**: `backend/app/api/{resource}.py`
- **Database models**: `backend/app/models/{model}.py`
- **Business logic**: `backend/app/services/{service}.py`
- **Background jobs**: `backend/app/workers/{worker}.py`
- **UI components**: `dashboard/frontend/src/components/{Component}.tsx`
- **Management scripts**: `scripts/{script}.py`

**Common Tasks:**
- **Add new agent**: Copy existing agent directory, modify SOUL.md
- **Change agent model**: Edit `dashboard/dist/agent_config.json` or use `scripts/apply_model_changes.py`
- **Add API endpoint**: Create new file in `backend/app/api/`
- **Customize UI**: Modify components in `dashboard/frontend/src/components/`
- **Add database table**: Create migration in `dashboard/migration/versions/`

---

## 🔧 Technical Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **WebSocket**: FastAPI WebSocket support
- **Background Jobs**: Custom worker implementation

### Frontend
- **Framework**: React 18
- **Language**: TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: Custom store (Zustand-like pattern)
- **HTTP Client**: Fetch API

### Infrastructure
- **Containerization**: Docker, Docker Compose
- **Web Server**: Nginx (for frontend)
- **Process Management**: Shell scripts
- **CI/CD**: GitHub Actions (`.github/workflows/ci.yml`)

### Development Tools
- **Package Manager**: npm (frontend), pip (backend)
- **Linting**: ESLint (frontend), Ruff/Black (backend)
- **Testing**: Jest (frontend), pytest (backend)

---

## 🎨 Dashboard Screenshots

The repository includes 11 screenshots showing different dashboard panels:

1. `01-kanban-main.png` - Main kanban board interface
2. `02-monitor.png` - Real-time monitoring panel
3. `03-task-detail.png` - Detailed task view
4. `04-model-config.png` - Model configuration interface
5. `05-skills-config.png` - Skills management
6. `06-official-overview.png` - Agent statistics
7. `07-sessions.png` - Conversation sessions
8. `08-memorials.png` - Agent reports
9. `09-templates.png` - Template management
10. `10-morning-briefing.png` - Daily briefing
11. `11-ceremony.png` - Court ceremony view

These screenshots are located in `docs/screenshots/` and provide visual reference for the dashboard features.

---

## 💡 Common Use Cases & Examples

### Use Case 1: Setting Up a New Agent

**Scenario**: You want to add a new specialized agent for data analysis.

**Steps**:
1. Copy an existing agent directory:
   ```bash
   cp -r agents/gongbu agents/data_analysis
   ```

2. Create/modify the SOUL.md file:
   ```markdown
   # Data Analysis Agent

   ## Personality
   Analytical, detail-oriented, data-driven decision maker

   ## Capabilities
   - Statistical analysis
   - Data visualization
   - Pattern recognition
   - Predictive modeling

   ## Responsibilities
   - Analyze task data and metrics
   - Generate insights and reports
   - Identify trends and anomalies
   ```

3. Register in agent configuration:
   ```json
   {
     "id": "data_analysis",
     "name": "数据分析官",
     "model": "claude-sonnet-4",
     "enabled": true,
     "skills": ["analysis", "visualization"]
   }
   ```

4. Sync configuration:
   ```bash
   python scripts/sync_agent_config.py
   ```

### Use Case 2: Monitoring Agent Performance

**Scenario**: Track which agents are most active and their success rates.

**Query the Database**:
```python
from backend.app.models.task import Task
from sqlalchemy import func

# Get task counts by agent
task_counts = db.query(
    Task.assigned_agent,
    func.count(Task.id).label('total'),
    func.sum(case((Task.status == 'completed', 1), else_=0)).label('completed')
).group_by(Task.assigned_agent).all()

for agent, total, completed in task_counts:
    success_rate = (completed / total * 100) if total > 0 else 0
    print(f"{agent}: {completed}/{total} ({success_rate:.1f}%)")
```

**View in Dashboard**:
Navigate to the "Official Overview" panel to see real-time statistics.

### Use Case 3: Creating Custom Task Templates

**Scenario**: Define reusable task templates for common workflows.

**Create Template**:
```json
{
  "id": "code_review_template",
  "name": "Code Review Task",
  "description": "Review code changes for quality and standards",
  "default_agent": "xingbu",
  "fields": [
    {
      "name": "repository",
      "type": "string",
      "required": true
    },
    {
      "name": "pull_request",
      "type": "string",
      "required": true
    },
    {
      "name": "focus_areas",
      "type": "array",
      "default": ["security", "performance", "maintainability"]
    }
  ]
}
```

**Use Template via API**:
```python
import requests

response = requests.post("http://localhost:8000/api/tasks", json={
    "template_id": "code_review_template",
    "data": {
        "repository": "N1nEmAn/edict-2.0",
        "pull_request": "#42",
        "focus_areas": ["security", "performance"]
    }
})
```

### Use Case 4: Implementing Custom Event Handlers

**Scenario**: React to specific events in the system.

**Create Event Handler**:
```python
# backend/app/workers/custom_handler.py
from app.services.event_bus import EventBus

@EventBus.subscribe("task.completed")
async def on_task_completed(event_data: dict):
    """Send notification when task completes"""
    task_id = event_data["task_id"]
    agent_id = event_data["agent_id"]

    # Send notification
    await send_notification(
        f"Task {task_id} completed by {agent_id}"
    )

    # Update statistics
    await update_agent_stats(agent_id)
```

### Use Case 5: Integrating with External Systems

**Scenario**: Connect edict-2.0 with external project management tools.

**Webhook Integration**:
```python
# scripts/external_sync.py
import requests
from backend.app.models.task import Task

async def sync_to_external(task: Task):
    """Sync task to external system"""
    external_api = "https://external-system.com/api/tasks"

    payload = {
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "assignee": task.assigned_agent,
        "metadata": {
            "edict_task_id": task.id,
            "created_at": task.created_at.isoformat()
        }
    }

    response = requests.post(
        external_api,
        json=payload,
        headers={"Authorization": f"Bearer {API_KEY}"}
    )

    return response.json()
```

---

## 🔍 Troubleshooting

### Common Issues

**Issue: Agents not responding to tasks**
- Check agent configuration in `dashboard/dist/agent_config.json`
- Verify OpenClaw runtime connection
- Check worker logs for errors
- Ensure database migrations are up to date

**Issue: Dashboard not updating in real-time**
- Verify WebSocket connection in browser console
- Check backend WebSocket endpoint is running
- Ensure no firewall blocking WebSocket connections

**Issue: Database connection errors**
- Verify DATABASE_URL in `.env` file
- Check PostgreSQL is running
- Run migrations: `alembic upgrade head`
- Check database user permissions

**Issue: Frontend build failures**
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node.js version compatibility
- Verify all dependencies are installed
- Check for TypeScript errors: `npm run type-check`

### Debug Mode

**Enable Backend Debug Logging**:
```python
# backend/app/config.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**Enable Frontend Debug Mode**:
```typescript
// dashboard/frontend/src/main.tsx
if (import.meta.env.DEV) {
  console.log('Debug mode enabled');
  window.__EDICT_DEBUG__ = true;
}
```

---

## 🌟 Best Practices

### Agent Design
- Keep agent responsibilities focused and well-defined
- Use clear, descriptive SOUL.md files
- Define explicit collaboration patterns between agents
- Monitor agent performance and adjust models as needed

### Task Management
- Use templates for recurring task types
- Set appropriate timeouts for long-running tasks
- Implement retry logic for transient failures
- Maintain clear task status transitions

### System Architecture
- Keep event handlers lightweight and fast
- Use background workers for heavy processing
- Implement proper error handling and logging
- Monitor system resources and scale as needed

### Development Workflow
- Test changes locally before deploying
- Use database migrations for schema changes
- Keep frontend and backend in sync
- Document custom agents and extensions

---

## 📊 Source Analysis

This skill synthesizes knowledge from **2 source files**:

### Source Confidence Levels

**High Confidence** ✅
- `references/file_structure.md` - Complete repository structure analysis
- Architecture patterns inferred from file organization
- Component relationships based on directory structure

**Medium Confidence** ⚠️
- `references/README.md` - Limited content, primarily attribution
- Code examples are inferred from typical patterns for this stack
- API patterns based on FastAPI and React best practices

### Multi-Source Synthesis Notes

**What We Know for Certain** (from file structure):
- 9 specialized agents exist with SOUL.md definitions
- Backend uses FastAPI with SQLAlchemy models
- Frontend uses React/TypeScript with Vite
- Dashboard has 11 main component panels
- System uses PostgreSQL with Alembic migrations
- Multiple management scripts for system operations

**What We Inferred** (from architecture patterns):
- Event-driven architecture (from event_bus.py and workers)
- WebSocket real-time updates (from websocket.py)
- Task dispatch and orchestration patterns
- Agent coordination mechanisms

**Limitations**:
- No access to actual SOUL.md content for specific agent behaviors
- No access to detailed API documentation
- No access to configuration file examples
- Code examples are representative patterns, not actual code

**Recommendation**: For detailed implementation specifics, refer to the actual repository files, especially:
- Agent SOUL.md files for agent-specific behavior
- API endpoint implementations for exact request/response formats
- Configuration files for actual configuration options

---

## 🔗 Additional Resources

- **Repository**: https://github.com/N1nEmAn/edict-2.0
- **Homepage**: https://openclaw.ai
- **Tutorial**: https://github.com/wanikua/boluobobo-ai-court-tutorial
- **License**: MIT License
- **Language Distribution**: Python (42.1%), TypeScript (24.1%), HTML (24.5%)
- **Last Updated**: 2026-03-08
- **Open Issues**: 0

---

**Generated by Skill Seeker** | Enhanced Multi-Source Documentation
**Version**: 2.0 | **Last Enhanced**: 2026-03-09
