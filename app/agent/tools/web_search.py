from langchain_community.tools.tavily_search import TavilySearchResults # type: ignore
from app.config import TAVILY_API_KEY

def get_web_search_tool():
    return TavilySearchResults(
        api_key=TAVILY_API_KEY,
        max_results=5,
        search_depth="advanced"
    )
