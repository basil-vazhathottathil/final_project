from langchain_core.messages import SystemMessage, HumanMessage  # type: ignore


def build_issue_prompt(chat_summary: str):
    return [
        SystemMessage(
            content=(
                "You are a professional vehicle diagnostician.\n\n"
                "From the provided conversation summary, extract AT MOST ONE vehicle issue.\n"
                "If the issue is not yet clear, extract a SUSPECTED issue.\n\n"

                "Respond with STRICT JSON ONLY. No explanations, no markdown.\n\n"

                "JSON format:\n"
                "{\n"
                "  \"title\": \"short issue name\",\n"
                "  \"summary\": \"concise diagnostic summary\",\n"
                "  \"severity\": \"LOW|MEDIUM|HIGH\"\n"
                "}\n\n"

                "Rules:\n"
                "- Use clear, mechanic-style language\n"
                "- Do NOT invent faults not supported by the summary\n"
                "- If information is insufficient, use a tentative title like:\n"
                "  \"Possible exhaust issue\" or \"Suspected sensor fault\"\n"
                "- Severity is based on fixability by a non-professional:\n"
                "  LOW = safe to monitor or DIY\n"
                "  MEDIUM = repairable but skill/tools needed\n"
                "  HIGH = unsafe or workshop required\n"
            )
        ),
        HumanMessage(content=chat_summary or ""),
    ]
