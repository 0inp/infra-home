from typing import Dict, List, Optional

from pydantic import BaseModel

from schemas.youtube.commons import Thumbnail


class SubscriptionThumbnails(BaseModel):
    default: Optional[Thumbnail] = None
    medium: Optional[Thumbnail] = None
    high: Optional[Thumbnail] = None


class SubscriptionSnippet(BaseModel):
    channelId: str
    description: Optional[str]
    publishedAt: str
    resourceId: Dict[str, str]
    thumbnails: Optional[SubscriptionThumbnails] = None
    title: str


class SubscriptionItem(BaseModel):
    id: str
    snippet: SubscriptionSnippet


class SubscriptionListResponse(BaseModel):
    items: List[SubscriptionItem]
    nextPageToken: Optional[str] = None
