# Bullpen

A minimal multi-agent system with file-based communication.

## Prerequisites

- Python 3
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated

## Quick Start

```bash
python3 main.py
```

This starts a REPL where you can create agents, send messages, and run the bullpen.

## Example Session

```
■ > add researcher Remy "You find and gather information."
Created: Remy (researcher)

■ > add writer Sam "You synthesize information into clear writing."
Created: Sam (writer)

■ > status

Loop: STOPPED
Agents: 2

  ✓ Remy (researcher)
    You find and gather information.
  ✓ Sam (writer)
    You synthesize information into clear writing.

■ > broadcast What are the key principles of good API design?
Sent to 2 agents

■ > start
Started loop

▶ > memos

  2026-01-28-researcher-api-design-principles.md
  2026-01-28-writer-api-design-summary.md

▶ > stop
Stopped

■ > quit
```

## Commands

```
add <id> <name> <role>  - Add an agent
rm <id>                 - Remove an agent
status                  - Show agents and loop status
send <id> <msg>         - Send message to one agent
broadcast <msg>         - Send to all agents
start                   - Start continuous loop
stop                    - Stop the loop
run [id]                - Run one cycle (or one agent)
memos                   - List recent memos
read <file>             - Read a memo
logs <id> [lines]       - View agent output
help                    - Show help
quit                    - Exit
```

## CLI Mode

Any command can be run directly from bash for scripting:

```bash
python3 main.py add researcher Remy "You find information."
python3 main.py broadcast "What is the weather?"
python3 main.py start
python3 main.py status
python3 main.py logs researcher
```

## How It Works

```
.context/
├── agents/
│   ├── registry.json     # Agent configs
│   └── memory/           # Per-agent memories
├── inbox/{agent}/        # Messages TO agents
├── outbox/{agent}/       # Messages FROM agents
└── memos/                # Shared workspace
```

1. Create agents with `add`
2. Send them messages with `send` or `broadcast`
3. Start the loop with `start` - agents run continuously
4. Agents read their inbox, read teammates' memos, and write their own
5. Check output with `memos` and `read`
