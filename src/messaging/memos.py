"""Memo system for shared team communication."""
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

CONTEXT_DIR = Path(".context")
MEMOS_DIR = CONTEXT_DIR / "memos"
DISCUSSIONS_DIR = CONTEXT_DIR / "discussions"


def write_memo(
    author: str,
    title: str,
    content: str,
    tags: Optional[list[str]] = None,
) -> Path:
    """Write a memo to the shared memos directory."""
    MEMOS_DIR.mkdir(parents=True, exist_ok=True)

    # Create filename: YYYY-MM-DD-author-title-slug.md
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:30]
    filename = f"{date_str}-{author}-{slug}.md"

    memo_file = MEMOS_DIR / filename

    # Format memo
    tags_str = " ".join(f"#{t}" for t in tags) if tags else ""
    memo_content = f"""# {title}
**Author:** {author}
**Time:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{f"**Tags:** {tags_str}" if tags_str else ""}

---

{content}
"""

    memo_file.write_text(memo_content)
    return memo_file


def list_memos(
    author: Optional[str] = None,
    limit: int = 10,
) -> list[dict]:
    """List recent memos, optionally filtered by author."""
    if not MEMOS_DIR.exists():
        return []

    memos = []
    for memo_file in sorted(MEMOS_DIR.glob("*.md"), reverse=True):
        # Parse filename for metadata
        parts = memo_file.stem.split("-", 4)  # date(3) + author + title
        if len(parts) >= 5:
            file_author = parts[3]
            if author and file_author != author:
                continue

        memos.append({
            "file": memo_file.name,
            "path": str(memo_file),
            "author": parts[3] if len(parts) >= 5 else "unknown",
        })

        if len(memos) >= limit:
            break

    return memos


def read_memo(filename: str) -> Optional[str]:
    """Read a specific memo by filename."""
    memo_file = MEMOS_DIR / filename
    if memo_file.exists():
        return memo_file.read_text()
    return None


def start_discussion(
    title: str,
    initiator: str,
    initial_message: str,
) -> Path:
    """Start a new discussion thread."""
    DISCUSSIONS_DIR.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:30]
    filename = f"{date_str}-{slug}.md"

    discussion_file = DISCUSSIONS_DIR / filename

    content = f"""# {title}
**Started:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## {initiator} ({datetime.now().strftime("%H:%M")})

{initial_message}
"""

    discussion_file.write_text(content)
    return discussion_file


def add_to_discussion(discussion_file: str, author: str, message: str) -> None:
    """Add a message to an existing discussion."""
    path = DISCUSSIONS_DIR / discussion_file
    if not path.exists():
        return

    addition = f"""
---

## {author} ({datetime.now().strftime("%H:%M")})

{message}
"""

    with open(path, "a") as f:
        f.write(addition)
