# Design: Oasis — classic editorial redesign

September 30, 2026 (abdul-dev). Brief from the owner: more professional and classy, a balanced and restrained palette rather than colorful, fewer words, more intuitive ordering, every image and the hero video looking intentional. This supersedes the Tikkaville visual treatment below; ordering, reservation, sender and membership behavior are unchanged on the server.

- **Reference direction.** Inspo/Stitch were not available in this cloud session and the restaurant's own site (oasiskebabhouse.com) was blocked by the network policy, so the fallback was a public-web direction: editorial restaurant sites in the vein of Dishoom — ivory ground, a serif display face, generous whitespace and one quiet accent — combined with the proven online-ordering pattern (sticky category chips, persistent order summary, bottom order bar on phones). Menu, hours and photos come from the existing repository sources; public review sites were read for tone only. No review quotes, ratings or new claims were added. "Halal" appears on the restaurant's own entrance sign (entrance.webp) and on its menu.
- **Palette** from the logo: ivory `#faf7f1`, ink `#1c2530`, deep Samarkand blue `#1d4e6e` for primary actions, brass `#a8823f` only for eyebrows and step markers, and one dark `#152029` visit band. No gradients or decorative color blocks.
- **Type.** Self-hosted Cormorant Garamond (headings) and Inter (body/UI), OFL. Oswald removed.
- **Hero video.** The source is portrait 720×990; stretched across a landscape hero it was cropped ~2× and looked accidental. It now sits in a portrait arch frame (4:5) beside the headline — shown near native resolution, cover-cropped only slightly. Re-encoded to 560px wide (6.5 MB → 3.2 MB). Muted, loops, pause control, no autoplay under reduced motion.
- **Home:** hero (headline, one-line description, Order pickup / Reserve, live open/closed status, pickup lead time), three signature dishes with quick add, a three-step "how pickup works" strip, story section, a five-photo mosaic, dark visit band with grouped hours.
- **Ordering.** Items without options add in one tap (toast with "View order"); items with required choices open the option dialog. Rows show "N in order". Desktop keeps a sticky order summary beside the menu; tablet/phone show a bottom order bar. Drawer and summaries allow quantity changes and removal. Checkout uses day chips (only open days), preselects the earliest time and skips to the next day when today is full, numbered steps, and an optional "remember my details on this device" (browser-only storage, documented in Privacy). The place-order button shows the total.
- **Reservations:** party-size chips, day chips, time chips, then details.
- **Status page:** progress tracker (Received → Confirmed → Preparing → Ready → Collected, or Requested → Confirmed → Seated), directions/call actions, auto-refresh every 30 s until a final state.
- **Header:** logo, four links, open-now status, Order pickup and order button; phones get a slide-in navigation sheet. No public admin link.
- Accessibility: native dialogs, real radio inputs behind chips, visible brass focus rings, 16px inputs on phones, reduced motion honored.

---

# Previous design: Oasis / Tikkaville structure

September 20, 2026. The user's explicit new reference is https://tikkaville.com/menu and, clarified twice, the entire Tikkaville website including its homepage. This supersedes the previous dark framed hero/three-card structure. Existing Oasis ordering, reservation, sender and membership workflows remain.

Inspected actual desktop homepage, menu, required-option item modal and mobile menu. Borrow structure and interactions, not Tikkaville copy, photos or business claims. User-supplied exact reference takes priority over discovery of unrelated sites. Stitch project8339421717311518030, system9581014791798261260, screenffe0d791498c4c8ca6f86ac8791c3bc7 produced an editable structural draft. Downloaded HTML and screenshot were inspected in ignored .stitch/designs. Its invented facts (phone, hours, certifications, parking) were discarded. The separate system-apply update returned an invalid-argument error, but generation using the created system succeeded. No generated media is shipped.

- White/ivory surfaces, deep Uzbek tile blue #126077, brass accent, original Oasis logo. Self-hosted Oswald headings follow the reference hierarchy; plain sans body.
- Compact sticky header; menu/reservations/gallery/visit public links, More contact dropdown, pickup CTA and cart. Absolutely no public admin link. Direct /admin entry still requires authentication.
- Full-width original Instagram video hero, lower-left heading/CTA, featured dish row with quick add, alternating authentic photo/text sections, gallery, FAQ, location and footer.
- Menu has a sticky category/search rail, grouped compact two-column rows, original photo feature cards, plus buttons, required-option modal and fixed quantity/add footer. On phones, rail becomes horizontal category navigation and a sticky cart action appears when populated.
- Cart/checkout require no customer account or card. Pickup notice/slots/hours/tax/capacity continue to come from existing server settings. Confirmation/status/outbox behavior preserved.
- Gallery, visit, reservation, checkout, receipts, privacy and staff workspace share the new type/color/form system. No unsupported rewards, delivery, fabricated discounts/reviews, decorative numbers or another restaurant's artwork.
- Employee accounts retain stored role viewer for compatibility. They may update order and reservation statuses/customer notes through existing transitions; menu, service settings, members/invites and email controls stay admin-only. All admins remain equal. Sender remains independent.
- Native dialogs, visible keyboard focus, real labels, reduced motion, muted video with pause and mobile card containment remain required.
