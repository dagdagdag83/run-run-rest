import os
from src.core.models import PersonaModel

# Load the base system prompt once at module initialization
current_dir = os.path.dirname(os.path.abspath(__file__))
prompt_path = os.path.join(current_dir, "SYSTEM_PROMPT.md")
try:
    with open(prompt_path, "r", encoding="utf-8") as f:
        BASE_SYSTEM_PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    # Fallback in case the file goes missing
    BASE_SYSTEM_PROMPT_TEMPLATE = "{{PERSONA_PROMPT}}\nUser: {{FIRST_NAME}}\nGoals: {{ACTIVE_GOALS}}\nCurrent Time: {{CURRENT_TIMESTAMP}}"

PERSONAS = {
    "supportive-realist": PersonaModel(
        id="supportive-realist",
        name="Supportive Realist",
        system_prompt="You are a supportive but realistic fitness coach. You encourage the user but don't sugarcoat the effort required."
    )
}

def get_persona(persona_id: str) -> PersonaModel:
    return PERSONAS.get(persona_id, PERSONAS["supportive-realist"])

def build_system_prompt(persona: PersonaModel, first_name: str, current_timestamp: str, active_goals: list[str] | str | None = None) -> str:
    # Format active goals gracefully
    if not active_goals:
        goals_str = "None specified"
    elif isinstance(active_goals, list):
        goals_str = ", ".join(active_goals)
    else:
        goals_str = str(active_goals)
        
    prompt = BASE_SYSTEM_PROMPT_TEMPLATE
    prompt = prompt.replace("{{PERSONA_PROMPT}}", persona.system_prompt)
    prompt = prompt.replace("{{FIRST_NAME}}", first_name)
    prompt = prompt.replace("{{ACTIVE_GOALS}}", goals_str)
    prompt = prompt.replace("{{CURRENT_TIMESTAMP}}", current_timestamp)
    
    return prompt
