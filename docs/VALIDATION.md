# Validation

In progress, September 20, 2026. Do not treat preparation as a deployed release.

Local container: 15 passing Flask tests cover all page responses, server-owned prices, order idempotency, CSRF/origin and unauthenticated access, required modifiers/unavailability, closed service/lead bounds, overlapping reservation capacity, viewer write rejection, equal-admin removal of the original admin and immediate session revocation, invite roles/revocation, email-bound OAuth invite acceptance, separate sender/login identities, delivery preview and status transitions, invalid OAuth state and persistent records across app recreation.

The first run exposed a reservation SQL placeholder mismatch; corrected and all 15 passed. Browser review and production deployment evidence will be added after verification.
