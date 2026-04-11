from pydantic import BaseModel, Field

class OpenLoopCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    owner: str | None = Field(default=None, max_length=100)
    priority: str | None = Field(default="normal", max_length=20)
