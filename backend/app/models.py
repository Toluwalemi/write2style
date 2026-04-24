from typing import Any

from pydantic import BaseModel, Field


class PersonaCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=500)


class Persona(BaseModel):
    id: str
    name: str
    description: str
    style_dna: dict[str, Any] | None = None
    sample_count: int = 0


class Sample(BaseModel):
    id: str
    filename: str
    content_type: str
    chunk_count: int
    char_count: int


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
