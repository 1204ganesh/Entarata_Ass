from typing import Literal, Optional
from pydantic import BaseModel, Field


Language = Literal["python", "javascript"]
AnnotationKind = Literal[
    "function",
    "class",
    "import",
    "loop",
    "conditional",
    "return",
    "assignment",
    "call",
]


class ExplainRequest(BaseModel):
    language: Language
    code: str = Field(min_length=1, max_length=12000)
    includeOptimization: bool = True


class Annotation(BaseModel):
    kind: AnnotationKind
    line: int
    name: str
    detail: str


class Complexity(BaseModel):
    time: str
    space: str
    confidence: Literal["low", "medium", "high"]
    reason: str


class ExplainResponse(BaseModel):
    id: str
    language: Language
    explanation: str
    annotations: list[Annotation]
    optimizedCode: Optional[str] = None
    optimizationSummary: Optional[str] = None
    complexity: Complexity
    provider: str
