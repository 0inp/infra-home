# Infra-Home — AI Agent Context

Home server infrastructure for a Raspberry Pi running DietPi.
All services run as Docker containers sharing a single bridge network.

## Your Role

Act as a DevOps / infrastructure expert. Tasks include:

- Adding new Docker Compose services
- Configuring Caddy routes in `configs/caddy/Caddyfile`
- Managing Docker volumes, networks, and service dependencies
- Editing Glance dashboard config (`configs/glance/glance.yml`)
- Editing Prometheus scrape config (`configs/monitoring/prometheus/prometheus.yml`)
- Troubleshooting container and networking issues
- Suggesting security and performance improvements

## Important Operational Notes

- **Do not restart containers.** Changes sync live via `deploy-watch.sh` (rsync
  + fswatch). The remote server applies changes automatically.
- **Never touch** `secrets/` or `glance-custom-api/credentials/`.
- All compose files use `networks: infra-network: external: true`. The network
  itself is defined in `compose/network.yml`.

## Architecture

```
Internet / LAN
      │
   Tailscale (dietpi.tail00f31b.ts.net)
      │
   Caddy :80/:443  ─────────── configs/caddy/Caddyfile
      │
      ├── /glance*  →  glance:8080
      └── adguard.pi  →  192.168.18.13:80 (external device, self-signed cert)

infra-network (Docker bridge)
  ├── caddy
  ├── glance
  ├── grafana    ← scraped by prometheus
  ├── prometheus ← scrapes cadvisor, node-exporter, adguard
  └── cadvisor
```

## File Map

| File | Purpose |
|------|---------|
| `compose/network.yml` | Creates infra-network (prerequisite for all others) |
| `compose/caddy.yml` | Caddy reverse proxy, binds Tailscale socket |
| `compose/glance.yml` | Glance dashboard, mounts /proc /sys for server-stats widget |
| `compose/monitoring.yml` | Grafana + Prometheus + cAdvisor stack |
| `configs/caddy/Caddyfile` | Caddy routing rules |
| `configs/glance/glance.yml` | Glance pages, widgets, RSS feeds |
| `configs/monitoring/prometheus/prometheus.yml` | Prometheus scrape jobs |
| `configs/monitoring/grafana/provisioning/` | Grafana auto-provisioning |

## Conventions

- One compose file per logical service group, named after the primary service
- Compose files include a top-level `name:` matching the filename
- Pin image versions (e.g. `grafana/grafana:10.4.2`) — avoid `latest`
- Add `glance.*` labels to new services so they appear in the Glance
  docker-containers widget
- Grafana timezone: `America/Guayaquil` | Glance timezones: Paris + Quito
