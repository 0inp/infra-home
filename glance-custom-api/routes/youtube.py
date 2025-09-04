import logging
from datetime import datetime, timedelta, timezone

from cachetools import TTLCache, cached
from fastapi import APIRouter, Request, Response
from googleapiclient.discovery import Resource
from pydantic import HttpUrl

from schemas.youtube.activities import ActivityItem, ActivityListResponse
from schemas.youtube.subscriptions import SubscriptionItem, SubscriptionListResponse
from schemas.youtube.videos import VideoItem, VideoListResponse

# Cache 1 day for subscriptions
subscriptions_cache = TTLCache(maxsize=1000, ttl=3600 * 24)


# Cache 1 hour for subscriptions' activities
subscription_activities_cache = TTLCache(maxsize=1000, ttl=3600)


def subscriptions_activities_key(youtube_client, subscriptions: list[SubscriptionItem]):
    # Only use channel IDs as key
    channel_ids = tuple(sub.snippet.resourceId["channelId"] for sub in subscriptions)
    return channel_ids


# Cache 7 day for video details
video_cache = TTLCache(maxsize=1000, ttl=3600 * 24 * 7)


logger = logging.getLogger(__name__)
router = APIRouter()


@cached(subscriptions_cache)
def get_all_subscriptions(youtube_client: Resource) -> list[SubscriptionItem]:
    """Fetch all subscriptions for the authenticated user, handling pagination."""
    subscriptions: list[SubscriptionItem] = []
    next_page_token = None

    while True:
        response = (
            youtube_client.subscriptions()  # type: ignore[attr-defined]
            .list(part="snippet", mine=True, maxResults=50, pageToken=next_page_token)
            .execute()
        )

        paged_subscriptions = SubscriptionListResponse(**response)
        subscriptions.extend(paged_subscriptions.items)
        next_page_token = paged_subscriptions.nextPageToken
        if not next_page_token:
            break

    logger.info(f"Fetched {len(subscriptions)} subscriptions")
    return subscriptions


@cached(subscription_activities_cache, key=subscriptions_activities_key)
def fetch_recent_videos_ids(
    youtube_client: Resource, subscriptions: list[SubscriptionItem]
) -> list[str]:
    """Return a list of video IDs from activities in the last week."""
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_videos_ids: list[str] = []

    for sub in subscriptions:
        channel_id = sub.snippet.resourceId["channelId"]
        response = (
            youtube_client.activities()  # type: ignore[attr-defined]
            .list(
                part="contentDetails,snippet",
                channelId=channel_id,
                publishedAfter=one_week_ago.isoformat(),
                maxResults=1,
            )
            .execute()
        )
        activities: list[ActivityItem] = ActivityListResponse(**response).items

        for item in activities:
            upload = item.contentDetails.upload
            if upload:
                recent_videos_ids.append(upload.videoId)

    logger.info(
        "Fetched %d recent videos from all subscriptions", len(recent_videos_ids)
    )
    return recent_videos_ids


@cached(video_cache)
def fetch_video_metadata(youtube_client: Resource, video_id: str) -> VideoItem:
    """Fetch video details."""

    response = (
        youtube_client.videos()  # type: ignore[attr-defined]
        .list(part="snippet,contentDetails", id=video_id)
        .execute()
    )
    return VideoListResponse(**response).items[0]


def render_html(videos: list[VideoItem]) -> str:
    """Render Glance-compatible HTML for a list of videos."""
    html = """
    <style>
      .video-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
      }
      .video-card {
        text-align: center;
      }
      .video-card img {
        width: 100%;
        border-radius: 8px;
      }
      .video-card-title {
        margin-top: 0.5rem;
        font-size: 0.9rem;
      }
    </style>
    <div class="video-grid">
    """

    for video in videos:
        vid_id: str = video.id
        title: str = video.snippet.title
        thumb: HttpUrl = video.snippet.thumbnails["medium"].url
        url: str = f"https://www.youtube.com/watch?v={vid_id}"

        html += f"""
        <div class="video-card">
            <a href="{url}" target="_blank">
                <img src="{thumb}" alt="{title}">
            </a>
            <div class="video-card-title">{title}</div>
        </div>
        """

    html += "</div>"
    return html


@router.get("/youtube/latest")
def youtube_latest(request: Request) -> Response:
    youtube_client: Resource = request.app.state.youtube_client
    subscriptions: list[SubscriptionItem] = get_all_subscriptions(youtube_client)
    recent_video_ids: list[str] = fetch_recent_videos_ids(youtube_client, subscriptions)
    videos_metadatas: list[VideoItem] = []
    for recent_video_id in recent_video_ids:
        video_metadata: VideoItem = fetch_video_metadata(
            youtube_client, recent_video_id
        )
        videos_metadatas.append(video_metadata)
    html_content: str = render_html(videos_metadatas)

    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Widget-Title": "Latest YouTube Videos",
            "Widget-Title-URL": "https://www.youtube.com/feed/subscriptions",
            "Widget-Content-Type": "html",
        },
    )
