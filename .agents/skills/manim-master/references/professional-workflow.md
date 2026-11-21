# Producing a lesson across video, slides and print

Decide who will present, which facts might change, and which objects the recipient must edit. A lecturer may want to move a tile in PowerPoint, a viewer needs a film that plays offline, and a publisher may need a vector figure. Start from one mathematical model and a shared set of color and type roles. Choose the simplest toolchain that preserves each deliverable.

## Select and verify the tools

Check the local package and executable versions for the tools you select. For desktop and cloud products, verify the available account, license, target platform, fonts and export permissions using a small representative file. Export a diagram, chart or short motion sample and reopen it in the recipient's application before building a series. In the handoff, identify which tools actually produced or rendered the files.

### Presentation and illustration

| Task | Tool and decision |
| --- | --- |
| A deck someone will update in Office | Use **Microsoft PowerPoint** layouts and masters for recurring design. Keep headings, notes, data charts and simple diagrams native. Reopen the saved PPTX in the delivery version and test embedded media offline. [Slide masters](https://support.microsoft.com/en-us/powerpoint/training/what-is-a-slide-master-in-powerpoint) · [Supported media](https://support.microsoft.com/en-us/powerpoint/video-and-audio-file-formats-supported-in-powerpoint) |
| A Mac-first talk | **Apple Keynote** supports authored builds and Magic Move between slides with corresponding objects. Keep the Keynote source where it is the master. When PPTX is the handoff, inspect a converted slide containing the most important transition, equation and font. [Keynote transitions](https://support.apple.com/en-il/guide/keynote/tanff5ae749e/mac) · [PowerPoint export](https://support.apple.com/guide/keynote/export-to-powerpoint-or-another-file-format-tana0d19882a/mac) |
| Precise art direction across many frames | In **Figma**, use layout grids, components for recurring diagrams, and variables or modes for color, spacing and themes. Compare compositions side by side. For code-driven geometry the equivalent can be shared tokens, explicit coordinates and a contact sheet. Export artwork separately so slide text and chart data stay editable. [Figma variables](https://help.figma.com/hc/en-us/articles/15339657135383-Guide-to-variables-in-Figma) |
| Vector drawing and scalable diagrams | Choose **Adobe Illustrator** for an illustrator's layered artboards, **Affinity Designer** for an existing Affinity design and export slices, or **Inkscape** for an open SVG editing workflow. Keep the editable source and export with a viewBox. Inspect stroke widths, clipped groups, fonts and masks in the final renderer. [Illustrator SVG](https://helpx.adobe.com/illustrator/desktop/save-and-export/export-files-to-different-formats/save-artwork-in-svg-format.html) · [Affinity export](https://affinity.help/designer2/en-US.lproj/pages/ExportPersona/exportPersona.html) · [Inkscape](https://inkscape-manuals.readthedocs.io/en/latest/) · [SVG specification](https://www.w3.org/TR/SVG2/) |
| Photograph or texture that needs retouching | **Adobe Photoshop** supports nondestructive adjustments, masks and Smart Objects. Retain the layered original. Export a color-managed crop at the required pixel dimensions and check the point of interest after placement. [Photoshop editing techniques](https://helpx.adobe.com/photoshop/desktop/create-manage-layers/create-layer-compositions/non-destructive-editing-techniques.html) |
| Reproducible editable PowerPoint | Choose **PptxGenJS** for a JavaScript or TypeScript pipeline, especially reusable slide masters. Choose **python-pptx** for a Python model or an existing PPTX template. Both support native shapes, text and charts. Check a representative chart's embedded data and any media relationships in the exported file. [PptxGenJS masters](https://gitbrent.github.io/PptxGenJS/docs/masters/) · [python-pptx charts](https://python-pptx.readthedocs.io/en/latest/user/charts.html) · [Movie shapes](https://python-pptx.readthedocs.io/en/latest/api/shapes.html) |

### Data, technical figures and type

| Deliverable | Tool and decision |
| --- | --- |
| A custom interactive data graphic | **D3.js** gives precise control over marks, scales and interaction in a browser. For a slide export, choose the informative state and expose values that would otherwise require hovering. [D3](https://d3js.org/what-is-d3) |
| A scientific figure or exploratory chart | Use **Matplotlib** for explicit units, vector export and reproducible print layout. Use **Plotly** for interactive exploration or an HTML companion. Verify Kaleido and its compatible browser for Plotly static export. Where people need to change values in PowerPoint, build a native chart from the same rows. [Matplotlib output backends](https://matplotlib.org/stable/users/explain/figure/backends.html) · [Plotly export](https://plotly.com/python/static-image-export/) |
| A topology or process diagram | Use **Graphviz** `dot` for ranked layouts and directed dependencies. Use **Mermaid** for a versioned flowchart maintained beside technical documentation. Export SVG and inspect edge crossings, arrowheads and label bounds. Use explicit coordinates when spatial position carries mathematical meaning. [Graphviz dot](https://graphviz.org/docs/layouts/dot/) · [Mermaid CLI](https://mermaid.js.org/config/mermaidCLI.html) |
| Complex mathematics | Use **LaTeX** through CE `MathTex` for fractions, matrices and aligned expressions. Preserve the TeX source alongside vector exports. In the deck, keep simple equations as editable text or use a native equation when the recipient needs structured math editing. [LaTeX](https://www.latex-project.org/about/) · [CE text and formulas](https://docs.manim.community/en/stable/guides/using_text.html) |

Choose type for its job. A serif with distinct math glyphs can carry equations and headlines. An open sans serif can handle units, captions and small labels. Establish a small scale and a consistent baseline grid. Test the longest label, minus sign, subscript and non-Latin glyphs the lesson uses. **Google Fonts** distributes font sources with family-specific license files. Check the font's terms and availability before packaging it. Coordinate shared values such as `canvas`, `ink`, `moving piece` and `remainder` across the slide system, vector figures and film. Use direct labels, geometry or line patterns as a second cue. [Google Fonts repository](https://github.com/google/fonts) · [Design token format](https://www.designtokens.org/tr/2025.10/format/) · [Accessible use of color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html) · [Contrast and palettes](visual-design.md)

### Motion and finishing

| Motion requirement | Tool and handoff |
| --- | --- |
| The motion itself proves a mathematical claim | **Manim Community Edition** can drive geometry, labels and values from one parameter. Test the invariant during interpolation, then render a timed master and chapter clips. [CE gallery](https://docs.manim.community/en/stable/examples.html) |
| Compositing, tracking or expressive typographic motion | **Adobe After Effects** suits footage, mattes and authored keyframe timing. Keep source layers and identify the input and output frame rates. For a diagram driven by a formula, bring in the rendered geometry with the required alpha or background. [After Effects](https://www.adobe.com/products/aftereffects.html) |
| Lighting and depth carry the explanation | Use **Blender** for an actual 3D scene with a camera, materials and occlusion. Preview the informative camera angles before an expensive render. For long shots render an image sequence that can resume and then encode the result. [Blender project](https://github.com/blender/blender) · [Rendering animations](https://docs.blender.org/manual/en/latest/render/output/animation.html) |
| An interactive browser animation | **GSAP** timelines provide ordered tweens, labels and relative start times. Test user interaction and reduced-motion behavior in the browser. Supply a movie when an offline slide needs the motion. [GSAP Timeline](https://gsap.com/docs/v3/GSAP/Timeline/) |
| Video compositions driven by React | **Remotion** uses a frame number to render parameterized graphics. It fits repeated video variants from application data. Make sampling, fonts and external assets deterministic. [Remotion's rendering model](https://www.remotion.dev/docs/idea) |
| Assembly and delivery | Use **FFmpeg** to assemble matching clips, mix voice, encode H.264 MP4, normalize streams where needed, and extract a poster. Inspect timestamps, dimensions, pixel format, frame rate and audio tracks with `ffprobe`. Watch a join and the last word on the final encode. [FFmpeg documentation](https://ffmpeg.org/documentation.html) · [Assembly recipe](storytelling.md) |

### Photography and image processing

When a real person, place, specimen or event supplies evidence, source a real photograph. Record the asset URL, title, creator, rights statement, retrieval date, credit text and modifications. Check the particular asset and intended use, including attribution, visible brands and identifiable people. Keep that record in the project and place the required credit in notes, on the slide, or in the delivered credits as appropriate.

- **Unsplash** and **Pexels** are sources for editorially relevant stock photography. Read the applicable asset terms, distinguish a site's standard license from paid or externally supplied content, and check restrictions on resale and implied endorsement. [Unsplash license](https://unsplash.com/license) · [Pexels license](https://www.pexels.com/license/)
- **Wikimedia Commons** has file-specific authorship and licenses. Follow attribution and share-alike terms when applicable. In an official institutional library such as **The Met Open Access**, look for the open-access designation on the actual object record and retain its accession number or persistent identifier. [Commons reuse](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia) · [The Met Open Access](https://www.metmuseum.org/hubs/open-access)
- Use **Pillow** for orientation, crops, thumbnails and frame contact sheets. Use **OpenCV** for measurement, masks, tracking or geometric registration when those operations support the claim. Distinguish an annotated reconstruction from the original photograph. [Pillow ImageOps](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html) · [OpenCV image processing](https://docs.opencv.org/4.x/d7/dbd/group__imgproc.html)
- **ImageMagick** fits command-line batch conversion and image comparison. **Sharp** fits a Node pipeline producing many sizes from one original. Preserve the master and check orientation, transparency, color space and final crop after export. [ImageMagick](https://imagemagick.org/) · [Sharp](https://sharp.pixelplumbing.com/)

## Production and review

1. **Research and content strategy.** Record the evidence, audience, learning goal, exact numerical claim and required outputs. Give every visual a question it helps answer.
2. **Visual storyboard.** Sketch the opening question, comparison, reveal and transfer example. Write the narration cue or speaker note beside the change it explains. Mark which geometry and camera position carry across a transition.
3. **Design system.** Select the grid, type scale, semantic colors and motion timing. Try a representative dense frame and a sparse one. Check contrast on the actual fill and readability at presentation distance.
4. **Source and draw.** Record photo rights when relevant. Keep vectors, data, equations and reusable components under source control. Preserve native points and text when the audience needs to edit a diagram.
5. **Compose and generate.** Use the target's native layouts, text, shapes, notes and charts wherever practical. Fit long labels before reducing type. Embed the movie and a meaningful poster for offline PowerPoint delivery. Give each slide an identifiable title and provide a spoken or textual description of essential visuals.
6. **Render, inspect and refine.** Inspect every slide in the target renderer and the video at its delivery frame rate. Check slide joins, reading order, font fallback, unintended overlaps, data values, media playback and editability. Repair the source, re-export, and inspect the changed result.
7. **Deliver.** Provide the requested deck, movie or vector file with the corresponding source and reproduction commands. State the application and version used to verify the final files and the compatibility checks still open.

## Worked handoff

The rectangle lesson packages an editable geometric dissection, a chart with its own data workbook and an embedded Manim film. The standalone SVG uses the same area values as the slide chart. The proof uses original geometry. [Deck generator](../examples/perimeter_deck.py) · [Shared colors](../examples/perimeter_palette.py)

Open the five-slide deck to move individual tiles, edit chart values or replay the dissection. The separate MP4 suits video players, and the SVG keeps chart labels editable for print. [PowerPoint lesson](../examples/output/EqualPerimeter.pptx) · [1080p film](../examples/output/EqualPerimeter.mp4) · [Vector chart](../examples/output/AreaLoss.svg)

From the skill directory, with Manim, python-pptx and Matplotlib available in the animation environment:

```sh
python -m manim render -qh --fps 30 --renderer cairo --format mp4 --media_dir media examples/advanced_animation.py EqualPerimeter
python examples/perimeter_deck.py media/videos/advanced_animation/1080p30/EqualPerimeter.mp4 EqualPerimeter.pptx --chart-svg AreaLoss.svg
```

The optional slide dependencies used for this handoff are `python-pptx==1.0.2` and `matplotlib==3.11.2`. Install them in the animation environment with `python -m pip install "python-pptx==1.0.2" "matplotlib==3.11.2"`. The poster and slide timing come from the supplied film. Check the playback by exporting the deck to video and comparing the moving dissection and final equality frame with the original. Applications can display the poster correctly while skipping the animation.

Two interoperability details matter when adapting the example. PowerPoint uses a media command in the slide's animation sequence to start playback on entry. A timed export also needs enough time to show the film. For native charts, keep axis identifiers unsigned and update their cross-references together. A chart can draw correctly in PowerPoint while a second reader rejects its identifiers. [PowerPoint media playback](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.playsettings.playonentry) · [DrawingML axis identifiers](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.drawing.charts.axisid?view=openxml-3.0.1)
