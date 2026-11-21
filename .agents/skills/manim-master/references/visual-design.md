# Designing a frame people can read

## A reusable palette with mathematical roles

Use a small cast of colors across the entire lesson. These original palettes give three quantities distinct edges on both light and dark backgrounds. A label, edge style or distinctive motion provides a second cue.

| Role | Dark theme | Light theme | Second cue |
| --- | --- | --- | --- |
| Canvas | `#10252B` | `#F7F3E8` | Empty space around the construction |
| Main ink | `#F5F1E5` | `#162B31` | Title, result, primary units |
| Secondary ink | `#B9CECA` | `#445C5E` | Thin reference contour or measurement rail |
| Base quantity | `#72D6C2` | `#116C65` | Continuous outline and direct label |
| Transported piece | `#F5C574` | `#805000` | Internal cuts or moving pivot |
| Remainder | `#FFA38D` | `#9F3B37` | Dimension marks and a matching equation term |

Against their respective canvases, the five ink/edge colors have contrast ratios from 8.2:1 to 14.1:1 in dark mode and 5.6:1 to 13.3:1 in light mode. These figures are for solid colors. Check the encoded frame again over translucent fills, intersections and gradients. Choose darker/lighter fills independently of the edge color. [Relative-luminance contrast definition](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)

## Compose the extremes first

- Start with the CE 16:9 frame. A useful first layout reserves roughly 5% at each outer edge, a strip for captions, and an open lane for the diagram to move. A tall equation or a close-up may need a different layout.
- Block the start, the widest intermediate pose, and the landing. A rotated strip can extend farther sideways halfway through its turn than it does in either endpoint. Test the path against the **rendered** title, measurement labels and camera viewport.
- Put labels close to their geometry. Offset labels along a local normal or use a short leader when points converge. For two nearby roots, choose different sides of the curve and distinct marker shapes. Keep units and comparison baselines in view.
- Use one legible text family and, if useful, a contrasting title or math face. CE `Text` uses Pango. Generic serif/sans families travel well, but metrics vary by device. For precise brand rendering, use an available licensed font and verify its installed family name. `MathTex` is appropriate for stacked fractions, matrices, or nested indices. [CE text guide](https://docs.manim.community/en/stable/guides/using_text.html)
- As a starting point with CE's default logical frame, try titles around 48–56, equations around 38–48 and captions around 28–34 font units. Choose by actual pixel legibility. Watch a 480p preview at normal size and also look at a phone-width thumbnail. A thin radical, faint tick, or crowded exponent can disappear in the encode.

## Direct attention through motion

Open with the mathematical question next to an active construction. Establish the reference, move the evidence, then reveal its name. If a quantity appears on both sides of the frame, carry a copy of its symbol from diagram to equation. Let the moving part arrive before moving the camera. Keep unchanged terms spatially stable when simplifying.

White space is functional when it accommodates a sweep, separates two scales or gives a caption room. Test a muted or grayscale frame. The base, moving piece and missing region should still be identifiable through their boundaries, labels or subdivision. For a light theme, inspect the faintest line and the brightest projector view. For dark, inspect a compressed frame where neighboring dark fills can merge.

## Visual review

Inspect a settled frame, the most congested moving frame, and the final frame at native resolution. Replay fast spans around a cut. Look for an unintended glyph collision, a reference hiding under a fill, a label drifting to the wrong object, and a last-frame sliver from a collapsed polygon. In the bundled dissection, keeping the square's `m` dimension visible gives the viewer a reference while the `t` dimension grows. Hide the zero-width strokes at equality.
