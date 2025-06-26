from pydantic import BaseModel, Field, SecretStr
from typing import Literal, List, Dict, Any, Optional, Callable, Union
import yaml

# === Grox ===
class GroxAppConfig(BaseModel):
    service: str = "grox"
    environment: str = "production"
    log_level: str = "INFO"
    log_callback: Optional[Callable[[dict], None]] = None
    tenants: Dict[str, List[str]] = Field(default_factory=dict)

    @classmethod
    def load_yaml(cls, path: str) -> "GroxConfig":
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: str):
        with open(path, "w") as f:
            yaml.safe_dump(self.dict(), f)

# === Metadata ===
class GroxProjectMetadata(BaseModel):
    title: str
    description: Optional[str] = None
    project: str
    workspace: str = "default"

# === Project Config ===
class GroxProjectConfig(BaseModel):
    version: Literal["1.0.0"]
    metadata: GroxProjectMetadata

    @classmethod
    def load_yaml(cls, path: str) -> "GroxProjectConfig":
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)
