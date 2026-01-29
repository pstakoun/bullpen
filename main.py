#!/usr/bin/env python3
"""
Multi-Agent Swarm

Usage:
    python main.py              - Start the REPL
    python main.py add <id> <name> <role>  - Add an agent
    python main.py rm <id>      - Remove an agent
"""
import sys
import readline
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.agents.registry import list_agents, get_agent, create_agent, delete_agent
from src.messaging.inbox import send_to_agent, broadcast, read_inbox, read_outbox
from src.messaging.memos import list_memos, read_memo
from src.runner import start_loop, stop_loop, is_running, run_agent, get_loop_status


def cmd_add(args):
    if len(args) < 3:
        print("Usage: add <id> <name> <role>")
        return
    agent = create_agent(args[0], args[1], " ".join(args[2:]))
    print(f"Created: {agent.name} ({agent.id})")


def cmd_rm(args):
    if not args:
        print("Usage: rm <id>")
        return
    if delete_agent(args[0]):
        print(f"Removed: {args[0]}")
    else:
        print(f"Not found: {args[0]}")


def cmd_status():
    agents = list_agents()
    loop = get_loop_status()

    if loop["running"]:
        if loop["current_agent"]:
            current = get_agent(loop["current_agent"])
            name = current.name if current else loop["current_agent"]
            print(f"\nLoop: RUNNING → {name}")
        else:
            print(f"\nLoop: RUNNING")
    else:
        print(f"\nLoop: STOPPED")

    if not agents:
        print("No agents.\n")
        return
    print(f"Agents: {len(agents)}\n")
    for agent in agents:
        is_current = loop["current_agent"] == agent.id
        if is_current:
            icon = "▶"
        elif agent.status == "active":
            icon = "✓"
        else:
            icon = "○"
        print(f"  {icon} {agent.name} ({agent.id})")
        print(f"    {agent.role}")
    print()


def cmd_send(args):
    if len(args) < 2:
        print("Usage: send <id> <message>")
        return
    agent = get_agent(args[0])
    if not agent:
        print(f"Not found: {args[0]}")
        return
    send_to_agent(args[0], " ".join(args[1:]), sender="user")
    print(f"Sent to {agent.name}")


def cmd_broadcast(args):
    if not args:
        print("Usage: broadcast <message>")
        return
    paths = broadcast(" ".join(args), sender="user")
    print(f"Sent to {len(paths)} agents")


def cmd_memos():
    memos = list_memos(limit=10)
    if not memos:
        print("No memos.")
        return
    print()
    for m in memos:
        print(f"  {m['file']}")
    print()


def cmd_read(args):
    if not args:
        print("Usage: read <filename>")
        return
    content = read_memo(args[0])
    if content:
        print(content)
    else:
        print(f"Not found: {args[0]}")


def cmd_inbox(args):
    if not args:
        print("Usage: inbox <id>")
        return
    agent = get_agent(args[0])
    if not agent:
        print(f"Not found: {args[0]}")
        return
    messages = read_inbox(args[0], clear=False)
    if not messages:
        print(f"\n{agent.name}'s inbox is empty.\n")
        return
    print(f"\n--- {agent.name}'s inbox ({len(messages)} messages) ---\n")
    for m in messages:
        print(f"=== {m['file']} ===")
        print(m['content'])
        print()


def cmd_outbox(args):
    if not args:
        print("Usage: outbox <id>")
        return
    agent = get_agent(args[0])
    if not agent:
        print(f"Not found: {args[0]}")
        return
    messages = read_outbox(args[0])
    if not messages:
        print(f"\n{agent.name}'s outbox is empty.\n")
        return
    print(f"\n--- {agent.name}'s outbox ({len(messages)} messages) ---\n")
    for m in messages:
        print(f"=== {m['file']} ===")
        print(m['content'])
        print()


def cmd_messages(args):
    """View the user's inbox (messages from agents)."""
    messages = read_inbox("user", clear=False)
    if not messages:
        print("\nNo messages from agents.\n")
        return
    print(f"\n--- Messages from agents ({len(messages)}) ---\n")
    for m in messages:
        print(f"=== {m['file']} ===")
        print(m['content'])
        print()


def cmd_clear(args):
    """Clear the user's inbox."""
    messages = read_inbox("user", clear=True)
    count = len(messages)
    print(f"Cleared {count} message(s).")


def cmd_sent(args):
    """View the user's sent messages (outbox)."""
    messages = read_outbox("user")
    if not messages:
        print("\nNo sent messages.\n")
        return
    print(f"\n--- Sent messages ({len(messages)}) ---\n")
    for m in messages:
        print(f"=== {m['file']} ===")
        print(m['content'])
        print()


def cmd_logs(args):
    if not args:
        print("Usage: logs <id> [lines]")
        return
    agent_id = args[0]
    agent = get_agent(agent_id)
    if not agent:
        print(f"Not found: {agent_id}")
        return

    lines = int(args[1]) if len(args) > 1 else 50
    log_file = Path(".context/logs") / f"{agent_id}.log"

    if not log_file.exists():
        print(f"No logs for {agent.name}")
        return

    content = log_file.read_text()
    log_lines = content.split("\n")

    # Show last N lines
    output = "\n".join(log_lines[-lines:])
    print(f"\n--- {agent.name} logs (last {lines} lines) ---\n")
    print(output)
    print()


def cmd_start(args):
    if start_loop():
        print("Started loop")
    else:
        print("Already running")


def cmd_stop():
    stop_loop()
    print("Stopped")


def cmd_run(args):
    if args:
        # Run specific agent
        agent = get_agent(args[0])
        if not agent:
            print(f"Not found: {args[0]}")
            return
        print(f"Running {agent.name}...")
        result = run_agent(args[0])
        if result.get("error"):
            print(f"Error: {result['error']}")
        else:
            print("Done")
    else:
        # Run all once
        from src.runner import run_cycle
        agents = list_agents(active_only=True)
        if not agents:
            print("No agents")
            return
        print(f"Running {len(agents)} agents...")
        run_cycle()
        print("Done")


def cmd_help():
    print("""
Commands:
  status                  - Show agents and loop status
  start                   - Start continuous loop
  stop                    - Stop the loop
  run [id]                - Run one cycle (or one agent)

  send <id> <msg>         - Send message to agent
  broadcast <msg>         - Send to all agents
  messages                - View messages from agents (your inbox)
  sent                    - View your sent messages (your outbox)
  clear                   - Clear your inbox

  inbox <id>              - View agent's inbox
  outbox <id>             - View agent's outbox
  logs <id> [lines]       - View agent logs
  memos                   - List shared memos
  read <file>             - Read a memo

  add <id> <name> <role>  - Add an agent
  rm <id>                 - Remove an agent
  help                    - Show this help
  quit                    - Exit
""")


def repl():
    print("Multi-Agent Swarm")
    print("Type 'help' for commands.\n")

    while True:
        try:
            status = "▶" if is_running() else "■"
            line = input(f"{status} > ").strip()
            if not line:
                continue

            parts = line.split()
            cmd = parts[0].lower()
            args = parts[1:]

            if cmd in ("quit", "exit", "q"):
                stop_loop()
                break
            elif cmd == "add":
                cmd_add(args)
            elif cmd == "rm":
                cmd_rm(args)
            elif cmd == "status":
                cmd_status()
            elif cmd == "send":
                cmd_send(args)
            elif cmd == "broadcast":
                cmd_broadcast(args)
            elif cmd == "start":
                cmd_start(args)
            elif cmd == "stop":
                cmd_stop()
            elif cmd == "run":
                cmd_run(args)
            elif cmd == "memos":
                cmd_memos()
            elif cmd == "read":
                cmd_read(args)
            elif cmd == "logs":
                cmd_logs(args)
            elif cmd == "inbox":
                cmd_inbox(args)
            elif cmd == "outbox":
                cmd_outbox(args)
            elif cmd == "messages":
                cmd_messages(args)
            elif cmd == "clear":
                cmd_clear(args)
            elif cmd == "sent":
                cmd_sent(args)
            elif cmd == "help":
                cmd_help()
            else:
                print(f"Unknown: {cmd}")

        except KeyboardInterrupt:
            print("\nUse 'quit' to exit")
        except EOFError:
            break


def main():
    if len(sys.argv) < 2:
        repl()
        return

    cmd = sys.argv[1]

    if cmd == "add":
        if len(sys.argv) < 5:
            print("Usage: python main.py add <id> <name> <role>")
            return
        cmd_add(sys.argv[2:])
    elif cmd == "rm":
        if len(sys.argv) < 3:
            print("Usage: python main.py rm <id>")
            return
        cmd_rm(sys.argv[2:])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
