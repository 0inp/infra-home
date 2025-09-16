# Infra-Home Project

This project is for setting up and managing my home server infrastructure.

## Architecture

-   The entire infrastructure is based on Docker containers.
-   Each service is defined in a `docker-compose.yml` file.
-   `Caddy` is used as a reverse proxy to manage networking and provide HTTPS.

## Current Services

-   **Pi-hole:** A network-wide ad blocker.
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

## Role for Gemini

Your role in this project is to act as a DevOps and infrastructure expert. Your tasks include:

-   Helping me add new services to the `docker-compose.yml` files.
-   Configuring Caddy as a reverse proxy for the services.
-   Managing Docker volumes and networks.
-   Troubleshooting container-related issues.
-   Suggesting best practices for security and performance.

**Important Note:** The Docker containers are running on a remote server with sync and hot reload enabled. You should not need to restart the containers after making changes.