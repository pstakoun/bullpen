"""Dynamic prompt generation for agents."""
from datetime import datetime
from pathlib import Path

from .config import AgentConfig
from .memory import get_memories
from .registry import list_agents, get_team_instructions

CONTEXT_DIR = Path(".context")


def generate_prompt(agent: AgentConfig) -> str:
    """
    Generate a dynamic prompt for an agent at invocation time.

    Minimal structure - let the agent define itself through its work.
    """
    # Get memory context (lessons the agent has accumulated)
    memories = get_memories(agent.id)
    memory_section = _format_memories(memories) if memories else ""

    # Get team context
    team_instructions = get_team_instructions()
    team_instructions_section = _format_team_instructions(team_instructions)
    team_roster_section = _format_team_roster(agent)

    # Agent's own instructions
    agent_instructions_section = ""
    if agent.instructions:
        agent_instructions_section = f"""## Your Instructions

{agent.instructions}
"""

    prompt = f"""# You are {agent.name}

{agent.role}

**Time:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{team_instructions_section}{team_roster_section}{agent_instructions_section}{memory_section}
## Workspace

Your workspace is `.context/` - coordinate with your team there:
- Your inbox: `.context/inbox/{agent.id}/`
- Your outbox: `.context/outbox/{agent.id}/`
- Shared memos: `.context/memos/`
- Message the user: `.context/inbox/user/` (for questions, updates, or results)

## Capabilities

You have full access to all tools: file read/write, web search, bash commands, MCP tools, etc. Use whatever you need to get your work done.
"""

    # Save generated prompt to disk for debugging
    prompt_file = CONTEXT_DIR / "agents" / "prompts" / f"{agent.id}.md"
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text(prompt)

    return prompt


def _format_memories(memories: list[dict]) -> str:
    """Format memories for inclusion in prompt."""
    if not memories:
        return ""

    lines = ["## What you've learned"]
    for m in memories[-5:]:  # Last 5 memories
        lines.append(f"- {m['content']}")

    return "\n".join(lines) + "\n"


def _format_team_instructions(instructions: str) -> str:
    """Format team-wide instructions for inclusion in prompt."""
    if not instructions or not instructions.strip():
        return ""

    return f"""
## Team Instructions

{instructions.strip()}
"""


def _format_team_roster(current_agent: AgentConfig) -> str:
    """Format team roster (other agents) for inclusion in prompt."""
    all_agents = list_agents()
    other_agents = [a for a in all_agents if a.id != current_agent.id]

    if not other_agents:
        return ""

    lines = ["", "## Your Team", ""]
    for agent in other_agents:
        status_note = " (benched)" if agent.status == "benched" else ""
        lines.append(f"- **{agent.name}** - {agent.role}{status_note}")

    return "\n".join(lines) + "\n"
