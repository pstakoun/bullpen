"""Agent configuration dataclass."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentConfig:
    """Configuration for a single agent."""

    id: str
    name: str
    role: str  # Freeform role description
    status: str = "active"  # active, benched

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentConfig":
        return cls(**data)
