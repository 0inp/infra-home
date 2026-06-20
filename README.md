# Infra-Home

Home server infrastructure for a Raspberry Pi running DietPi, managed as code
and synced live with `rsync`.

## Architecture

All services run as Docker containers on a shared `infra-network` Docker bridge.
Caddy acts as a reverse proxy and handles HTTPS via Tailscale.

```
Tailscale (dietpi.tail00f31b.ts.net)
      │
   Caddy :80/:443
      ├── /glance*  →  Glance dashboard
      └── adguard.pi  →  AdGuard (192.168.18.13, separate device)

infra-network (Docker bridge)
  ├── caddy
  ├── glance
  ├── grafana
  ├── prometheus
  └── cadvisor
```

## Services

| Service    | Description                                  | Access                          |
|------------|----------------------------------------------|---------------------------------|
| Caddy      | Reverse proxy with automatic HTTPS           | Ports 80/443                    |
| Glance     | Self-hosted dashboard                        | `<tailscale-host>/glance`       |
| Grafana    | Metrics dashboards                           | `http://grafana.pi` (LAN only)  |
| Prometheus | Metrics collection (cAdvisor, node, AdGuard) | `http://prometheus.pi` (LAN)    |
| cAdvisor   | Docker container metrics                     | Internal only                   |
| AdGuard    | Network-wide ad blocker (external device)    | `192.168.18.13`                 |

## Deployment

Changes are synced in real-time to the remote server. Run the watcher once from
your development machine:

```bash
./deploy-watch.sh
```

This uses `fswatch` to watch the local directory and `rsync` to push changes to
`dietpi:/home/dietpi/infra-home/`. The remote server applies changes without
needing container restarts.

**Requires:** `fswatch` (`brew install fswatch`) and SSH access to `dietpi`.

## Repository Layout

```
compose/            # Docker Compose files
  network.yml       # Must be applied first — creates infra-network
  caddy.yml
  glance.yml
  monitoring.yml    # Grafana + Prometheus + cAdvisor

configs/            # Bind-mounted config files
  caddy/Caddyfile
  glance/glance.yml
  monitoring/
    prometheus/prometheus.yml
    grafana/provisioning/datasources/prometheus.yml

deploy-watch.sh     # Live-sync script (development use)
```

## Bootstrap (first run on a new server)

```bash
# 1. Create the shared network first
docker compose -f compose/network.yml up -d

# 2. Start services
docker compose -f compose/caddy.yml up -d
docker compose -f compose/glance.yml up -d
docker compose -f compose/monitoring.yml up -d
```

## Planned Services

- **Immich** — photo storage
- **Docmost** — note-taking (Notion alternative)
- **Media stack** — Radarr, Sonarr, Prowlarr, Jellyfin

## Tools

- **Docker / Docker Compose** — containerisation
- **Caddy** — reverse proxy, automatic HTTPS via Tailscale
- **Glance** — dashboard with RSS, server stats, docker widget
- **Grafana + Prometheus + cAdvisor** — monitoring
- **AdGuard Home** — DNS-level ad blocking (external device)
- **Tailscale** — secure remote access
