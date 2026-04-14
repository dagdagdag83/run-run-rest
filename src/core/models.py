from pydantic import BaseModel

class PersonaModel(BaseModel):
    id: str
    name: str
    system_prompt: str
