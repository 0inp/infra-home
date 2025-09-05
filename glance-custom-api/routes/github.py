import logging

from cachetools import TTLCache, cached
from fastapi import APIRouter, Request, Response
from github import Github
from github.PaginatedList import PaginatedList
from github.Repository import Repository
from markdown_it import MarkdownIt

from schemas.github.custom_objects import CustomGithubItem, CustomGithubReaction

# Cache 1 day for subscriptions
user_starred_repo_cache = TTLCache(maxsize=1000, ttl=3600 * 24)

repo_last_release_cache = TTLCache(maxsize=1000, ttl=3600)

logger = logging.getLogger(__name__)
router = APIRouter()


def render_github_releases_html(items: list[CustomGithubItem]) -> str:
    if not items:
        return "<div>Could not load GitHub releases.</div>"

    # Sort items by release published date
    items.sort(key=lambda x: x.release_published_at, reverse=True)

    html = """
    <style>
      .release-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 1rem;
      }
      .release-card {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        padding: 1rem;
        border: 1px solid #333;
        border-radius: 8px;
      }
      .release-header {
        display: flex;
        align-items: center;
        gap: 1rem;
      }
      .release-header img {
        width: 48px;
        height: 48px;
        border-radius: 50%;
      }
      .release-titles {
        display: flex;
        flex-direction: column;
      }
      .repo-name a {
        font-size: 1.2rem;
        font-weight: bold;
        color: inherit;
        text-decoration: none;
      }
      .release-name a {
        font-size: 1rem;
        color: #aaa;
        text-decoration: none;
      }
      .release-body {
        background-color: #222;
        padding: 0.5rem;
        border-radius: 4px;
        font-size: 0.9rem;
      }
      .release-reactions {
        display: flex;
        gap: 0.5rem;
        align-items: center;
        font-size: 0.9rem;
      }
      .reaction {
        display: flex;
        align-items: center;
        gap: 0.2rem;
      }
    </style>
    <div class="release-grid">
    """

    md = MarkdownIt()
    logging.getLogger("markdown_it").setLevel(logging.WARNING)

    for item in items:
        # Truncate and render markdown body to HTML
        truncated_body = item.release_body.splitlines()
        if len(truncated_body) > 10:
            truncated_body = truncated_body[:10]
            body_html = md.render("\n".join(truncated_body) + "...\n")
        else:
            body_html = md.render(item.release_body)

        # Prepare reactions string
        reactions_html = ""
        if item.release_reactions:
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
                count = getattr(item.release_reactions, reaction)
                if count > 0:
                    reactions_html += f'<div class="reaction">{emoji} {count}</div>'

        html += f"""
        <div class="release-card">
            <div class="release-header">
                <img src="{item.avatar_url}" alt="{item.repo_name} author avatar">
                <div class="release-titles">
                    <div class="repo-name"><a href="{item.repo_url}" target="_blank">{item.repo_name}</a></div>
                    <div class="release-name"><a href="{item.release_url}" target="_blank">{item.release_name or 'Release'}</a></div>
                </div>
            </div>
            <div class="release-body">
                {body_html}
            </div>
            <div class="release-reactions">
                {reactions_html}
            </div>
        </div>
        """

    html += "</div>"
    return html


@cached(user_starred_repo_cache)
def fetch_user_starred_repo(github_client: Github) -> PaginatedList[Repository]:
    return github_client.get_user().get_starred()


@cached(repo_last_release_cache)
def fetch_repo_last_release(repo: Repository) -> CustomGithubItem | None:
    releases = repo.get_releases().get_page(0)
    if releases:
        release = releases[0]
        if release and release.reactions:
            reactions = CustomGithubReaction(
                plus_1=release.reactions["+1"],
                minus_1=release.reactions["-1"],
                laugh=release.reactions["laugh"],
                hooray=release.reactions["hooray"],
                confused=release.reactions["confused"],
                heart=release.reactions["heart"],
                rocket=release.reactions["rocket"],
                eyes=release.reactions["eyes"],
            )

            item = CustomGithubItem(
                repo_name=repo.name,
                repo_url=repo.html_url,
                release_name=release.name,
                release_published_at=release.published_at,
                release_url=release.html_url,
                release_reactions=reactions,
                release_body=release.body,
                avatar_url=(
                    repo.organization.avatar_url
                    if repo.organization
                    else release.author.avatar_url
                ),
            )
            return item


@router.get("/github/feed")
def github_feed(request: Request) -> Response:
    github_client: Github = request.app.state.github_client
    items: list[CustomGithubItem] = []
    starred_user_repos: PaginatedList[Repository] = fetch_user_starred_repo(
        github_client
    )
    for repo in starred_user_repos:
        item: CustomGithubItem | None = fetch_repo_last_release(repo)
        if item:
            items.append(item)

    logger.info(f"Found {len(items)} releases.")

    html_content: str = render_github_releases_html(items)

    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Widget-Title": "GitHub Releases",
            "Widget-Title-URL": "https://github.com/stars",
            "Widget-Content-Type": "html",
        },
    )
