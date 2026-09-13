from prompts.sdlc_selection import SDLC_SELECTION_PROMPT


def select_sdlc_model(requirement_specification: str, llm) -> str:
    """Select and justify an SDLC model from the generated specification."""
    return llm(
        SDLC_SELECTION_PROMPT,
        f"Requirement Specification:\n\n{requirement_specification}",
        max_new_tokens=1000,
        do_sample=False,
    )
