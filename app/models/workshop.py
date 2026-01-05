from pydantic import BaseModel  # type: ignore
from typing import List


class WorkshopResponse(BaseModel):
    maps_urls: List[str]
