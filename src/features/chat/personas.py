import os
import glob
from src.features.chat.models import PersonaModel
from src.shared.logger import logger

current_dir = os.path.dirname(os.path.abspath(__file__))

def get_base_system_prompt() -> str:
    prompt_path = os.path.abspath(os.path.join(current_dir, "../../..", "SYSTEM_PROMPT.md"))
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback in case the file goes missing
        return "{{PERSONA_PROMPT}}\nUser: {{FIRST_NAME}}\nActive Training Block:\n**{{ACTIVE_TRAINING_BLOCK}}**\nActive Directives: {{ACTIVE_DIRECTIVES}}\nCurrent Time: {{CURRENT_TIMESTAMP}}"

def load_personas() -> dict[str, PersonaModel]:
    personas = {}
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
            
        personas[persona_id] = PersonaModel(
            id=persona_id,
            name=persona_name,
            persona_prompt=content
        )
        
    return personas

def get_persona(persona_id: str) -> PersonaModel:
    personas = load_personas()
    
    if persona_id in personas:
        logger.info(f"Successfully loaded persona '{persona_id}' (originating from markdown file).")
        return personas[persona_id]
        
    # Handle the fallback safely if none or missing
    if not personas:
        fallback = PersonaModel(
            id="cheering-coach",
            name="Cheering Coach",
            persona_prompt="You are an uplifting, empathetic, and holistic running coach. Your archetype is the 'Cheering Coach'. You believe that the best training plan is the one the athlete actually enjoys."
        )
    else:
        fallback = personas.get("cheering-coach", list(personas.values())[0])
        
    logger.warning(f"Persona requested '{persona_id}' not found. Falling back to default '{fallback.id}'.")
    return fallback

def build_system_prompt(persona: PersonaModel, first_name: str, current_timestamp: str, active_directives_str: str, biometrics_str: str, active_block_str: str) -> str:
    prompt = get_base_system_prompt()
    prompt = prompt.replace("{{PERSONA_PROMPT}}", persona.persona_prompt)
    prompt = prompt.replace("{{FIRST_NAME}}", first_name)
    prompt = prompt.replace("{{ACTIVE_TRAINING_BLOCK}}", active_block_str)
    prompt = prompt.replace("{{ACTIVE_DIRECTIVES}}", active_directives_str)
    prompt = prompt.replace("{{BIOMETRICS}}", biometrics_str)
    prompt = prompt.replace("{{CURRENT_TIMESTAMP}}", current_timestamp)
    
    return prompt
