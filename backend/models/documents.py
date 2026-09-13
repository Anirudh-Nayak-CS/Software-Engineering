from dataclasses import dataclass
from typing import Any, TypedDict


@dataclass(frozen=True)
class Document:
    name: str
    doc_type: str
    source: str
    text: str
    page: int


@dataclass(frozen=True)
class Chunk:
    text: str
    source: str
    chunk_id: int
    page: int


class GraphState(TypedDict):
    user_requirement: str
    retrieved_context: str
    retrieved_documents: list[dict[str, object]]
    prd_spec: str
    sdlc_recommendation: str


@dataclass(frozen=True)
class SourceReference:
    source: str
    page: int


@dataclass(frozen=True)
class PipelineResult:
    user_requirement: str
    retrieved_documents: list[Any]
    requirement_specification: str
    sdlc_recommendation: str
