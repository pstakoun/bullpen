"""Inbox/outbox messaging system for agent communication."""
from datetime import datetime
from pathlib import Path

CONTEXT_DIR = Path(".context")
INBOX_DIR = CONTEXT_DIR / "inbox"
OUTBOX_DIR = CONTEXT_DIR / "outbox"


def send_to_agent(agent_id: str, message: str, sender: str = "user") -> Path:
    """Send a message to an agent's inbox (and copy to sender's outbox)."""
    inbox = INBOX_DIR / agent_id
    inbox.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    msg_file = inbox / f"{timestamp}_{sender}.md"

    content = f"""# Message from {sender}
**Time:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{message}
"""
    msg_file.write_text(content)

    # Also save to sender's outbox for tracking
    outbox = OUTBOX_DIR / sender
    outbox.mkdir(parents=True, exist_ok=True)
    outbox_content = f"""# Message to {agent_id}
**Time:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{message}
"""
    outbox_file = outbox / f"{timestamp}_to_{agent_id}.md"
    outbox_file.write_text(outbox_content)

    return msg_file


def broadcast(message: str, sender: str = "user") -> list[Path]:
    """Send a message to all agents."""
    from src.agents.registry import list_agents

    files = []
    for agent in list_agents(active_only=True):
        files.append(send_to_agent(agent.id, message, sender))
    return files


def read_inbox(agent_id: str, clear: bool = False) -> list[dict]:
    """Read all messages in an agent's inbox."""
    inbox = INBOX_DIR / agent_id
    if not inbox.exists():
        return []

    messages = []
    for msg_file in sorted(inbox.glob("*.md")):
        messages.append({
            "file": msg_file.name,
            "content": msg_file.read_text(),
        })
        if clear:
            msg_file.unlink()

    return messages


def archive_inbox(agent_id: str) -> int:
    """
    Archive inbox messages to agent's conversation history before clearing.

    Returns the number of messages archived.
    """
    inbox = INBOX_DIR / agent_id
    if not inbox.exists():
        return 0

    # Archive to agent's personal context directory
    conversations_file = CONTEXT_DIR / "agents" / agent_id / "conversations.md"
    conversations_file.parent.mkdir(parents=True, exist_ok=True)

    archived = 0
    for msg_file in sorted(inbox.glob("*.md")):
        content = msg_file.read_text()
        # Append to conversations file
        with open(conversations_file, "a") as f:
            f.write(f"\n---\n\n{content}\n")
        archived += 1

    return archived


def write_to_outbox(agent_id: str, content: str, title: str = "response") -> Path:
    """Write a response to an agent's outbox."""
    outbox = OUTBOX_DIR / agent_id
    outbox.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = outbox / f"{timestamp}_{title}.md"
    out_file.write_text(content)
    return out_file


def read_outbox(agent_id: str) -> list[dict]:
    """Read all messages in an agent's outbox."""
    outbox = OUTBOX_DIR / agent_id
    if not outbox.exists():
        return []

    messages = []
    for msg_file in sorted(outbox.glob("*.md")):
        messages.append({
            "file": msg_file.name,
            "content": msg_file.read_text(),
        })
    return messages


def delete_inbox_message(agent_id: str, filename: str) -> bool:
    """Delete a single message from an agent's inbox."""
    inbox = INBOX_DIR / agent_id
    msg_file = inbox / filename
    if msg_file.exists() and msg_file.is_file():
        msg_file.unlink()
        return True
    return False
