"""Dynamic prompt generation for agents."""
from datetime import datetime
from pathlib import Path

from .config import AgentConfig
from .memory import get_memories

CONTEXT_DIR = Path(".context")


def generate_prompt(agent: AgentConfig) -> str:
    """
    Generate a dynamic prompt for an agent at invocation time.

    Minimal structure - let the agent define itself through its work.
    """
    # Get memory context (lessons the agent has accumulated)
    memories = get_memories(agent.id)
    memory_section = _format_memories(memories) if memories else ""

    prompt = f"""# You are {agent.name}

{agent.role}

**Time:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{memory_section}

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

    return "\n".join(lines)
