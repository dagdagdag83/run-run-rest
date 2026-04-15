from pydantic import BaseModel

class ChatPayload(BaseModel):
    message: str
