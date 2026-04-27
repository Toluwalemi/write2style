import pytest
from pydantic import ValidationError

from app.models import GenerateRequest, Persona, PersonaCreate, Sample


class TestPersonaCreate:
    def test_valid(self):
        p = PersonaCreate(name="Professional", description="formal voice")
        assert p.name == "Professional"
        assert p.description == "formal voice"

    def test_default_description(self):
        p = PersonaCreate(name="Casual")
        assert p.description == ""

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            PersonaCreate(name="")

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            PersonaCreate(name="x" * 81)

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            PersonaCreate(name="ok", description="x" * 501)


class TestGenerateRequest:
    def test_valid(self):
        r = GenerateRequest(prompt="write a tweet")
        assert r.prompt == "write a tweet"

    def test_empty_prompt_rejected(self):
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="")

    def test_prompt_too_long(self):
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="x" * 4001)


class TestPersona:
    def test_minimal(self):
        p = Persona(id="abc", name="x", description="")
        assert p.style_dna is None
        assert p.sample_count == 0


class TestSample:
    def test_required_fields(self):
        s = Sample(id="1", filename="a.txt", content_type="text/plain", chunk_count=2, char_count=100)
        assert s.chunk_count == 2
