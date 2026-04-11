from pydantic import BaseModel, Field

class ActionPayload(BaseModel):
    source: str = Field(min_length=1, max_length=100)
