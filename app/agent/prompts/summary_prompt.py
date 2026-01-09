from langchain_core.messages import SystemMessage, HumanMessage  # type: ignore


def build_summary_prompt(previous_summary: str, new_turn: str):
    return [
        SystemMessage(
            content=(
                "You are a vehicle diagnostic assistant.\n\n"
                "You maintain a running summary of a conversation.\n"
                "Update the existing summary using the new turn.\n\n"

                "Focus on:\n"
                "- Reported symptoms\n"
                "- When it happens\n"
                "- What is confirmed\n"
                "- What is ruled out\n"
                "- User DIY skill level\n"
                "- Open questions\n\n"

                "Rules:\n"
                "- Preserve previously confirmed facts\n"
                "- Remove items that are now ruled out\n"
                "- Add new information only if relevant\n"
                "- Do NOT repeat the full conversation\n"
                "- Keep the summary concise, factual, and stable\n"
            )
        ),
        HumanMessage(
            content=(
                f"Existing summary:\n{previous_summary or 'None'}\n\n"
                f"New turn:\n{new_turn}"
            )
        ),
    ]
