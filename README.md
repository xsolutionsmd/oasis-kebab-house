# Oasis Uzbek Kebab House

A responsive Uzbek restaurant website with real restaurant photography, pickup orders paid in store, table requests and a private Google-authenticated workspace.

## Local development

Install Docker Desktop and Python 3. Run `./app.ps1 start` on Windows or `./start.sh` on Linux/macOS. Open http://127.0.0.1:8789. `./app.ps1 check` builds and tests the application; `./app.ps1 stop` stops it. See [WORKFLOW.md](WORKFLOW.md) for the dev/installed modes and immutable image updates.

Develop on `dev`; checked `main` releases publish immutable multi-architecture containers and the independent Oracle updater applies them. The live demonstration is https://oasis.xsolutionsmd.com. Noindex remains enabled, and orders/reservations are clearly marked as demonstrations until operating settings have been confirmed and `DEMO_MODE=false` is explicitly configured.

## Abdul's development preview

Work on `abdul-dev`, branched from `main`. Every push runs checks and automatically deploys only https://oasis-abdul-dev.xsolutionsmd.com. The preview has separate test data, keys, email setup, container and release history. The main Oasis site stays on `main`. See [Abdul's workflow](docs/ABDUL_DEV.md) for setup, review and promotion.

## Application

Python 3.12, Flask, SQLite WAL and a small dependency-free browser interface. One Gunicorn worker with four request threads and a serialized email outbox worker. Price calculations, item availability, pickup notice, opening hours, reservation capacity and member permissions are validated on the server. Persistent data and encryption keys live outside the image in `/data`.

The staff workspace is reached directly at `/admin`; public navigation never links to it. Admin access is by Google sign-in and invitations bound to an email address. Every admin has equal permissions, including removing the initially configured admin. Invitations support Admin and Viewer and expire after 24 hours. Removed accounts lose existing sessions immediately. Viewers act as employees: they can update customer order and reservation statuses and accompanying messages. Menu, settings, team and sender changes require an admin. An admin cannot remove their own currently signed-in account.

The outgoing Gmail connection is separate from admin membership. Connect it under **Admin → Emails**, send a test, then enable confirmations. Changing the sender never changes the signed-in identity or creates a member. When disabled, emails are saved as previews. A provider timeout is marked uncertain and never automatically retried to avoid duplicate messages. A user must grant the selected Google sending account access themselves.

Configuration: `PUBLIC_ORIGIN`, `OPERATOR_EMAIL` (initial membership only), `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `DEMO_MODE`, `DATA_DIR`. Keep credentials in an ignored local file or root-only server environment file. Register `${PUBLIC_ORIGIN}/oauth/callback` as the Google OAuth redirect. Login uses OpenID email identity; connecting the sender additionally requests `gmail.send`. See Google's [OpenID Connect guide](https://developers.google.com/identity/openid-connect/openid-connect) and [Gmail sending guide](https://developers.google.com/workspace/gmail/api/guides/sending).

## Content

The menu is transcribed from the restaurant's published April 2024 menu and must be confirmed before real trading. Photos and the cropped silent plov video come from the restaurant's Instagram. The restaurant logo is its original site asset. No food or restaurant image was generated. Full sources are in [MEDIA_SOURCES.json](docs/MEDIA_SOURCES.json). The Samarkand architecture image represents Uzbekistan, not the restaurant interior.

Read [deployment and recovery](docs/ORACLE_DEPLOYMENT.md), [design decisions](docs/DESIGN.md), and [validation](docs/VALIDATION.md) before changing the app.
