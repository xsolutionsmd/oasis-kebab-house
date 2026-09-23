# Validation

Verified September 20, 2026.

- Container: 16 passing tests cover public pages, server-owned prices, idempotency, CSRF/origin checks, options/availability, lead times/closures, overlapping table capacity, viewer write rejection, equal-admin removal and session revocation, role invitations, email-bound OAuth, independent sender identity, outbox/status transitions, persistent records and a consistent database/key backup restore.
- Updater: 18 isolated fault scenarios exercise the actual Bash updater with synthetic Docker/HTTP commands and real archives, including candidate rejection, replacement/TLS/state failures, interrupted transactions and failed recovery. These are fault simulations, not failures injected into the shared production host.
- App Launchpad: container test/runtime builds, health, OCI source label and exact revision verified. Runtime image excludes test files, browser QA pages and git history. Graft query returned relevant backend, frontend and tests; adapter suite passed 11 tests with one Windows-only skip.
- Browser: actual local menu-to-cart-to-checkout receipt and table request completed using synthetic contacts. Google sign-in completed locally and over production HTTPS. Admin People and Emails controls inspected. Desktop home/gallery/visit and mobile home/menu/gallery/reservation layouts inspected; mobile controls fit their cards without horizontal overflow.
- Real Instagram plov footage decodes at 720 x 990, loops muted, and supports pause. Reduced-motion users receive the genuine video poster with a play control. Food/place imagery is real photography; provenance is in MEDIA_SOURCES.json.
- First production release: main c6af4fbe1566ab6c287965c8764dd0f7070a8daa, PR #1; Oracle workflow 35538458939 passed and exact HTTPS revision matched. Shared server sibling container IDs remained unchanged. DNS/TLS resolve at https://oasis.xsolutionsmd.com.

Limits: this is a prospect demo with test requests, not a restaurant operating launch. Menu/prices, hours, capacity and tax require restaurant confirmation. Gmail sending has not been connected or delivered externally; messages remain previews. Sender OAuth separation is covered by tests; a real Gmail grant and delivery test are still needed. Reticle was not requested and was not used. Rollback fault tests do not simulate sudden host power loss; interrupted recovery remains fail-closed for operator inspection.

## Tikkaville redesign and employee permissions â€” September 20, 2026

The later user correction supersedes read-only Viewer behavior above: Viewers are employees and may update order/table status and customer update messages. Membership, invitation, menu/settings and sender mutations remain admin-only. Added tests verify successful employee transitions, guest receipt updates, audit/outbox creation, unauthenticated rejection, stale-transition rejection and administrative boundaries. All public page links exclude /admin; direct /admin still redirects successfully to the authenticated workspace.

18 container tests passed. Production image test/runtime build, isolated health/source/revision passed. Both JavaScript files pass node --check. Browser search -> Manti required filling -> quantity2 -> cart -> checkout -> quantity3 preserved name/contact/date; local synthetic order receipt correctly shows3 Beef Manti/$42, pay in store. No external message was sent.

Desktop homepage/menu/item dialog/checkout/gallery/visit and 390px mobile homepage/menu/checkout/reservation inspected. Mobile page widths375/375; all checkout/reservation fields fit their cards. Fixed a floated legend that initially pushed a required option beyond the item dialog; corrected dialog scrollWidth equals clientWidth640. Heading fonts are self-hosted. New plov dish image is a genuine8-second frame from the existing source video. No generated photos, competitor media or fabricated business details were shipped. The reference and Stitch evidence are recorded in DESIGN.md.

Current changes use the existing unchanged stateful updater; no new infrastructure or migration. Live release evidence is maintained in the private client deployment record after the normal checked PR/main release completes.

## Derek frontend preview — September 23 reservation/navigation refinement

The independent derek-preview branch now includes the reservation design, shorter copy, corrected section navigation and removal of visible preview notices at Derek’s request. Local browser and static evidence, reference decisions and frontend-only constraints are in [RESERVATION_DESIGN.md](../preview/docs/RESERVATION_DESIGN.md). These checks concern the separate static preview, not the Flask backend or its production release.
