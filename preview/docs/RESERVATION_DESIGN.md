# Reservation and navigation refinement — September 23, 2026

The new reserve.html page extends the accepted Oasis editorial system: actual dining-room photography, Newsreader headings, DM Sans controls, ivory and ceramic blue, restrained brass accents, 4px form corners and the shared 10px dialog. Desktop uses an asymmetric composition; mobile places the form directly after the introduction, followed by the photo and contact details. Controls have explicit labels, contained native date/time inputs, inline errors, first-invalid focus and keyboard-accessible review. No decorative numbering or invented business claims.

Stitch project 7679680410903142487, design system assets/4918558396268756600, reservation screen c1273e77ef1d4bd3be24045da74233f3. Generated HTML/image are retained in ignored .stitch/designs. Its composition informed implementation; its invented imagery, telephone, hours and large-group claims were rejected. Existing verified media and contact details were used.

Derek subsequently requested necessary words only, intentional spacing, and removal of the preview/functionality notices. These instructions supersede the earlier visible-demo-notice convention. The banner, mobile/footer notices and menu design commentary were removed from all pages. The noindex/environment separation remains. The reservation form only creates a local review: no network submission, storage or availability lookup, and no false confirmation. Without JavaScript the form remains disabled and a telephone fallback is shown.

## Reference principles

- [Aman Arva dining](https://www.aman.com/hotels/aman-tokyo/dining/arva): inspected the actual page and desktop pixels; restrained palette, real photography, fine separators and a clear reservation route inform the consistency review. Its identity, imagery and business claims were not copied.
- [Apple motion guidance](https://developer.apple.com/design/human-interface-guidelines/motion): purposeful feedback and continuity inform the existing motion system. Reservation review reuses its 380ms entrance/220ms exit; reduced motion uses 140/120ms opacity only. No new animation library.

## Section navigation

Gallery previously aligned its padded outer boundary, placing its heading about 160px farther down the screen. Mark the content wrapper with data-anchor-content, calculate its untransformed layout position, and stop 32px below the sticky header. Visit targets the address panel similarly; Our story retains its previous 20px section offset. Same-page clicks glide with the existing interruptible curve. Cross-page fragments align after load/fonts settle, unless the user has begun interacting. Do not animate or reclaim the scroll after that interaction.

The desktop Gallery height also adapts to viewport height, so a 1366x768 laptop shows heading and photos together (measured content top126px, photos bottom708px). The Visit image is absolutely contained inside its grid cell: its portrait intrinsic dimensions no longer inflate the desktop section from1266px to the intended730px. This does not alter the homepage hero or video.

## Verification

Local browser: 1440x1000 and1366x768 desktop;390x844 and320x740 phones. Every reservation input/textarea is inside its card; no horizontal page overflow or broken images. Empty submission produces field-specific errors and focuses date. Synthetic date/time/contact entries open the correct summary; Escape and Edit close it, unlock scrolling and restore Review request focus. Reduced-motion phone summary inspected with no transform and no dialog overflow. Mobile navigation exposes separate Visit/Reserve routes and returns from reservation to Gallery with its content104px below viewport top (72px header plus32px gap). Desktop Gallery, Visit, Our story, Menu and cross-page Gallery navigation inspected. Explore menu aligns its browsing rail and content125px below viewport top, and the keyboard Skip to content link preserves main-content focus at the start of the page. Browser error log empty.

Static checks: all four JavaScript files pass node --check; preview check covers all three pages, links/noindex and72 published dishes; git diff --check passes. CI now also checks reserve.js and reserve.html in candidate and live containers. CI/live evidence is recorded separately after publication.

## Video ideas — not implemented

Recommended: retain the portrait film in a narrow desktop panel, approximately one-third of the composition, with the heading and calm ivory space beside it; preserve the current mobile video framing. Alternatives: a wide authentic food photograph with a smaller portrait-film inset; or genuinely landscape restaurant footage if a suitable source is found. No alternative footage was selected or substituted. The current hero markup, styles and media are unchanged.
