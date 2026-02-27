from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from typing import Any, get_args, get_origin


@dataclass(slots=True)
class FeatureSchemaField:
    name: str
    type: str


@dataclass(slots=True)
class FeatureSchema:
    version: str
    fields: list[FeatureSchemaField]


@dataclass(slots=True)
class FeatureArtifactMetadata:
    dataset_name: str
    version: str
    created_at: str
    row_count: int
    content_hash: str
    schema_hash: str
    schema_version: str
    quality: dict[str, Any]


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def compute_content_hash(rows_json_bytes: bytes) -> str:
    return hashlib.sha256(rows_json_bytes).hexdigest()


def compute_schema_hash(schema: FeatureSchema) -> str:
    canonical = canonical_json_bytes(_schema_to_payload(schema))
    return hashlib.sha256(canonical).hexdigest()


def build_schema_from_dataclass(dc_type: type[Any], version: str = "v1") -> FeatureSchema:
    if not is_dataclass(dc_type):
        raise TypeError("build_schema_from_dataclass requiere un tipo dataclass.")
    schema_fields = [
        FeatureSchemaField(name=item.name, type=_annotation_to_name(item.type)) for item in fields(dc_type)
    ]
    return FeatureSchema(version=version, fields=schema_fields)


def feature_schema_to_dict(schema: FeatureSchema) -> dict[str, Any]:
    return _schema_to_payload(schema)


def feature_schema_from_dict(payload: dict[str, Any]) -> FeatureSchema:
    version = str(payload.get("version", ""))
    raw_fields = payload.get("fields", [])
    parsed_fields = [
        FeatureSchemaField(name=str(item["name"]), type=str(item["type"])) for item in raw_fields
    ]
    return FeatureSchema(version=version, fields=parsed_fields)


def feature_metadata_to_dict(metadata: FeatureArtifactMetadata) -> dict[str, Any]:
    return {
        "dataset_name": metadata.dataset_name,
        "version": metadata.version,
        "created_at": metadata.created_at,
        "row_count": metadata.row_count,
        "content_hash": metadata.content_hash,
        "schema_hash": metadata.schema_hash,
        "schema_version": metadata.schema_version,
        "quality": metadata.quality,
    }


def feature_metadata_from_dict(payload: dict[str, Any]) -> FeatureArtifactMetadata:
    return FeatureArtifactMetadata(
        dataset_name=str(payload["dataset_name"]),
        version=str(payload["version"]),
        created_at=str(payload["created_at"]),
        row_count=int(payload["row_count"]),
        content_hash=str(payload["content_hash"]),
        schema_hash=str(payload["schema_hash"]),
        schema_version=str(payload["schema_version"]),
        quality=dict(payload.get("quality", {})),
    )


def _schema_to_payload(schema: FeatureSchema) -> dict[str, Any]:
    return {
        "version": schema.version,
        "fields": [{"name": field.name, "type": field.type} for field in schema.fields],
    }


def _annotation_to_name(annotation: Any) -> str:
    origin = get_origin(annotation)
    if origin is None:
        return getattr(annotation, "__name__", str(annotation))
    args = ", ".join(_annotation_to_name(arg) for arg in get_args(annotation))
    return f"{getattr(origin, '__name__', str(origin))}[{args}]"
