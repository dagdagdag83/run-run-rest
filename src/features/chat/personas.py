import os
from src.features.chat.models import PersonaModel

# Load the base system prompt once at module initialization
current_dir = os.path.dirname(os.path.abspath(__file__))
prompt_path = os.path.join(current_dir, "SYSTEM_PROMPT.md")
try:
    with open(prompt_path, "r", encoding="utf-8") as f:
        BASE_SYSTEM_PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    # Fallback in case the file goes missing
    BASE_SYSTEM_PROMPT_TEMPLATE = "{{PERSONA_PROMPT}}\nUser: {{FIRST_NAME}}\nActive Directives: {{ACTIVE_DIRECTIVES}}\nCurrent Time: {{CURRENT_TIMESTAMP}}"

PERSONAS = {
    "supportive-realist": PersonaModel(
        id="supportive-realist",
        name="Supportive Realist",
        system_prompt="You are a supportive but realistic fitness coach. You encourage the user but don't sugarcoat the effort required."
    )
}

def get_persona(persona_id: str) -> PersonaModel:
    return PERSONAS.get(persona_id, PERSONAS["supportive-realist"])

def build_system_prompt(persona: PersonaModel, first_name: str, current_timestamp: str, active_directives_str: str, biometrics_str: str) -> str:
    prompt = BASE_SYSTEM_PROMPT_TEMPLATE
    prompt = prompt.replace("{{PERSONA_PROMPT}}", persona.system_prompt)
    prompt = prompt.replace("{{FIRST_NAME}}", first_name)
    prompt = prompt.replace("{{ACTIVE_DIRECTIVES}}", active_directives_str)
    prompt = prompt.replace("{{BIOMETRICS}}", biometrics_str)
    prompt = prompt.replace("{{CURRENT_TIMESTAMP}}", current_timestamp)
    
    return prompt
