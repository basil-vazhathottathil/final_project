from langchain_core.messages import SystemMessage, HumanMessage # type: ignore


def build_issue_prompt(chat_summary: str):
    return [
        SystemMessage(
            content=(
                "You are a professional vehicle diagnostician.\n"
                "Based on the summary, extract ONE issue as JSON:\n"
                "{"
                "  \"title\": \"\",\n"
                "  \"summary\": \"\",\n"
                "  \"severity\": \"LOW|MEDIUM|HIGH\"\n"
                "}\n"
                "Severity is based on fixability by a non-professional."
            )
        ),
        HumanMessage(content=chat_summary or ""),
    ]
