# Infra-Home Project

This project is for setting up and managing my home server infrastructure.

## Architecture

-   The entire infrastructure is based on Docker containers.
-   Each service is defined in a `docker-compose.yml` file.
-   `Caddy` is used as a reverse proxy to manage networking and provide HTTPS.

## Current Services

-   **AdGuard:** A network-wide ad blocker.
-   **Glance:** A self-hosted dashboard to monitor the server.
-   **Custom FastAPI Backend:** A small backend that provides custom endpoints for the Glance dashboard, including:
    -   Latest videos from YouTube subscriptions.
    -   A GitHub feed with the latest releases of starred repositories.

## Future Services

I am planning to add the following services:

-   **Photo Storage:** Immich
-   **Note Taking:** Docmost (as a Notion alternative)
-   **AI Assistant:** (Details to be defined)
-   **Media Services:**
    -   Radarr (for movies)
    -   Sonarr (for TV shows)
    -   Prowlarr (indexer manager)
    -   A media player like Jellyfin or Plex.

## Networking

The networking is managed by Caddy. Caddy is a powerful, enterprise-ready, open source web server with automatic HTTPS written in Go.

Each service is exposed through a subdomain of a primary domain. For example:

-   `adguard.my-domain.com`
-   `glance.my-domain.com`

Caddy automatically handles the SSL certificates for each subdomain.

The `docker-compose.yml` files are configured to use a custom network called `caddy`. This allows Caddy to discover and route traffic to the other containers.

## Tools

-   **Docker:** For containerization.
-   **Docker Compose:** For defining and running multi-container Docker applications.
-   **Caddy:** For reverse proxying and automatic HTTPS.
-   **FastAPI:** For the custom backend.
-   **Glance:** For the dashboard.
-   **AdGuard:** For ad blocking.
