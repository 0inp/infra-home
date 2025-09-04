from typing import Optional, Dict
from pydantic import BaseModel
from schemas.youtube.commons import Thumbnail


class ContentSnippet(BaseModel):
    categoryId: Optional[str]
    channelId: str
    description: Optional[str]
    publishedAt: str
    thumbnails: Dict[str, Thumbnail]
    title: str


class ContentDetails(BaseModel):
    duration: Optional[str]
    dimension: Optional[str]
    definition: Optional[str]


class VideoItem(BaseModel):
    id: str
    snippet: ContentSnippet
    contentDetails: Optional[ContentDetails]


class VideoListResponse(BaseModel):
    items: list[VideoItem]
