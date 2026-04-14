from models import PersonaModel

PERSONAS = {
    "supportive-realist": PersonaModel(
        id="supportive-realist",
        name="Supportive Realist",
        system_prompt="You are a supportive but realistic fitness coach. You encourage the user but don't sugarcoat the effort required."
    )
}

def get_persona(persona_id: str) -> PersonaModel:
    return PERSONAS.get(persona_id, PERSONAS["supportive-realist"])
