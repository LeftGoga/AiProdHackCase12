from pydantic import BaseModel, Field


class Message(BaseModel):
    username: str
    text: str
    file_urls: list[str] = Field(default_factory=list)
