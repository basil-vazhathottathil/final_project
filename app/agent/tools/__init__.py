from app.agent.tools.web_search import get_web_search_tool
from app.agent.tools.workshop_giver import get_workshop_tool

def get_tools():
    return [
        get_web_search_tool(),
        get_workshop_tool(),
    ]
