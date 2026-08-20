from pydantic import BaseModel, Field


class TranslationRequest(BaseModel):
    text: str
    source_language: str
    target_language: str


class TranslationResponse(BaseModel):
    text: str
    confidence: float = Field(ge=0, le=1)
