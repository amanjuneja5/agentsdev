from dataclasses import dataclass
import os

@dataclass
class Config:
    model:  str = "claude-haiku-4-5-20251001"
    max_token: int = 1024
    api_key: str = ""

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            model = os.environ.get("AGENT_MODEL"),
            api_key = os.environ.get("ANTHROPIC_API_KEY")
        )
