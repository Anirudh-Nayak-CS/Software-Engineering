from infrastructure.config import Settings, settings
from prompts.requirement_generation import REQUIREMENT_GENERATION_PROMPT


def generate_requirement_specification(
    user_requirement: str,
    retrieved_context: str,
    llm,
    app_settings: Settings = settings,
) -> str:
    """Generate a source-grounded requirement spec from retrieved context."""
    system_prompt = REQUIREMENT_GENERATION_PROMPT.replace(
        "{user_requirement}", user_requirement
    ).replace("{context}", retrieved_context)
    return llm(
        system_prompt,
        "Generate the requirement specification from the supplied project requirement "
        "and retrieved evidence.",
        max_new_tokens=app_settings.requirement_spec_tokens,
        max_time=app_settings.requirement_generation_max_seconds,
        do_sample=True,
        temperature=0.3,
        top_p=0.9,
    )
