import os
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Response
import google.oauth2.credentials
import googleapiclient.discovery
import googleapiclient.errors

logger = logging.getLogger(__name__)
router = APIRouter()

SCOPES: list[str] = ["https://www.googleapis.com/auth/youtube.readonly"]
CLIENT_SECRET_FILE: str = "credentials/client_secret.json"
TOKEN_FILE: str = "credentials/token.json"


def get_youtube_client() -> any:
    """Return an authenticated YouTube client using stored token.json."""
    if not os.path.exists(TOKEN_FILE):
        logger.error("Token file not found at %s", TOKEN_FILE)
        raise RuntimeError("Token file not found. Run OAuth flow locally to generate it.")

    creds = google.oauth2.credentials.Credentials.from_authorized_user_file(
        TOKEN_FILE, SCOPES
    )
    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)

def get_all_subscriptions(youtube_client) -> list:
    """Fetch all subscriptions for the authenticated user, handling pagination."""
    subscriptions = []
    next_page_token = None

    while True:
        response = youtube_client.subscriptions().list(
            part="snippet",
            mine=True,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        subscriptions.extend(response.get("items", []))
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    logger.info("Fetched %d subscriptions", len(subscriptions))
    return subscriptions

def fetch_recent_videos(youtube_client, subscriptions) -> list:
    """Return a list of video IDs from activities in the last week."""
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_videos_ids = []

    for sub in subscriptions:
        channel_id = sub["snippet"]["resourceId"]["channelId"]
        response = youtube_client.activities().list(
            part="contentDetails,snippet",
            channelId=channel_id,
            publishedAfter=one_week_ago.isoformat(),
            maxResults=50
        ).execute()

        for item in response.get("items", []):
            upload = item.get("contentDetails", {}).get("upload")
            if upload and "videoId" in upload:
                recent_videos_ids.append(upload["videoId"])

    logger.info("Fetched %d recent videos from all subscriptions", len(recent_videos_ids))
    return recent_videos_ids

def fetch_videos_metadata(youtube_client, video_ids) -> list:
    """Fetch video details in chunks of 50 IDs."""
    def chunked(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    all_videos = []
    for batch in chunked(video_ids, 50):
        response = youtube_client.videos().list(
            part="snippet,contentDetails,statistics",
            id=",".join(batch)
        ).execute()
        all_videos.extend(response.get("items", []))

    logger.info("Fetched metadata for %d videos", len(all_videos))
    return all_videos

def render_html(videos) -> str:
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
        vid_id = video["id"]
        title = video["snippet"]["title"]
        thumb = video["snippet"]["thumbnails"]["medium"]["url"]
        url = f"https://www.youtube.com/watch?v={vid_id}"

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
def youtube_latest() -> Response:
    youtube_client = get_youtube_client()
    subscriptions = get_all_subscriptions(youtube_client)
    recent_video_ids = fetch_recent_videos(youtube_client, subscriptions)
    videos_metadata = fetch_videos_metadata(youtube_client, recent_video_ids)
    html_content = render_html(videos_metadata)

    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Widget-Title": "Latest YouTube Videos",
            "Widget-Title-URL": "https://www.youtube.com/feed/subscriptions",
            "Widget-Content-Type": "html",
        },
    )
