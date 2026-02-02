"""Agent personal context management - agent-owned scratchpad and journal."""
from pathlib import Path

CONTEXT_DIR = Path(".context")
AGENTS_DIR = CONTEXT_DIR / "agents"


def get_agent_context_dir(agent_id: str) -> Path:
    """Get the personal context directory for an agent."""
    return AGENTS_DIR / agent_id


def init_agent_context_dir(agent_id: str) -> Path:
    """Initialize an agent's personal context directory with starter files."""
    context_dir = get_agent_context_dir(agent_id)
    context_dir.mkdir(parents=True, exist_ok=True)

    # Create starter files if they don't exist
    context_file = context_dir / "context.md"
    if not context_file.exists():
        context_file.write_text("")

    journal_file = context_dir / "journal.md"
    if not journal_file.exists():
        journal_file.write_text("")

    return context_dir


def read_agent_context(agent_id: str) -> str:
    """Read an agent's personal context files for inclusion in prompt."""
    context_dir = get_agent_context_dir(agent_id)
    sections = []

    # Current state/scratchpad
    context_file = context_dir / "context.md"
    if context_file.exists():
        content = context_file.read_text().strip()
        if content:
            sections.append(f"## Your Context\n\n{content}")

    # Recent journal (last ~50 lines to avoid bloat)
    journal_file = context_dir / "journal.md"
    if journal_file.exists():
        content = journal_file.read_text().strip()
        if content:
            lines = content.split("\n")
            recent = "\n".join(lines[-50:]) if len(lines) > 50 else content
            sections.append(f"## Your Journal (Recent)\n\n{recent}")

    return "\n\n".join(sections)


def rotate_journal(agent_id: str, keep_lines: int = 100) -> bool:
    """
    Archive old journal entries, keep recent ones.

    Returns True if rotation happened, False otherwise.
    """
    context_dir = get_agent_context_dir(agent_id)
    journal = context_dir / "journal.md"
    archive = context_dir / "journal_archive.md"

    if not journal.exists():
        return False

    content = journal.read_text()
    if not content.strip():
        return False

    lines = content.split("\n")
    if len(lines) <= keep_lines:
        return False

    # Archive old, keep recent
    old = lines[:-keep_lines]
    recent = lines[-keep_lines:]

    with open(archive, "a") as f:
        f.write("\n".join(old) + "\n")

    journal.write_text("\n".join(recent))
    return True


def rotate_conversations(agent_id: str, keep_lines: int = 200) -> bool:
    """
    Archive old conversation entries, keep recent ones.

    Returns True if rotation happened, False otherwise.
    """
    context_dir = get_agent_context_dir(agent_id)
    conversations = context_dir / "conversations.md"
    archive = context_dir / "conversations_archive.md"

    if not conversations.exists():
        return False

    content = conversations.read_text()
    if not content.strip():
        return False

    lines = content.split("\n")
    if len(lines) <= keep_lines:
        return False

    # Archive old, keep recent
    old = lines[:-keep_lines]
    recent = lines[-keep_lines:]

    with open(archive, "a") as f:
        f.write("\n".join(old) + "\n")

    conversations.write_text("\n".join(recent))
    return True
