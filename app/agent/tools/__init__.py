from app.agent.tools.web_search import get_web_search_tool

def get_tools():
    return [
        get_web_search_tool(),
        # add more tools later (maps, OBD decoder, etc.)
    ]
