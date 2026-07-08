from typing import Literal
from pydantic import BaseModel

Status = Literal["scored", "na", "not_evaluated"]

class Block(BaseModel):
    kind: str
    text: str = ""
    page: int = 0
    section: str | None = None

class ParsedDoc(BaseModel):
    doc_id: str
    markdown: str
    blocks: list[Block]
    parse_confidence: float

class CriterionScore(BaseModel):
    id: str
    tag: Literal["D", "H", "L"]
    weight: int
    status: Status
    score: int | None = None
    justification: str
    evidence: str | None = None

class DocScore(BaseModel):
    doc_id: str
    global_pct: float
    level: str
    coverage_pct: float
    dimensions: dict[str, float]
    criteria: list[CriterionScore]
    worst_sections: list[str] = []
    flags: list[str] = []
    config_hash: str
