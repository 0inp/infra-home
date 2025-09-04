from typing import Optional
from pydantic import BaseModel, HttpUrl


class Thumbnail(BaseModel):
    url: HttpUrl
    width: Optional[int] = None
    height: Optional[int] = None
