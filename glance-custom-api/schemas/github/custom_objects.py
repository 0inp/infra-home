from datetime import datetime
from pydantic import BaseModel


class CustomGithubReaction(BaseModel):
    plus_1: int
    minus_1: int
    laugh: int
    hooray: int
    confused: int
    heart: int
    rocket: int
    eyes: int


class CustomGithubItem(BaseModel):
    title: str
    title_url: str
    subtitle: str | None
    subtitle_url: str | None
    item_date: datetime
    reactions: CustomGithubReaction | None
    body: str | None
    avatar_url: str
