from pydantic import BaseModel
from typing import List

class TranscriptionResponse(BaseModel):
    transcription: str
    summary: str
    notes: List[str]
