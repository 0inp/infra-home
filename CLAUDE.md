# Infra-Home — Claude Code Context

Home server infrastructure managed as code and synced live to a Raspberry Pi
running DietPi (hostname: `dietpi`).

## Workflow

Changes are synced to the remote server in real-time via `deploy-watch.sh`
(uses `fswatch` + `rsync`). The remote server auto-reloads containers on config
changes, so you do **not** need to restart containers after editing files.

To start the watcher: `./deploy-watch.sh`

## Repository Layout

```
compose/          # Docker Compose files, one per service group
  network.yml     # Creates the shared "infra-network" bridge network (run first)
  caddy.yml       # Caddy reverse proxy
  glance.yml      # Glance dashboard
  monitoring.yml  # Grafana + Prometheus + cAdvisor + adguard-exporter
  speedtest.yml   # Speedtest Prometheus exporter

configs/          # Runtime config files (bind-mounted into containers)
  caddy/Caddyfile
  glance/glance.yml
  monitoring/
    prometheus/prometheus.yml
    grafana/provisioning/datasources/prometheus.yml
    grafana/provisioning/dashboards/dashboards.yml
    grafana/provisioning/dashboards/pi-stats.json
    grafana/provisioning/dashboards/speedtest.json
    grafana/provisioning/dashboards/adguard.json

secrets/          # Gitignored — create manually on the server
  adguard.env     # ADGUARD_SERVERS, ADGUARD_USERNAMES, ADGUARD_PASSWORDS
```

## Services

| Service    | Image                        | Access                                    |
|------------|------------------------------|-------------------------------------------|
| Caddy      | caddy:2                      | Ports 80/443 on the host                  |
| Glance     | glanceapp/glance             | Via Caddy at `/glance`                    |
| Grafana          | grafana/grafana:12.1.1             | `http://grafana.pi` (internal)          |
| Prometheus       | prom/prometheus:v2.51.2            | `http://prometheus.pi` (internal)       |
| cAdvisor         | gcr.io/cadvisor/cadvisor:...       | Internal only                           |
| adguard-exporter | henrywhitaker3/adguard-exporter    | Internal only (port 9618)               |
| Speedtest        | danopstech/speedtest_exporter      | Internal only (port 9798)               |
| AdGuard Home     | (native install, not Docker)       | `http://192.168.18.13:3000` (LAN)      |
| Node Exporter    | (native install, not Docker)       | `192.168.18.13:9100` (scraped by Prom) |

## Networking

All containers share the `infra-network` Docker bridge (defined in
`compose/network.yml`, must be created before any other service).

External access goes through Caddy:
- Tailscale domain: `dietpi.tail00f31b.ts.net` — routes `/glance*` to glance
- Local DNS: `.pi` suffix (e.g. `grafana.pi`) resolved by AdGuard on the LAN

AdGuard Home runs natively on the Pi at `192.168.18.13:3000` (web UI) and port 53
(DNS). It is NOT a Docker container. The `adguard-exporter` container queries
AdGuard's API and exposes Prometheus metrics on port 9618; credentials live in
`secrets/adguard.env` (gitignored). Node Exporter also runs natively on the Pi.

## Key Constraints

- Never commit files under `secrets/` or `glance-custom-api/credentials/`
- The remote server path is `dietpi:/home/dietpi/infra-home/`
- All services use `restart: unless-stopped`
- Grafana timezone is `America/Guayaquil`; Glance shows both Paris and Quito

## Adding a New Service

1. Create `compose/<service>.yml` with `networks: infra-network: external: true`
2. Add `configs/<service>/` for any bind-mounted config
3. Add a Caddy route in `configs/caddy/Caddyfile` if external access is needed
4. Add Glance labels to the service if you want it in the docker-containers widget
