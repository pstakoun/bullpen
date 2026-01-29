"""Agent registry - load, save, and manage agents."""
import json
from pathlib import Path
from typing import Optional

from .config import AgentConfig

CONTEXT_DIR = Path(".context")
REGISTRY_FILE = CONTEXT_DIR / "agents" / "registry.json"


def _load_registry() -> dict:
    """Load registry from disk."""
    if REGISTRY_FILE.exists():
        return json.loads(REGISTRY_FILE.read_text())
    return {"agents": {}}


def _save_registry(registry: dict) -> None:
    """Save registry to disk."""
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2))


def get_agent(agent_id: str) -> Optional[AgentConfig]:
    """Get agent by ID."""
    registry = _load_registry()
    if agent_id in registry["agents"]:
        return AgentConfig.from_dict(registry["agents"][agent_id])
    return None


def list_agents(active_only: bool = False) -> list[AgentConfig]:
    """List all agents."""
    registry = _load_registry()
    agents = [AgentConfig.from_dict(a) for a in registry["agents"].values()]
    if active_only:
        agents = [a for a in agents if a.status == "active"]
    return agents


def save_agent(agent: AgentConfig) -> None:
    """Save or update an agent."""
    registry = _load_registry()
    registry["agents"][agent.id] = agent.to_dict()
    _save_registry(registry)


def bench_agent(agent_id: str) -> None:
    """Bench an agent (temporarily remove from active duty)."""
    agent = get_agent(agent_id)
    if agent:
        agent.status = "benched"
        save_agent(agent)


def activate_agent(agent_id: str) -> None:
    """Activate a benched agent."""
    agent = get_agent(agent_id)
    if agent:
        agent.status = "active"
        save_agent(agent)


def create_agent(agent_id: str, name: str, role: str) -> AgentConfig:
    """Create a new agent."""
    agent = AgentConfig(id=agent_id, name=name, role=role)
    save_agent(agent)
    return agent


def delete_agent(agent_id: str) -> bool:
    """Delete an agent."""
    registry = _load_registry()
    if agent_id in registry["agents"]:
        del registry["agents"][agent_id]
        _save_registry(registry)
        return True
    return False
