"""Agent registry - load, save, and manage agents."""

import json
from pathlib import Path
from typing import Optional

from .config import AgentConfig
from .names import generate_name, generate_id

CONTEXT_DIR = Path(".context")
REGISTRY_FILE = CONTEXT_DIR / "agents" / "registry.json"
INBOX_DIR = CONTEXT_DIR / "inbox"
OUTBOX_DIR = CONTEXT_DIR / "outbox"


def init_context() -> None:
    """Initialize the .context directory structure."""
    CONTEXT_DIR.mkdir(exist_ok=True)
    (CONTEXT_DIR / "agents").mkdir(exist_ok=True)
    (CONTEXT_DIR / "memos").mkdir(exist_ok=True)
    (CONTEXT_DIR / "logs").mkdir(exist_ok=True)
    INBOX_DIR.mkdir(exist_ok=True)
    OUTBOX_DIR.mkdir(exist_ok=True)
    # Create user inbox/outbox
    (INBOX_DIR / "user").mkdir(exist_ok=True)
    (OUTBOX_DIR / "user").mkdir(exist_ok=True)


def _init_agent_dirs(agent_id: str) -> None:
    """Initialize inbox/outbox directories for an agent."""
    (INBOX_DIR / agent_id).mkdir(parents=True, exist_ok=True)
    (OUTBOX_DIR / agent_id).mkdir(parents=True, exist_ok=True)


def init_all_agent_dirs() -> None:
    """Initialize inbox/outbox directories for all existing agents."""
    init_context()
    for agent in list_agents():
        _init_agent_dirs(agent.id)


def _load_registry() -> dict:
    """Load registry from disk."""
    # Ensure directory structure exists
    init_context()

    if REGISTRY_FILE.exists():
        data = json.loads(REGISTRY_FILE.read_text())
        # Ensure team_instructions exists
        if "team_instructions" not in data:
            data["team_instructions"] = ""
        if "agents" not in data:
            data["agents"] = {}
        return data
    return {"team_instructions": "", "agents": {}}


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


def get_agent_by_name(name: str) -> Optional[AgentConfig]:
    """Get agent by name (case-insensitive)."""
    registry = _load_registry()
    name_lower = name.lower()
    for agent_data in registry["agents"].values():
        if agent_data["name"].lower() == name_lower:
            return AgentConfig.from_dict(agent_data)
    return None


def resolve_agent(identifier: str) -> Optional[AgentConfig]:
    """Resolve agent by name (preferred) or ID (fallback)."""
    agent = get_agent_by_name(identifier)
    if agent:
        return agent
    return get_agent(identifier)


def name_exists(name: str, exclude_id: Optional[str] = None) -> bool:
    """Check if a name is already taken (case-insensitive)."""
    registry = _load_registry()
    name_lower = name.lower()
    for agent_id, agent_data in registry["agents"].items():
        if agent_data["name"].lower() == name_lower:
            if exclude_id and agent_id == exclude_id:
                continue
            return True
    return False


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


def create_agent(
    role: str,
    name: Optional[str] = None,
    instructions: str = "",
) -> AgentConfig:
    """
    Create a new agent with auto-generated name and ID.

    Args:
        role: Brief role/title for the agent
        name: Optional name (auto-generated if not provided)
        instructions: Detailed instructions for the agent

    Returns:
        The created AgentConfig
    """
    # Generate or validate name
    if name is None:
        used_names = [a["name"] for a in _load_registry()["agents"].values()]
        name = generate_name(used_names)
    elif name_exists(name):
        raise ValueError(f"Agent name '{name}' already exists")

    # Generate ID from name
    agent_id = generate_id(name)

    # Handle ID collision (different names could slug to same ID)
    registry = _load_registry()
    if agent_id in registry["agents"]:
        counter = 2
        while f"{agent_id}-{counter}" in registry["agents"]:
            counter += 1
        agent_id = f"{agent_id}-{counter}"

    agent = AgentConfig(
        id=agent_id,
        name=name,
        role=role,
        instructions=instructions,
    )
    save_agent(agent)
    _init_agent_dirs(agent_id)
    return agent


def update_agent(
    agent_id: str,
    name: Optional[str] = None,
    role: Optional[str] = None,
    instructions: Optional[str] = None,
) -> Optional[AgentConfig]:
    """
    Update an existing agent's fields.

    Args:
        agent_id: The agent's ID
        name: New name (optional, must be unique)
        role: New role (optional)
        instructions: New instructions (optional)

    Returns:
        The updated AgentConfig, or None if agent not found
    """
    agent = get_agent(agent_id)
    if not agent:
        return None

    if name is not None and name != agent.name:
        if name_exists(name, exclude_id=agent_id):
            raise ValueError(f"Agent name '{name}' already exists")
        agent.name = name

    if role is not None:
        agent.role = role

    if instructions is not None:
        agent.instructions = instructions

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


def get_team_instructions() -> str:
    """Get team-wide instructions."""
    registry = _load_registry()
    return registry.get("team_instructions", "")


def set_team_instructions(instructions: str) -> None:
    """Set team-wide instructions."""
    registry = _load_registry()
    registry["team_instructions"] = instructions
    _save_registry(registry)
