# Oasis preview motion refinement — September 23, 2026

Derek approved the overall design and asked for deliberate corner styling, a gliding two-bar menu, smoother Gallery navigation and interactions, and removal of mobile emoji arrows. This is a targeted refinement of the existing Stitch-derived design, implemented directly in the static preview.

## Research and decisions

- [Apple: Motion](https://developer.apple.com/design/human-interface-guidelines/motion) recommends purposeful, brief feedback, matching entrance/exit direction, and letting people interrupt animations. These principles inform the implementation; it does not copy or claim to reproduce Apple's internal website code.
- [Google: High-performance CSS animations](https://web.dev/articles/animations-guide) recommends prioritizing transform and opacity over properties that repeatedly trigger layout/painting. Accordingly, the header no longer animates its height, the live video has no CSS filter, the overlay has no backdrop blur, and photos no longer animate a large clip mask.
- [MDN: scrollIntoView](https://developer.mozilla.org/en-US/docs/Web/API/Element/scrollIntoView) documents smooth navigation and fixed-header spacing. Native smooth-scroll timing is browser-controlled. This preview uses a small, bounded animation only for clicked in-page links so long journeys receive a deliberate duration; wheel/touch scrolling remains native.

The architectural composition keeps square full-bleed section boundaries. Buttons and framed photographs receive a barely visible 4px radius, icon controls 6px, and floating dialogs 10px. This is a design judgment for Oasis's carved screens, typography and photo composition, not a rule that luxury websites must have a particular radius.

## Exact implementation

`dist/motion.js` owns the shared interaction behavior. It loads before `main.js` and `menu.js`; there is no animation framework or extra network dependency.

| Interaction | Behavior |
| --- | --- |
| Open mobile navigation | Measure the header's bottom once, reveal a fixed clipping shell beneath it, lock background scrolling, make background controls inert, and move an opaque panel from `translateY(-100%)` to `0` over 520ms with `cubic-bezier(.22,1,.36,1)`. Links rise 18px/fade over 380ms, beginning at 70ms with 35ms stagger. |
| Close mobile navigation | Retract upward over 360ms with `cubic-bezier(.4,0,1,1)`. Keep the panel mounted and the background locked until the animation finishes, then hide the shell. Snapshot the current transform before cancelling an active animation so a rapid reversal does not reset its position. |
| Focus | Move focus without scrolling; cycle Tab within the open navigation, support Escape, and restore the toggle on dismissal. A selected section receives focus only once navigation completes. Opening a menu halfway down the page preserves that position. |
| Section links | Close the menu first. Reveal and begin loading the destination's photographs. Read the destination and header offset once, then interpolate `scrollY` using a cosine ease-in/out. Duration is `min(1600, 600 + abs(distance) * .16)` milliseconds; finish 20px beneath the constant-height header. Update the URL fragment through history, preserving ordinary link behavior for new tabs/external links. |
| Interrupt navigation | Wheel, touch, pointer or scrolling/navigation keys cancel the active animation immediately. A later anchor click starts from the actual current position. Back/Forward uses browser history; there is no wheel/touch interception or scroll-hijacking library. |
| Photo and dish dialogs | Native modal dialog/focus containment, a 380ms opacity/18px entrance with tiny scale change, and a 220ms exit. Close only after the exit finishes; restore the trigger with `preventScroll`. Gallery dimensions come from the loaded thumbnail to avoid a collapsed dialog expanding after opening. |
| Menu filtering | Preserve category button nodes, focus and horizontal rail position. Update pressed state and results without forcing a scroll to the top of the section. A brief 220ms result fade introduces the changed content. Search remains immediate. |
| Decorative work | Pause the hero video while an overlay covers it or it is offscreen. Cache document height with ResizeObserver; the scroll handler batches its progress/sticky state update into one animation frame. Reveal sections early using IntersectionObserver, with short transform/opacity entrances and no mobile stagger. |
| Icons | All static and generated directional icons use 24×24 inline SVG paths, `currentColor`, consistent strokes, and `aria-hidden`. Unicode arrow glyphs are removed from both pages and menu generation, preventing platform emoji substitution. |
| Reduced motion | Large movement is removed: navigation uses a 140ms fade, dialogs use 140ms entrance/120ms exit, anchors move immediately, and introductory animation delays are zero. Video autoplay remains disabled. No operating-system preference is changed. |

The small corner/motion tokens live in `styles.css`; menu-specific states live in `menu.css`. All affected source files are formatted for subsequent editing. The preview workflow syntax-checks all three JavaScript files before building and verifying the release image.

## Local browser verification

Verified in the in-app Chromium browser using 390×844 and 320×740 phone viewports and a 1440×1000 desktop viewport, including normal and reduced-motion emulation:

- Intermediate menu transforms were observed on opening and closing; it remains mounted until closing completes. Open/close/open rapid reversal settled correctly with working focus/inert/scroll-lock states.
- Shift+Tab from the first menu link reaches the close button; Escape restores focus and unlocks the page. A menu opened at a nonzero scroll position retained that position through dismissal.
- Gallery navigation was sampled through its journey (0, 163, 765, 1532, 2632, 3735, 4664, 5192, 5421 CSS pixels); the phone header stayed 72px tall. It settled with the section 92px from the viewport top, and all destination photos loaded. Wheel input interrupted a separate journey.
- Photo and dish dialogs animated both ways, fit the phone viewport, and restored their triggers without scrolling. Closed dish dialogs remained `display:none`, including after selecting an item with a photo.
- Searching `manti` returned three dishes. Selecting Mains returned two, kept the category focused, and preserved `scrollY` at 692.67px. At 320px, the search input remained inside its rail and the document had no horizontal overflow. No directional emoji glyphs remained in rendered text.
- No browser console errors were observed. One desktop Gallery journey recorded about 2.1ms aggregate layout work and 9.2ms JavaScript execution in Chrome's metrics. This is one local measurement, not an FPS benchmark or a guarantee for physical phones/network conditions.

Release checks and exact live revision are recorded in the client deployment evidence after publication. Only the independent `derek-preview` pipeline is used.
