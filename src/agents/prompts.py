"""Dynamic prompt generation for agents."""
from datetime import datetime
from pathlib import Path

from .config import AgentConfig
from .context import read_agent_context
from .registry import list_agents, get_team_instructions

CONTEXT_DIR = Path(".context")


def generate_prompt(agent: AgentConfig) -> str:
    """
    Generate a dynamic prompt for an agent at invocation time.

    Minimal structure - let the agent define itself through its work.
    """
    # Get agent's personal context (scratchpad and journal)
    agent_context = read_agent_context(agent.id)
    agent_context_section = f"\n{agent_context}\n" if agent_context else ""

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
{team_instructions_section}{team_roster_section}{agent_instructions_section}{agent_context_section}
## Maintaining Your Context

You have a personal directory at `.context/agents/{agent.id}/` for maintaining continuity across sessions.

**context.md** - Your scratchpad. Keep it updated with:
- What you're currently working on
- Where you left off
- Next steps and priorities
- Open questions or blockers

**journal.md** - Your running log. Append entries for:
- Session summaries (what you did, what you learned)
- Important decisions and reasoning
- Things to remember long-term

Before ending your session, update these files. Your future self will read them at the start of your next run.

## Communication

**Do not output questions or messages directly.** Use the messaging system:

- **To message the user:** Write a markdown file to `.context/inbox/user/`
- **To message a teammate:** Write a markdown file to `.context/inbox/{{their_id}}/`

Your direct output is for working and thinking. All communication with the user or teammates must go through the inbox system - that's how they'll see it.

When you have a question, need input, or want to share results: write it to the appropriate inbox.

## Workspace

Your workspace is `.context/` - coordinate with your team there:
- Your personal context: `.context/agents/{agent.id}/`
- Your inbox: `.context/inbox/{agent.id}/`
- Your outbox: `.context/outbox/{agent.id}/`
- Shared memos: `.context/memos/`

## Capabilities

You have full access to all tools: file read/write, web search, bash commands, MCP tools, etc. Use whatever you need to get your work done.
"""

    # Save generated prompt to disk for debugging
    prompt_file = CONTEXT_DIR / "agents" / "prompts" / f"{agent.id}.md"
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text(prompt)

    return prompt


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
