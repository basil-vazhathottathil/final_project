from langchain_core.messages import SystemMessage, HumanMessage # type: ignore


def build_summary_prompt(history: list):
    return [
        SystemMessage(
            content=(
                "You are a vehicle diagnostic assistant.\n"
                "Summarize the conversation so far focusing on:\n"
                "- Reported symptoms\n"
                "- When it happens\n"
                "- What is confirmed\n"
                "- What is ruled out\n"
                "- User DIY skill level\n"
                "- Open questions\n"
                "Keep it concise and factual."
            )
        ),
        HumanMessage(content=str(history)),
    ]
