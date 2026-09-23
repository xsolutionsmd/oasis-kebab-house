# Oasis Derek Dev

Frontend-only design preview for Oasis Uzbek Kebab House. The homepage and menu use the restaurant's original media and published dish names; ordering and reservations are intentionally disconnected.

- Local: `docker compose -f preview/compose.dev.yaml up -d`, then open `http://127.0.0.1:8942/`.
- Review: [design decisions](docs/DESIGN_REVIEW.md).
- Deployment: [independent Oracle pipeline](docs/DEPLOYMENT.md).

The existing Flask app, `dereks-dev`, production `main`, and Abdul's preview remain separate. This branch releases only the stateless design container at `oasis-derek.xsolutionsmd.com`.
