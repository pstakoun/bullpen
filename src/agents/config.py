"""Agent configuration dataclass."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentConfig:
    """Configuration for a single agent."""

    id: str
    name: str
    role: str  # Brief role/title
    instructions: str = ""  # Detailed agent instructions
    status: str = "active"  # active, benched

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "instructions": self.instructions,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentConfig":
        # Handle existing agents without instructions field
        if "instructions" not in data:
            data = {**data, "instructions": ""}
        return cls(**data)
