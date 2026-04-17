from pydantic import BaseModel

class ChatPayload(BaseModel):
    message: str

class PersonaModel(BaseModel):
    id: str
    name: str
    persona_prompt: str
