# Oasis Derek Dev preview deployment

The preview at `https://oasis-derek.xsolutionsmd.com` is a separate stateless container. It serves the frontend design for review on any browser, including a phone. It does not connect to the Oasis database, order API, reservation API, email sender, or administrative membership. It stays noindex. It neither changes the production Oasis container nor Abdul's development container.

## Release identity

| Item | Value |
| --- | --- |
| Source | `xsolutionsmd/oasis-kebab-house`, branch `derek-preview` |
| Build context | `preview/` only |
| Workflow | `.github/workflows/derek-preview.yml` |
| Immutable image package | `ghcr.io/xsolutionsmd/oasis-kebab-house-derek-preview` |
| Release asset | `derek-preview-<full branch SHA>/deployment.json`, prerelease |
| Container project/alias | `oasis-derek-preview` / `oasis-derek-preview` |
| Hostname | `oasis-derek.xsolutionsmd.com` |
| Internal port | `8080`, no host port |
| Installed runtime | `/opt/oasis-derek-preview` |
| Updater and state | `oasis-derek-preview-update.timer` / `/var/lib/oasis-derek-preview-deploy` |

The preview workflow checks JavaScript, source links, content, image health, revision, menu/reservation pages, and noindex headers on a push or PR to `derek-preview`. Only a push to that exact branch publishes a digest-pinned image and manifest. The root-owned server updater independently reads that branch and exact prerelease; main and `dereks-dev` are ignored. The workflow waits for the same revision over public HTTPS before reporting success. An infrastructure change to the root-owned updater or gateway needs a reviewed reinstall; ordinary frontend pushes replace only the preview image.

## Local development

From the repository root, `docker compose -f preview/compose.dev.yaml up -d` serves source-mounted edits at `http://127.0.0.1:8942/`. `docker compose -f preview/compose.dev.yaml down` stops only the local preview. Run `python preview/scripts/check_preview.py`, `node --check preview/dist/main.js`, `node --check preview/dist/motion.js`, `node --check preview/dist/menu.js`, and `node --check preview/dist/reserve.js` before pushing. A production-like check is `docker build --build-arg REVISION=<40-hex-SHA> -t oasis-derek-preview-local preview`, followed by a read-only container probe of `/healthz`, `/version.json`, `/`, and `/menu.html`.

## First server installation

Verify the hostname resolves to the Oracle address, the alias and Compose project are unused, the source package can be read anonymously, and the ARM64 image fits capacity. The gateway source belongs to the X Solutions website repository; add only `preview/deploy/oracle.caddy`'s route there and to the installed gateway after backing up its current Caddyfile. Validate and reload the current gateway without recreating it or its certificate volumes. A newly unused hostname can have its route before the first image arrives.

From a checked copy of this repository's `derek-preview` branch on the server, `sudo bash preview/server/install.sh` installs the preview's root-owned Compose template, updater, timer, and scoped automatic image-retention registration. The installer leaves a new updater timer paused; after the route is ready, enable it with `sudo systemctl enable --now oasis-derek-preview-update.timer`. The timer applies the exact published preview image. Nothing from the Flask app or its runtime secrets is copied to this container.

## Operations and recovery

Status: `sudo systemctl status oasis-derek-preview-update.timer` and `sudo journalctl -u oasis-derek-preview-update.service -n 80 --no-pager`. Applied identity: `sudo cat /var/lib/oasis-derek-preview-deploy/current.json`. Container: `sudo docker compose --project-name oasis-derek-preview --env-file /opt/oasis-derek-preview/release.env -f /opt/oasis-derek-preview/compose.yaml ps`. A manual immediate check is `sudo systemctl start oasis-derek-preview-update.service`; it follows only the current `derek-preview` branch release.

Candidate failure leaves the existing container. A handled replacement failure attempts to restore the prior Compose/image. An interrupted update leaves `/var/lib/oasis-derek-preview-deploy/transaction` and recovery files for inspection; do not discard the guard. The preview is stateless, so there is no database backup or migration path. Scoped image retention protects the running image plus two previous successful image sets; the shared proxy, certificates, and unrelated app images remain outside its cleanup scope.

No backend work should be merged into `dereks-dev` on the strength of this preview alone. After Derek approves the visual direction, implement it against the real app in `dereks-dev`, validate its existing functional flows, and keep main deployment behind its separate release gate.
