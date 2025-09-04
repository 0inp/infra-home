from typing import Optional
from pydantic import BaseModel


class ActivityUpload(BaseModel):
    videoId: str


class ActivityContentDetails(BaseModel):
    upload: Optional[ActivityUpload] = None


class ActivitySnippet(BaseModel):
    publishedAt: str
    channelId: str
    title: Optional[str] = None


class ActivityItem(BaseModel):
    id: str
    snippet: ActivitySnippet
    contentDetails: ActivityContentDetails


class ActivityListResponse(BaseModel):
    items: list[ActivityItem]
