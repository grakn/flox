from pydantic import BaseModel, Field, SecretStr
from typing import Literal, List, Dict, Any, Optional, Callable, Union
from pathlib import Path
import yaml
from seyaml import load_seyaml
from langfabric import load_model_configs
from .documents.schema import Document

# === Grox ===
class GroxAppConfig(BaseModel):
    service: str = "grox"
    version: Optional[str] = None
    environment: Optional[str] = None
    log_level: str = "INFO"
    log_format: str = "console"
    log_callback: Optional[Callable[[dict], None]] = None
    tenants: Dict[str, List[str]] = Field(default_factory=dict)

    @classmethod
    def load_yaml(cls, path: str) -> "GroxAppConfig":
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return GroxAppConfig.model_validate(data)

    def to_yaml(self, path: str):
        with open(path, "w") as f:
            yaml.safe_dump(self.dict(), f)

# === Metadata ===
class ProjectMetadata(BaseModel):
    title: str
    description: Optional[str] = None
    project: str
    workspace: str = "default"

# === Orchestration ===
class OrchestrationConfig(BaseModel):
    documents: Optional[List[str]] = Field(default_factory=list)
    document_configs: Optional[list] = None

# === Infrastructure ===
class DefaultsConfig(BaseModel):
    chat_model: Optional[str] = None
    chat_model_with_tools: Optional[str] = None
    embedding_model: Optional[str] = None

class InfrastructureConfig(BaseModel):
    models: Optional[List[str]] = Field(default_factory=list)
    model_configs: Optional[dict] = None
    defaults: Optional[DefaultsConfig] = None
    backends: Optional[List[str]] = Field(default_factory=list)
    backend_configs: Optional[dict] = None

# === Backends (as named collection) ===
class BackendConfig(BaseModel):
    name: str
    backend: str
    sync: bool = False
    url: SecretStr = None
    ttl: Optional[str] = None

# === Project Config ===
class GroxProjectConfig(BaseModel):
    version: Literal["1.0.0"]
    metadata: ProjectMetadata
    orchestration: Optional[OrchestrationConfig] = None
    infrastructure: Optional[InfrastructureConfig] = None

    @classmethod
    def load_yaml(cls, path: str, secrets: dict = None) -> "GroxProjectConfig":
        abs_path = Path(path).resolve()
        base_dir = abs_path.parent

        root = load_seyaml(abs_path, secrets)
        if "orchestration" in root:
            orch = root["orchestration"]
            if "documents" in orch:
                document_paths = [
                    str((base_dir / document_path).resolve())
                    for document_path in orch.get("documents", [])
                ]
                orch["documents"] = document_paths

        if "infrastructure" in root:
            infra = root["infrastructure"]
            if "models" in infra:
                model_paths = [
                    str((base_dir / model_path).resolve())
                    for model_path in infra.get("models", [])
                ]
                infra["model_configs"] = load_model_configs(model_paths, secrets=secrets)
            if "backends" in infra:
                backend_paths = [
                    str((base_dir / backend_path).resolve())
                    for backend_path in infra.get("backends", [])
                ]
                infra["backend_configs"] = load_backend_configs(backend_paths, secrets=secrets)

        return cls(**root)

def load_backend_configs(paths: List[str], secrets: dict = None) -> Dict[str, BackendConfig]:
    configs: Dict[str, BackendConfig] = {}

    for path in paths:
        full_path = Path(path).resolve()
        raw = load_seyaml(full_path, secrets)

        if not isinstance(raw, list):
            raise ValueError(f"{full_path} must contain a list at the top level")

        for item in raw:
            if not isinstance(item, dict):
                raise ValueError(f"Each backend entry must be a mapping")
            if "name" not in item:
                raise ValueError("Each backend config must include a 'name' field")
            config = BackendConfig(**item)
            configs[config.name] = config

    return configs
