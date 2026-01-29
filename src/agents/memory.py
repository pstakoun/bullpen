"""Agent memory system - simple append-only log of learnings."""
import json
from datetime import datetime
from pathlib import Path

CONTEXT_DIR = Path(".context")
MEMORY_DIR = CONTEXT_DIR / "agents" / "memory"


def _get_memory_file(agent_id: str) -> Path:
    """Get the memory file path for an agent."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    return MEMORY_DIR / f"{agent_id}.jsonl"


def add_memory(agent_id: str, content: str) -> None:
    """Add a memory for an agent."""
    memory_file = _get_memory_file(agent_id)

    memory = {
        "content": content,
        "timestamp": datetime.now().isoformat(),
    }

    with open(memory_file, "a") as f:
        f.write(json.dumps(memory) + "\n")


def get_memories(agent_id: str, limit: int = 10) -> list[dict]:
    """Get recent memories for an agent."""
    memory_file = _get_memory_file(agent_id)
    if not memory_file.exists():
        return []

    memories = []
    for line in memory_file.read_text().strip().split("\n"):
        if not line:
            continue
        memories.append(json.loads(line))

    # Return most recent
    return memories[-limit:]
