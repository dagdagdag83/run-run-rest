import os
from src.features.chat.models import PersonaModel
from src.shared.logger import logger

# Load the base system prompt once at module initialization
current_dir = os.path.dirname(os.path.abspath(__file__))
prompt_path = os.path.abspath(os.path.join(current_dir, "../../..", "SYSTEM_PROMPT-v2.md"))
try:
    with open(prompt_path, "r", encoding="utf-8") as f:
        BASE_SYSTEM_PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    # Fallback in case the file goes missing
    BASE_SYSTEM_PROMPT_TEMPLATE = "{{PERSONA_PROMPT}}\nUser: {{FIRST_NAME}}\nActive Training Block:\n**{{ACTIVE_TRAINING_BLOCK}}**\nActive Directives: {{ACTIVE_DIRECTIVES}}\nCurrent Time: {{CURRENT_TIMESTAMP}}"

import glob

PERSONAS = {}

def load_personas():
    personas_dir = os.path.abspath(os.path.join(current_dir, "../../..", "personas"))
    if not os.path.exists(personas_dir):
        os.makedirs(personas_dir)
        
    for md_file in glob.glob(os.path.join(personas_dir, "*.md")):
        basename = os.path.basename(md_file)
        name_no_ext = os.path.splitext(basename)[0]
        
        persona_id = name_no_ext.lower().replace("_", "-")
        persona_name = name_no_ext.replace("_", " ").title()
        
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        PERSONAS[persona_id] = PersonaModel(
            id=persona_id,
            name=persona_name,
            persona_prompt=content
        )

# Load existing personas
load_personas()

# Fallback safely if none exist
if not PERSONAS:
    PERSONAS["supportive-realist"] = PersonaModel(
        id="supportive-realist",
        name="Supportive Realist",
        persona_prompt="You are a supportive but realistic fitness coach. You encourage the user but don't sugarcoat the effort required."
    )

def get_persona(persona_id: str) -> PersonaModel:
    if persona_id in PERSONAS:
        logger.info(f"Successfully loaded persona '{persona_id}' (originating from markdown file).")
        return PERSONAS[persona_id]
        
    fallback = PERSONAS.get("supportive-realist", list(PERSONAS.values())[0])
    logger.warning(f"Persona requested '{persona_id}' not found. Falling back to default '{fallback.id}'.")
    return fallback

def build_system_prompt(persona: PersonaModel, first_name: str, current_timestamp: str, active_directives_str: str, biometrics_str: str, active_block_str: str) -> str:
    prompt = BASE_SYSTEM_PROMPT_TEMPLATE
    prompt = prompt.replace("{{PERSONA_PROMPT}}", persona.persona_prompt)
    prompt = prompt.replace("{{FIRST_NAME}}", first_name)
    prompt = prompt.replace("{{ACTIVE_TRAINING_BLOCK}}", active_block_str)
    prompt = prompt.replace("{{ACTIVE_DIRECTIVES}}", active_directives_str)
    prompt = prompt.replace("{{BIOMETRICS}}", biometrics_str)
    prompt = prompt.replace("{{CURRENT_TIMESTAMP}}", current_timestamp)
    
    return prompt
