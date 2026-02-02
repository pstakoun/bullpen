"""Bullpen Web UI - FastAPI application."""
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.registry import (
    list_agents, get_agent, create_agent, delete_agent,
    bench_agent, activate_agent, update_agent, name_exists,
    get_team_instructions, set_team_instructions, init_all_agent_dirs
)
from src.agents.names import generate_name
from src.agents.memory import get_memories
from src.messaging.inbox import send_to_agent, broadcast, read_inbox, read_outbox, delete_inbox_message
from src.messaging.memos import list_memos, read_memo
from src.runner import (
    start_loop, stop_loop, get_loop_status, run_agent, run_cycle
)

app = FastAPI(title="Bullpen")


@app.on_event("startup")
async def startup_event():
    """Initialize directory structure on startup."""
    init_all_agent_dirs()


# Setup templates and static files
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

CONTEXT_DIR = Path(".context")
LOGS_DIR = CONTEXT_DIR / "logs"


# ============================================================================
# Dashboard Helpers
# ============================================================================

def get_inbox_count(agent_id: str) -> int:
    """Count unread messages in agent's inbox."""
    inbox = CONTEXT_DIR / "inbox" / agent_id
    return len(list(inbox.glob("*.md"))) if inbox.exists() else 0


def get_last_log_lines(agent_id: str, lines: int = 2) -> list[str]:
    """Get last N meaningful log lines (skip separators and metadata)."""
    log_file = LOGS_DIR / f"{agent_id}.log"
    if not log_file.exists():
        return []
    content = log_file.read_text().strip()
    if not content:
        return []
    meaningful = []
    for l in content.split("\n"):
        l = l.strip()
        if not l:
            continue
        # Skip separator lines
        if l.startswith("===") or l.startswith("---"):
            continue
        # Skip iteration headers
        if l.startswith("Iteration at"):
            continue
        # Clean up bullet points for display
        if l.startswith("- "):
            l = l[2:]
        meaningful.append(l)
    return meaningful[-lines:] if meaningful else []


def get_context_snippet(agent_id: str, max_len: int = 80) -> str:
    """Get meaningful content from agent's context.md file."""
    ctx = CONTEXT_DIR / "agents" / agent_id / "context.md"
    if not ctx.exists():
        return ""
    content = ctx.read_text().strip()
    if not content:
        return ""

    lines = content.split("\n")

    # First pass: look for Task: or Status: lines which are most useful
    for line in lines:
        line = line.strip()
        if line.startswith("- Task:"):
            return line[7:].strip()[:max_len]
        if line.startswith("- Status:"):
            result = line[9:].strip().strip("*")  # Remove markdown bold
            return result[:max_len]

    # Second pass: find first meaningful content line
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip markdown headers
        if line.startswith("#"):
            continue
        # Skip lines that are just labels (end with colon)
        if line.endswith(":"):
            continue
        # Skip horizontal rules
        if line.startswith("---") or line.startswith("***"):
            continue
        # Skip metadata lines
        if line.startswith("- Session:") or line.startswith("Session:"):
            continue
        # Strip leading bullet/dash if present
        if line.startswith("- "):
            line = line[2:]
        return (line[:max_len] + "...") if len(line) > max_len else line

    return ""


def get_enriched_agents() -> list[dict]:
    """Get all agents with dashboard metadata."""
    return [{
        "agent": a,
        "inbox_count": get_inbox_count(a.id),
        "last_logs": get_last_log_lines(a.id, 1),
    } for a in list_agents()]


# ============================================================================
# HTML Pages
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    enriched_agents = get_enriched_agents()
    loop_status = get_loop_status()
    memos = list_memos(limit=5)
    team_instructions = get_team_instructions()
    user_inbox_count = get_inbox_count("user")
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "enriched_agents": enriched_agents,
        "loop_status": loop_status,
        "memos": memos,
        "team_instructions": team_instructions,
        "user_inbox_count": user_inbox_count,
    })


@app.get("/agents/{agent_id}", response_class=HTMLResponse)
async def agent_detail(request: Request, agent_id: str):
    """Agent detail page with logs and messages."""
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    loop_status = get_loop_status()
    memories = get_memories(agent_id, limit=10)
    inbox = read_inbox(agent_id, clear=False)
    outbox = read_outbox(agent_id)

    # Get last 100 lines of logs
    log_content = ""
    log_file = LOGS_DIR / f"{agent_id}.log"
    if log_file.exists():
        lines = log_file.read_text().split("\n")
        log_content = "\n".join(lines[-100:])

    return templates.TemplateResponse("agent_detail.html", {
        "request": request,
        "agent": agent,
        "loop_status": loop_status,
        "memories": memories,
        "inbox": inbox,
        "outbox": outbox,
        "log_content": log_content,
        "user_inbox_count": get_inbox_count("user"),
    })


@app.get("/messages", response_class=HTMLResponse)
async def messages_page(request: Request):
    """Messages page."""
    agents = list_agents()
    loop_status = get_loop_status()
    user_inbox = read_inbox("user", clear=False)
    user_outbox = read_outbox("user")
    return templates.TemplateResponse("messages.html", {
        "request": request,
        "agents": agents,
        "loop_status": loop_status,
        "inbox": user_inbox,
        "outbox": user_outbox,
        "user_inbox_count": len(user_inbox),
    })


@app.get("/memos", response_class=HTMLResponse)
async def memos_page(request: Request):
    """Memos page."""
    loop_status = get_loop_status()
    memos = list_memos(limit=50)
    return templates.TemplateResponse("memos.html", {
        "request": request,
        "loop_status": loop_status,
        "memos": memos,
        "user_inbox_count": get_inbox_count("user"),
    })


# ============================================================================
# API: Agents
# ============================================================================

@app.get("/api/agents")
async def api_list_agents():
    """List all agents."""
    agents = list_agents()
    return [{"id": a.id, "name": a.name, "role": a.role, "instructions": a.instructions, "status": a.status} for a in agents]


@app.get("/api/agents/new-name")
async def api_new_name():
    """Generate a new unique agent name."""
    used_names = [a.name for a in list_agents()]
    name = generate_name(used_names)
    return {"name": name}


@app.post("/api/agents")
async def api_create_agent(
    name: str = Form(...),
    role: str = Form(...),
    instructions: str = Form("")
):
    """Create a new agent with auto-generated ID."""
    if name_exists(name):
        raise HTTPException(status_code=400, detail="Agent name already exists")
    try:
        agent = create_agent(role=role, name=name, instructions=instructions)
        return {"id": agent.id, "name": agent.name, "role": agent.role, "instructions": agent.instructions, "status": agent.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/agents/{agent_id}")
async def api_delete_agent(agent_id: str):
    """Delete an agent."""
    if not get_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    delete_agent(agent_id)
    return {"deleted": agent_id}


@app.put("/api/agents/{agent_id}")
async def api_update_agent(
    agent_id: str,
    name: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    instructions: Optional[str] = Form(None)
):
    """Update an agent's fields."""
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    try:
        updated = update_agent(agent_id, name=name, role=role, instructions=instructions)
        return {"id": updated.id, "name": updated.name, "role": updated.role, "instructions": updated.instructions, "status": updated.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/agents/{agent_id}/bench")
async def api_bench_agent(agent_id: str):
    """Bench an agent."""
    if not get_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    bench_agent(agent_id)
    return {"benched": agent_id}


@app.post("/api/agents/{agent_id}/activate")
async def api_activate_agent(agent_id: str):
    """Activate a benched agent."""
    if not get_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    activate_agent(agent_id)
    return {"activated": agent_id}


# ============================================================================
# API: Loop Control
# ============================================================================

@app.get("/api/loop/status")
async def api_loop_status():
    """Get loop status."""
    status = get_loop_status()
    # Add agent name if running
    if status["current_agent"]:
        agent = get_agent(status["current_agent"])
        status["current_agent_name"] = agent.name if agent else status["current_agent"]
    return status


@app.post("/api/loop/start")
async def api_start_loop():
    """Start the agent loop."""
    if start_loop():
        return {"started": True}
    return {"started": False, "message": "Already running"}


@app.post("/api/loop/stop")
async def api_stop_loop():
    """Stop the agent loop."""
    stop_loop()
    return {"stopped": True}


@app.post("/api/loop/run")
async def api_run_cycle():
    """Run one cycle of all agents."""
    results = run_cycle()
    return {"results": results}


@app.post("/api/loop/run/{agent_id}")
async def api_run_agent(agent_id: str):
    """Run a single agent."""
    if not get_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    result = run_agent(agent_id)
    return result


# ============================================================================
# API: Messages
# ============================================================================

@app.post("/api/messages/send/{agent_id}")
async def api_send_message(agent_id: str, message: str = Form(...)):
    """Send a message to an agent."""
    if not get_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    send_to_agent(agent_id, message, sender="user")
    return {"sent": True, "to": agent_id}


@app.post("/api/messages/broadcast")
async def api_broadcast(message: str = Form(...)):
    """Broadcast a message to all active agents."""
    paths = broadcast(message, sender="user")
    return {"sent": True, "count": len(paths)}


@app.get("/api/messages/inbox/{agent_id}")
async def api_agent_inbox(agent_id: str):
    """Get an agent's inbox."""
    messages = read_inbox(agent_id, clear=False)
    return messages


@app.get("/api/messages/user")
async def api_user_inbox():
    """Get user's inbox (messages from agents)."""
    messages = read_inbox("user", clear=False)
    return messages


@app.post("/api/messages/user/clear")
async def api_clear_user_inbox():
    """Clear user's inbox."""
    messages = read_inbox("user", clear=True)
    return {"cleared": len(messages)}


@app.delete("/api/messages/user/{filename:path}")
async def api_delete_user_message(filename: str):
    """Delete a single message from user's inbox."""
    if delete_inbox_message("user", filename):
        return {"deleted": filename}
    raise HTTPException(status_code=404, detail="Message not found")


# ============================================================================
# API: Memos
# ============================================================================

@app.get("/api/memos")
async def api_list_memos(limit: int = 20):
    """List memos."""
    return list_memos(limit=limit)


@app.get("/api/memos/{filename:path}")
async def api_read_memo(filename: str):
    """Read a specific memo."""
    content = read_memo(filename)
    if content is None:
        raise HTTPException(status_code=404, detail="Memo not found")
    return {"filename": filename, "content": content}


# ============================================================================
# API: Team
# ============================================================================

@app.get("/api/team/instructions")
async def api_get_team_instructions():
    """Get team-wide instructions."""
    instructions = get_team_instructions()
    return {"instructions": instructions}


@app.put("/api/team/instructions")
async def api_set_team_instructions(instructions: str = Form(...)):
    """Set team-wide instructions."""
    set_team_instructions(instructions)
    return {"updated": True, "instructions": instructions}


# ============================================================================
# API: Logs
# ============================================================================

@app.get("/api/logs/{agent_id}")
async def api_get_logs(agent_id: str, lines: int = 100):
    """Get agent logs (last N lines)."""
    log_file = LOGS_DIR / f"{agent_id}.log"
    if not log_file.exists():
        return {"content": "", "lines": 0}

    content = log_file.read_text()
    log_lines = content.split("\n")
    last_lines = log_lines[-lines:]
    return {"content": "\n".join(last_lines), "lines": len(last_lines)}


@app.get("/api/logs/{agent_id}/stream")
async def api_stream_logs(agent_id: str):
    """SSE stream for live logs."""
    log_file = LOGS_DIR / f"{agent_id}.log"

    async def event_generator():
        last_size = 0
        if log_file.exists():
            last_size = log_file.stat().st_size
            # Send last 50 lines initially
            content = log_file.read_text()
            lines = content.split("\n")[-50:]
            initial = "\n".join(lines).replace("\n", "\\n")
            yield f"data: {initial}\n\n"

        while True:
            await asyncio.sleep(0.5)
            if not log_file.exists():
                continue

            current_size = log_file.stat().st_size
            if current_size > last_size:
                with open(log_file, "r") as f:
                    f.seek(last_size)
                    new_content = f.read()
                    if new_content:
                        # Escape for SSE
                        escaped = new_content.replace("\n", "\\n")
                        yield f"data: {escaped}\n\n"
                last_size = current_size

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


# ============================================================================
# Partials (htmx fragments)
# ============================================================================

@app.get("/partials/agent-list", response_class=HTMLResponse)
async def partial_agent_list(request: Request):
    """Partial: agent list for htmx refresh."""
    enriched_agents = get_enriched_agents()
    loop_status = get_loop_status()
    return templates.TemplateResponse("partials/agent_list.html", {
        "request": request,
        "enriched_agents": enriched_agents,
        "loop_status": loop_status,
    })


@app.get("/partials/status", response_class=HTMLResponse)
async def partial_status(request: Request):
    """Partial: loop status badge."""
    loop_status = get_loop_status()
    if loop_status["current_agent"]:
        agent = get_agent(loop_status["current_agent"])
        loop_status["current_agent_name"] = agent.name if agent else loop_status["current_agent"]
    return templates.TemplateResponse("partials/status.html", {
        "request": request,
        "loop_status": loop_status,
    })


@app.get("/partials/nav", response_class=HTMLResponse)
async def partial_nav(request: Request):
    """Partial: nav links with inbox badge."""
    user_inbox_count = get_inbox_count("user")
    return templates.TemplateResponse("partials/nav.html", {
        "request": request,
        "user_inbox_count": user_inbox_count,
    })


@app.get("/partials/logs/{agent_id}", response_class=HTMLResponse)
async def partial_logs(request: Request, agent_id: str, lines: int = 100):
    """Partial: log viewer content."""
    log_file = LOGS_DIR / f"{agent_id}.log"
    log_content = ""
    if log_file.exists():
        content = log_file.read_text()
        log_lines = content.split("\n")
        log_content = "\n".join(log_lines[-lines:])
    return templates.TemplateResponse("partials/log_viewer.html", {
        "request": request,
        "agent_id": agent_id,
        "log_content": log_content,
    })
