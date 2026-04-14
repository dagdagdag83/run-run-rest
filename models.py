from pydantic import BaseModel

class ChatPayload(BaseModel):
    message: str

class PersonaModel(BaseModel):
    id: str
    name: str
    system_prompt: str
