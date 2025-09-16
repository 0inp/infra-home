import logging
from datetime import datetime, timedelta, timezone

from cachetools import TTLCache, cached
from fastapi import APIRouter, Request, Response
from github import Github
from github.Event import Event
from github.GithubException import UnknownObjectException
from github.GitRelease import GitRelease
from github.NamedUser import NamedUser
from github.PaginatedList import PaginatedList
from github.Repository import Repository
from markdown_it import MarkdownIt

from schemas.github.custom_objects import CustomGithubItem, CustomGithubReaction

# Cache 1 day for subscriptions
user_starred_repo_cache = TTLCache(maxsize=1000, ttl=3600 * 24)

repo_last_release_cache = TTLCache(maxsize=1000, ttl=3600)

user_following_users = TTLCache(maxsize=1000, ttl=3600 * 24)

following_user_events = TTLCache(maxsize=1000, ttl=3600)

logger = logging.getLogger(__name__)
router = APIRouter()


def render_html(items: list[CustomGithubItem]) -> str:
    if not items:
        return "<div>Could not load GitHub releases.</div>"

    # Sort items by release published date
    items.sort(key=lambda x: x.item_date, reverse=True)

    html = """
    <style>
      .github-release-header {
        display: flex;
        flex-direction: row;
        gap: 1rem;
      }
      .github-release-avatar {
        max-width: 5rem;
      }
      .github-release-body {
        color: black;
        background-color: #919191;
        padding: 0.5rem;
        margin: 1rem 0;
        border-radius: 1rem;
      }
    </style>
    <div class="cards-vertical">
    """

    md = MarkdownIt()
    logging.getLogger("markdown_it").setLevel(logging.WARNING)

    for item in items:
        # Truncate and render markdown body to HTML
        body_html = ""
        if item.body:
            truncated_body = item.body.splitlines()
            if len(truncated_body) > 10:
                truncated_body = truncated_body[:10]
                body_html = md.render("\n".join(truncated_body) + "...\n")
            else:
                body_html = md.render(item.body)

        # Prepare reactions string
        reactions_html = ""
        if item.reactions:
            emojis = {
                "plus_1": "👍",
                "minus_1": "👎",
                "laugh": "😄",
                "hooray": "🎉",
                "confused": "😕",
                "heart": "❤️",
                "rocket": "🚀",
                "eyes": "👀",
            }
            for reaction, emoji in emojis.items():
                count = getattr(item.reactions, reaction)
                if count > 0:
                    reactions_html += f"<li>{emoji} {count}</li>"

        html += f"""
        <div class="card">
            <div class="github-release-header">
                <img class="github-release-avatar" src="{item.avatar_url}" alt="{item.title} loading="lazy" author avatar">
                <ul class="list">
                    <li class="size-h3"><a class="color-primary-if-not-visited" href="{item.title_url}" target="_blank">{item.title}</a></li>
                    <li class="size-h4"><a class="color-highlight" href="{item.subtitle_url}" target="_blank">{item.subtitle or 'Release'}</a></li>
                </ul>
            </div>
            <hr class="margin-block-3">
            <div class="github-release-body">
                {body_html}
            </div>
            <ul class="list-horizontal-text">
                {reactions_html}
            </ul>
        </div>
        <hr class="margin-block-10">
        """

    html += "</div>"
    return html


@cached(user_starred_repo_cache)
def fetch_user_starred_repo(github_client: Github) -> PaginatedList[Repository]:
    return github_client.get_user().get_starred()


@cached(repo_last_release_cache)
def fetch_repo_last_release(repo: Repository) -> CustomGithubItem | None:
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    releases: list[GitRelease] = repo.get_releases().get_page(0)
    if releases:
        latest_release = releases[0]
        if latest_release and latest_release.published_at > one_week_ago:
            reactions = None
            if latest_release.reactions:
                reactions = CustomGithubReaction(
                    plus_1=latest_release.reactions["+1"],
                    minus_1=latest_release.reactions["-1"],
                    laugh=latest_release.reactions["laugh"],
                    hooray=latest_release.reactions["hooray"],
                    confused=latest_release.reactions["confused"],
                    heart=latest_release.reactions["heart"],
                    rocket=latest_release.reactions["rocket"],
                    eyes=latest_release.reactions["eyes"],
                )

            item = CustomGithubItem(
                title=repo.full_name,
                title_url=repo.html_url,
                subtitle=latest_release.name,
                subtitle_url=latest_release.html_url,
                item_date=latest_release.published_at,
                reactions=reactions,
                body=latest_release.body,
                avatar_url=(
                    repo.organization.avatar_url
                    if repo.organization
                    else latest_release.author.avatar_url
                ),
            )
            return item


@cached(user_following_users)
def fetch_user_following_users(github_client: Github) -> PaginatedList[NamedUser]:
    return github_client.get_user().get_following()


@cached(following_user_events)
def fetch_following_user_events(following_user: NamedUser) -> CustomGithubItem | None:
    following_user_events: list[Event] = following_user.get_events().get_page(0)
    if following_user_events:
        latest_event = following_user_events[0]
        try:
            latest_event.repo.full_name
        except UnknownObjectException:
            logger.info(
                f"The repository of the event {latest_event} is not public and can't be accessed"
            )
            return

        logger.info(f"Event type: {latest_event.type}")
        item = CustomGithubItem(
            title=latest_event.actor.display_login,
            title_url=latest_event.actor.url,
            subtitle=latest_event.repo.full_name,
            subtitle_url=latest_event.repo.url,
            item_date=latest_event.created_at,
            reactions=None,
            body=str(latest_event.payload),
            avatar_url=latest_event.actor.avatar_url,
        )
        return item


@router.get("/github/feed")
def github_feed(request: Request) -> Response:
    github_client: Github = request.app.state.github_client

    items: list[CustomGithubItem] = []

    # Step 1 : Get releases for starred repo
    starred_user_repos: PaginatedList[Repository] = fetch_user_starred_repo(
        github_client
    )
    for repo in starred_user_repos:
        item: CustomGithubItem | None = fetch_repo_last_release(repo)
        if item:
            items.append(item)

    # Step 2 : Get news from user I follow
    following_users: PaginatedList[NamedUser] = fetch_user_following_users(
        github_client
    )
    for following_user in following_users:
        logger.info(f"user : {following_user}")
        following_user_event_item: CustomGithubItem | None = (
            fetch_following_user_events(following_user)
        )
        if following_user_event_item:
            items.append(following_user_event_item)

    logger.info(f"Found {len(items)} news for the feed.")

    items_sorted_by_date = sorted(items, key=lambda item: item.item_date, reverse=True)

    html_content: str = render_html(items_sorted_by_date)

    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Widget-Title": "GitHub Releases",
            "Widget-Title-URL": "https://github.com/stars",
            "Widget-Content-Type": "html",
        },
    )
