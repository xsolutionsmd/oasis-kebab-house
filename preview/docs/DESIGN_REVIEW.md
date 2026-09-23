# Oasis Derek Dev — visual and motion decisions

This is a frontend design preview for Derek to review before integrating the design into the Flask ordering and reservation application. It uses the original Oasis identity, published dish names, authentic restaurant photography and plov footage, and the approved light homepage/menu journey. It does not receive requests or claim that preview interactions place orders.

## Cohesive visual language

| Detail | Decision | Why it belongs |
| --- | --- | --- |
| Surface | Warm ivory, white, deep ceramic blue, small antique-brass accents | Carries the real logo colors and the warmth of the dining room without turning the site into a generic dark luxury theme. |
| Type | Newsreader display, DM Sans body, Oswald for small labels | The expressive serif gives the photography space and scale; the familiar Oswald keeps continuity with the approved site; the sans face protects menu readability. |
| Corners | Architectural sections; 4px controls/framed photos, 6px icon buttons, 10px dialogs | Preserves the carved-screen/editorial character while softening surfaces people touch. Full-bleed section edges remain square; pills would weaken the composition. |
| Composition | Wide film, asymmetric photo placement, generous space, fine rules | Creates an editorial rhythm while keeping the menu itself compact and easy to scan. |
| Cultural detail | A small geometric line motif and actual interior photos | The original space carries the cultural identity. Decorative stock patterns, invented architecture, and visual clichés would weaken it. |
| CTAs | Strong blue/ivory rectangles and understated text links | The primary route remains clear. Every arrow shown as an action belongs to a working link or button. |

## Motion and advanced frontend techniques reviewed one by one

| Technique | Decision | Benefit or cost |
| --- | --- | --- |
| Original plov film in hero | Use, with a visible pause control and a static poster for reduced motion | Genuine craft adds atmosphere; controlled playback avoids an exhausting or inaccessible loop. |
| Layered hero entrance | Use a measured stagger across location, headline, description, and actions | Gives the first frame a composed reveal without making visitors wait to act. |
| Photo reveal on scroll | Use an early, once-only 600ms opacity/20px transform reveal | Replaces the expensive 1.35-second clip mask. Direct navigation reveals its destination in advance so the visitor never waits for content after arriving. |
| Asymmetric card staggering | Use only for wide screens | Adds art direction. The phone layout returns to a direct, single-column reading order. |
| Hover movement | Use restrained image scale, arrow shift, underline growth, and a small button lift | Gives responsive feedback without making controls jump away from a pointer. Keyboard focus remains visible. |
| Cross-page transitions | Use progressive same-origin view transitions where supported | Softens Home-to-Menu navigation. Unsupported browsers keep ordinary links. |
| Mobile menu choreography | Reversible 520ms panel entrance, 360ms retraction, lightly staggered links | The sheet stays opaque and travels beneath the header. Rapid taps reverse from the current position; focus and scroll lock last through closing. |
| Scroll progress line | Use a hairline at the top of the viewport | Quietly communicates depth in the long editorial homepage. |
| Deep scroll parallax | Leave out | The vertical source video and modest-resolution photographs lose clarity under aggressive movement; text and images need to stay aligned. |
| Scroll hijacking or pinned full-screen chapters | Leave out | It interferes with navigation, browser history, accessibility, and quick access to menu/address. |
| WebGL/3D scenes or animated shaders | Leave out | Adds load, thermal cost, and a synthetic visual layer that competes with real restaurant photography. |
| Magnetic buttons or cursor followers | Leave out | They make small targets harder to predict and feel more like a technology demo than hospitality. |
| Draggable galleries or carousels | Leave out | A static image grid and click-to-expand are clearer on touch and keyboard; dragging offers no content advantage here. |
| Autoplay animations in menu rows | Leave out | The 72 published dishes need scanning speed and stable positions. Search and category changes are immediate. |
| Reduced-motion mode | Required | No travel, page transitions, autoplay or delayed entrances. Menus/dialogs use a short opacity-only fade, with immediate section navigation. |

The preview is deliberately noindex and static. Prices, availability, and operating rules remain outside it until the restaurant confirms them. The pending integration will map approved visuals to existing Flask pages without changing production data or enabling transactions from this preview.

The September 23 motion refinement, research, exact timings, implementation and browser checks are documented in [MOTION_IMPLEMENTATION.md](MOTION_IMPLEMENTATION.md).
