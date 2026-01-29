"""Agent runner - executes agents using Claude CLI."""
import json
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.agents.registry import get_agent, list_agents
from src.agents.prompts import generate_prompt
from src.messaging.inbox import read_inbox

CONTEXT_DIR = Path(".context")
LOGS_DIR = CONTEXT_DIR / "logs"

# Global state for the loop
_running = False
_loop_thread = None
_current_agent = None  # Currently running agent id
_loop_status = "stopped"  # "stopped" or "running"


def run_agent(agent_id: str, task: Optional[str] = None) -> dict:
    """Run a single iteration for one agent."""
    agent = get_agent(agent_id)
    if not agent:
        return {"error": f"Agent {agent_id} not found"}

    if agent.status != "active":
        return {"error": f"Agent {agent_id} is {agent.status}"}

    # Generate fresh prompt
    prompt = generate_prompt(agent)

    # Check inbox
    inbox_messages = read_inbox(agent_id, clear=True)
    inbox_context = ""
    if inbox_messages:
        inbox_context = "\n\n## Inbox Messages\n"
        for msg in inbox_messages:
            inbox_context += f"\n{msg['content']}\n"

    # Build the full prompt for this iteration
    iteration_prompt = f"""{prompt}

## Current Session
**Time:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{inbox_context}
{f"## Task: {task}" if task else ""}
"""

    # Save iteration prompt for debugging
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"{agent_id}.log"
    with open(log_file, "a") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Iteration at {datetime.now().isoformat()}\n")
        f.write(f"{'='*60}\n")

    # Invoke Claude CLI
    result = _invoke_claude(agent_id, iteration_prompt)

    # Log completion (output already streamed in real-time)
    with open(log_file, "a") as f:
        f.write(f"\n--- Done (code: {result.get('returncode', 'N/A')}) ---\n")
        if result.get("error"):
            f.write(f"ERROR: {result.get('error')}\n")

    return result


def run_cycle(task: Optional[str] = None) -> list[dict]:
    """Run one cycle of all active agents in sequence."""
    results = []
    agents = list_agents(active_only=True)

    for agent in agents:
        result = run_agent(agent.id, task)
        result["agent_id"] = agent.id
        result["agent_name"] = agent.name
        results.append(result)

    return results


def _loop_worker():
    """Background worker that runs continuous cycles."""
    global _running, _current_agent, _loop_status
    _loop_status = "running"
    while _running:
        agents = list_agents(active_only=True)
        for agent in agents:
            if not _running:
                break
            _current_agent = agent.id
            run_agent(agent.id)
        _current_agent = None
    _loop_status = "stopped"


def start_loop():
    """Start the continuous agent loop."""
    global _running, _loop_thread

    if _running:
        return False

    _running = True
    _loop_thread = threading.Thread(target=_loop_worker, daemon=True)
    _loop_thread.start()
    return True


def stop_loop():
    """Stop the continuous agent loop."""
    global _running
    _running = False


def is_running():
    """Check if the loop is running."""
    return _running


def get_loop_status():
    """Get detailed loop status."""
    return {
        "running": _running,
        "status": _loop_status,
        "current_agent": _current_agent,
    }


def _invoke_claude(agent_id: str, prompt: str) -> dict:
    """Invoke Claude CLI with the given prompt, streaming output to log."""
    try:
        prompt_file = CONTEXT_DIR / "agents" / "prompts" / f"{agent_id}_current.md"
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_text(prompt)

        log_file = LOGS_DIR / f"{agent_id}.log"

        # Use Popen to stream output in real-time
        proc = subprocess.Popen(
            [
                "claude", "-p", prompt,
                "--output-format", "stream-json",
                "--verbose",
                "--dangerously-skip-permissions",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(Path.cwd()),
        )

        # Stream output to log file and collect for parsing
        raw_output = []
        with open(log_file, "a") as f:
            for line in proc.stdout:
                raw_output.append(line)
                # Parse and write readable version to log in real-time
                parsed = _parse_single_line(line)
                if parsed:
                    f.write(parsed + "\n")
                    f.flush()

        proc.wait()

        # Parse full output for return value
        output = _parse_stream_json("".join(raw_output))

        return {
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "output": output,
            "error": None if proc.returncode == 0 else "Non-zero exit",
        }

    except subprocess.TimeoutExpired:
        proc.kill()
        return {"success": False, "error": "Timeout"}
    except FileNotFoundError:
        return {"success": False, "error": "Claude CLI not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_single_line(line: str) -> Optional[str]:
    """Parse a single JSON line for real-time logging."""
    line = line.strip()
    if not line:
        return None
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None

    msg_type = obj.get("type")

    if msg_type == "assistant":
        parts = []
        for block in obj.get("message", {}).get("content", []):
            if block.get("type") == "text":
                text = block.get("text", "").strip()
                if text:
                    parts.append(text)
            elif block.get("type") == "tool_use":
                name = block.get("name", "unknown")
                inp = json.dumps(block.get("input", {}))
                if len(inp) > 200:
                    inp = inp[:200] + "..."
                parts.append(f"[tool] {name}: {inp}")
        return "\n".join(parts) if parts else None

    # Skip result messages in real-time log (text already shown above)
    return None


def _parse_stream_json(raw: str) -> str:
    """Parse Claude's stream-json output into readable format."""
    lines = []
    text_buffer = ""
    tool_inputs = {}

    for line in raw.strip().split("\n"):
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_type = obj.get("type")

        if msg_type == "assistant":
            # Assistant message with content blocks
            for block in obj.get("message", {}).get("content", []):
                if block.get("type") == "text":
                    text_buffer += block.get("text", "")
                elif block.get("type") == "tool_use":
                    name = block.get("name", "unknown")
                    inp = json.dumps(block.get("input", {}))
                    if len(inp) > 200:
                        inp = inp[:200] + "..."
                    lines.append(f"[tool] {name}: {inp}")

        elif msg_type == "result":
            # Tool result
            content = obj.get("result", "")
            if isinstance(content, str) and content:
                preview = content[:300] + "..." if len(content) > 300 else content
                preview = preview.replace("\n", " ")
                lines.append(f"[result] {preview}")

    # Add any accumulated text
    if text_buffer:
        lines.append(text_buffer)

    return "\n".join(lines) if lines else "(no output)"
