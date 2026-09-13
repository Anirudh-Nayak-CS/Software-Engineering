from infrastructure.config import Settings, settings
from prompts.requirement_generation import REQUIREMENT_GENERATION_PROMPT
from services.retrieval import format_retrieved_documents


def generate_requirement_specification(
    user_requirement: str,
    retriever,
    llm,
    app_settings: Settings = settings,
) -> tuple[str, list]:
    """Retrieve evidence and generate the notebook's grounded PRD."""
    retrieved_documents = retriever.invoke(user_requirement)
    context = format_retrieved_documents(retrieved_documents)
    system_prompt = REQUIREMENT_GENERATION_PROMPT.replace(
        "{user_requirement}", user_requirement
    ).replace("{context}", context)
    specification = llm(
        system_prompt,
        "Generate the requirement specification from the supplied project requirement "
        "and evidence.",
        max_new_tokens=4096,
        do_sample=True,
        temperature=0.3,
        top_p=0.9,
    )
    return specification, list(retrieved_documents)
