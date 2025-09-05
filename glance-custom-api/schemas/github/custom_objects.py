from dataclasses import dataclass
from datetime import datetime


@dataclass
class CustomGithubReaction:
    plus_1: int
    minus_1: int
    laugh: int
    hooray: int
    confused: int
    heart: int
    rocket: int
    eyes: int


@dataclass
class CustomGithubItem:
    repo_name: str
    repo_url: str
    release_name: str
    release_published_at: datetime
    release_url: str
    release_reactions: CustomGithubReaction | None
    release_body: str
    avatar_url: str
