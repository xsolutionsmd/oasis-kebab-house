# Validation

Verified September 20, 2026.

- Container: 16 passing tests cover public pages, server-owned prices, idempotency, CSRF/origin checks, options/availability, lead times/closures, overlapping table capacity, viewer write rejection, equal-admin removal and session revocation, role invitations, email-bound OAuth, independent sender identity, outbox/status transitions, persistent records and a consistent database/key backup restore.
- Updater: 18 isolated fault scenarios exercise the actual Bash updater with synthetic Docker/HTTP commands and real archives, including candidate rejection, replacement/TLS/state failures, interrupted transactions and failed recovery. These are fault simulations, not failures injected into the shared production host.
- App Launchpad: container test/runtime builds, health, OCI source label and exact revision verified. Runtime image excludes test files, browser QA pages and git history. Graft query returned relevant backend, frontend and tests; adapter suite passed 11 tests with one Windows-only skip.
- Browser: actual local menu-to-cart-to-checkout receipt and table request completed using synthetic contacts. Google sign-in completed locally and over production HTTPS. Admin People and Emails controls inspected. Desktop home/gallery/visit and mobile home/menu/gallery/reservation layouts inspected; mobile controls fit their cards without horizontal overflow.
- Real Instagram plov footage decodes at 720 x 990, loops muted, and supports pause. Reduced-motion users receive the genuine video poster with a play control. Food/place imagery is real photography; provenance is in MEDIA_SOURCES.json.
- First production release: main c6af4fbe1566ab6c287965c8764dd0f7070a8daa, PR #1; Oracle workflow 35538458939 passed and exact HTTPS revision matched. Shared server sibling container IDs remained unchanged. DNS/TLS resolve at https://oasis.xsolutionsmd.com.

Limits: this is a prospect demo with test requests, not a restaurant operating launch. Menu/prices, hours, capacity and tax require restaurant confirmation. Gmail sending has not been connected or delivered externally; messages remain previews. Sender OAuth separation is covered by tests; a real Gmail grant and delivery test are still needed. Reticle was not requested and was not used. Rollback fault tests do not simulate sudden host power loss; interrupted recovery remains fail-closed for operator inspection.

## Tikkaville redesign and employee permissions — September 20, 2026

The later user correction supersedes read-only Viewer behavior above: Viewers are employees and may update order/table status and customer update messages. Membership, invitation, menu/settings and sender mutations remain admin-only. Added tests verify successful employee transitions, guest receipt updates, audit/outbox creation, unauthenticated rejection, stale-transition rejection and administrative boundaries. All public page links exclude /admin; direct /admin still redirects successfully to the authenticated workspace.

18 container tests passed. Production image test/runtime build, isolated health/source/revision passed. Both JavaScript files pass node --check. Browser search -> Manti required filling -> quantity2 -> cart -> checkout -> quantity3 preserved name/contact/date; local synthetic order receipt correctly shows3 Beef Manti/$42, pay in store. No external message was sent.

Desktop homepage/menu/item dialog/checkout/gallery/visit and 390px mobile homepage/menu/checkout/reservation inspected. Mobile page widths375/375; all checkout/reservation fields fit their cards. Fixed a floated legend that initially pushed a required option beyond the item dialog; corrected dialog scrollWidth equals clientWidth640. Heading fonts are self-hosted. New plov dish image is a genuine8-second frame from the existing source video. No generated photos, competitor media or fabricated business details were shipped. The reference and Stitch evidence are recorded in DESIGN.md.

Current changes use the existing unchanged stateful updater; no new infrastructure or migration. Live release evidence is maintained in the private client deployment record after the normal checked PR/main release completes.


## Abdul's isolated Oracle preview — September20,2026

Created abdul-dev from main9e1a31f, then installed independent updater, Compose project, data/keys, OAuth client and HTTPS route. First automatic push release6ba3ad277b665492b485765850f0085fd306f1f6 passed Application CI and preview workflow35545025111. Public HTTPS and server receipt matched. Image digest88fa436d2bc0188824de716655c33212a8539e99b8016296b8be983973dbdc8e is in the separate public preview package. Main remains9e1a31f with unchanged container; all sibling containers/gateway preserved.

18 preview updater fault scenarios pass on Linux, including first/subsequent success, absent/stale/malformed release, architecture/candidate/replacement/HTTPS/snapshot/state errors, handled termination and refused interrupted/failed recovery. Real preview Compose was exercised with isolated synthetic configuration, test network/volume and original runtime limits:256MiB,100PIDs, read-only root, non-root user. Recreating its container retained data. Rehearsal resources were removed without touching existing volumes.

Clean second clone on abdul-dev started via shared launcher at localhost8793 with its own persistent volume. Real Google sign-in succeeded at the new HTTPS /admin. Both partners have separate preview admin membership; production memberships and sender connections were untouched. One synthetic $18 plov order was created and accepted through the preview UI, with email unconnected. Session/encryption keys differ from main, and preview began with zero customer requests or sender secrets. Public package visibility and prerelease/main-latest separation were inspected. No external email sent.

The follow-up handoff/branch-guidance commit is also used to verify a subsequent automatic update and synthetic-data persistence. Final exact live receipt and backup evidence are maintained in the private client deployment record. Power-loss recovery and Abdul's own interactive Google login are not claimed; his configured account is ready to sign in.


## Classic redesign on abdul-dev — September 30, 2026

Local evidence only (cloud session; Docker unavailable, so `scripts/app.py check` and the production-image check were not run here — CI on push runs them). 18 app tests pass with pytest against Flask directly; 18 preview updater scenarios pass (`scripts/test_updater.py --abdul-dev`); `node --check` passes for site.js and admin.js.

Playwright/Chromium against a local server with synthetic data, at 1440×900 and 390×844: menu → one-tap add (Tandoori Samsa, Samarkand Plov) → Manti dialog rejects submit without a filling → Pumpkin ×2 → order drawer/bottom bar → checkout (empty-name error shown, today full so the next open day was auto-selected, earliest time preselected) → order placed → status page with progress tracker. Reservation: remembered details prefilled, 4 guests, time chip, request placed → status page. No page errors or console errors. No horizontal overflow on home, menu, checkout, reserve, visit, gallery or privacy at 320, 390, 768, 1024, 1280 and 1440px. Staff workspace login page renders with the new tokens. No external email or real order was sent. Reticle was not requested and not used. Live preview verification happens through the Abdul dev preview workflow after push.

Follow-up (same day): hero rebuilt to show the complete plov video without cropping over a blurred live canvas backdrop; added colour bands and tile pattern. Re-ran the same Playwright order/reservation flows at 1440 and 390px (no page/console errors), the overflow sweep at 320–1280px (none) and the 18 app tests (pass). Instagram, Yelp and oasiskebabhouse.com were blocked by this session's network policy, so no new media was collected. Yelp photos are customer uploads covered by Yelp's terms and were deliberately not used.

Container evidence (cloud session, Docker 29.3.1, revision 99afe3d): the repository Dockerfile's `test` and `production` targets were built. The only change was a temporary out-of-repo copy that trusts the sandbox proxy certificate for pip; the committed Dockerfile is unchanged. The test stage ran the pytest suite during the build. The production image, run read-only with tmpfs /data as in the preview workflow, became healthy, reported the exact revision in /version.json, and served /, /menu, the new stylesheet, fonts and the 5.2 MB video. The runtime image contains no tests. The same Playwright pickup-order and reservation flows passed against the container at 1440 and 390px. Live preview evidence still depends on the PR merge and the Abdul dev preview workflow.

Simplification pass (after PR #4 merged): removed the blurred canvas backdrop and repeated hours/status/address blocks. Playwright order and reservation flows at 1440 and 390px, the overflow sweep at 320–1280px and the 18 app tests pass locally. Instagram, Yelp, oasiskebabhouse.com and reference restaurant sites remained blocked by the session network policy.

Essentials-only pass: removed decorative/story sections and duplicate navigation. Same Playwright flows (1440/390px), overflow sweep and 18 app tests pass locally. Yelp remained blocked by the session network policy, so no Yelp photos were added.
