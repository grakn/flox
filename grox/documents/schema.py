import yaml
from pydantic import BaseModel, Field, constr, conlist, StringConstraints
from typing import List, Optional, Literal, Dict, Any, Annotated, Union
from redisvl.schema import IndexSchema, IndexInfo, BaseField
from redisvl.utils.utils import model_to_dict

# ----------------
# Field Definitions
# ----------------

class VectorAttrs(BaseModel):
    algorithm: Literal['flat', 'hnsw'] = 'flat'
    dims: int = 1536
    distance_metric: Literal['cosine', 'l2', 'ip'] = 'cosine'
    datatype: Literal['float32', 'float64'] = 'float32'


class FieldDef(BaseModel):
    name: str
    type: Literal['text', 'tag', 'numeric', 'vector']
    attrs: Optional[VectorAttrs] = None
    description: Optional[str] = None

class IndexSettings(BaseModel):
    name: str
    prefix: str
    key_separator: Optional[str] = ":"
    storage_type: Literal['json', 'hash'] = "hash"

# ----------------
# Collection Index Schema
# ----------------

class CollectionIndexSchema(BaseModel):
    fields: list[FieldDef] = []

    @staticmethod
    def from_dict(data: dict) -> "CollectionIndexSchema":
        if not isinstance(data, dict):
            raise ValueError("Expected a dictionary to construct CollectionIndexSchema")

        fields_data = data.get("fields", [])
        fields = [FieldDef(**field) for field in fields_data]
        return CollectionIndexSchema(fields=fields)

# ----------------
# Data Definition
# ----------------

class DataEntry(BaseModel):
    documents: List[str]
    metadata: Dict[str, Any]
    id: Optional[str] = None

# ----------------
# Collection with Data
# ----------------

class Collection(BaseModel):
    name: str
    index: Optional[IndexSettings] = None
    collection_schema: Optional[CollectionIndexSchema] = Field(None, alias="schema")
    data: List[DataEntry]

    def to_schema_dict(self) -> Dict[str, Any]:
        """Serialize the index schema model to a dictionary, handling Enums
        and other special cases properly.

        Returns:
            Dict[str, Any]: The index schema as a dictionary.
        """
        # Manually serialize to ensure all field attributes are preserved
        dict_schema = {
            "index": model_to_dict(self.index),
            "fields": [
                model_to_dict(field) for field in self.collection_schema.fields
            ],
            "version": "0.1.0"
        }
        return dict_schema

    def get_embedding_field_name(self, default: str = "embeddings") -> str:
        """
        Returns the name of the first vector field in the schema.
        Falls back to `default` if none found.
        """
        return next(
            (field.name for field in self.collection_schema.fields if field.type == "vector"),
            default
        )

    def get_content_field_name(self, default: str = "text") -> str:
        """
        Returns a primary text field name based on common conventions.
        Priority: 'text' > 'content' > default.
        """
        text_fields = [field.name for field in self.collection_schema.fields if field.type == "text"]

        for preferred in ("text", "content"):
            if preferred in text_fields:
                return preferred

        return default

# ----------------
# Document YAML structure
# ----------------

class Document(BaseModel):
    version: Annotated[str, StringConstraints(pattern=r'^\d+\.\d+\.\d+$')] = '0.1.0'
    collections: List[Collection]

    @classmethod
    def load_yaml(cls, path: str) -> "Document":
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return Document.model_validate(data)

    def to_yaml(self, path: str):
        with open(path, "w") as f:
            yaml.safe_dump(self.dict(), f)
