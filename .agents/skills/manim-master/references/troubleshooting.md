# Rendering and diagnosing a scene

## Establish a working environment

Use the animation project's environment or make a separate one. For the bundled example, Python 3.12 and `manim==0.22.1` are a reproducible starting point. With the intended virtual environment active:

```sh
python -m pip install "manim==0.22.1"
python -m manim --version
python -m manim checkhealth
python -m manim render --help
```

Cairo and Pango provide the drawing and text backends. Follow the platform installation guide if native dependencies cannot build. CE 0.22.1 uses PyAV to write movies. The external FFmpeg CLI is useful for extraction, inspection and chapter assembly. `Text` needs a Pango-visible font. Default `MathTex` also needs a working LaTeX toolchain, including the `standalone` class, AMS packages and `dvisvgm`. [Official installation](https://docs.manim.community/en/stable/installation/uv.html) · [CE movie writer](https://github.com/ManimCommunity/manim/blob/v0.22.1/manim/scene/scene_file_writer.py)

## What each check measures

The commands below assume the bundled self-contained example and the skill directory. For another project, invoke the [validator](../scripts/validate_scene.py) by its full path from the project's usual render directory. A scene using `ImageMobject('plot.png')` can fail to locate its asset if you only supply an absolute scene path and change working directory. Static mode uses only the Python standard library. It compiles the source without running it, flags direct ManimGL imports in the supplied file, and checks that the named class is declared there. Rendering exercises inheritance, imports and drawing behavior.

```sh
python scripts/validate_scene.py examples/advanced_animation.py EqualPerimeter --render
python scripts/validate_scene.py examples/advanced_animation.py EqualPerimeter --render --output-dir previews --at 14.5 --at 19 --at 26.3
```

Render mode runs the named scene as Python code using the current interpreter's CE CLI and Cairo. It creates a unique run directory, expects CE's normal scene filename beneath its media directory, decodes every frame, and writes a timestamped PNG contact sheet. By default it samples nine evenly spaced frames. Use `--at` for mid-motion or very brief beats. The sheet is an index for visual inspection. Readability, intentional overlaps and proof correctness require judgment.

| Need | Command | What to inspect |
| --- | --- | --- |
| Fast motion preview | `python -m manim render -ql lesson.py MyScene` | 854×480 at nominal 15 fps. Look at the widest intermediate pose. |
| Inspect a costly beat | `python -m manim render -ql -n 3,5 lesson.py MyScene` | Render the indexed animation range and then check its joins in the full movie. |
| Final composition only | `python -m manim render -s lesson.py MyScene` | Final count, caption clearance and mathematical endpoint. |
| Delivery pass | `python -m manim render -qh --fps 30 lesson.py MyScene` | 1920×1080 at the requested 30 fps. Choose a delivery rate suitable for the work. |
| Native-size detail | `ffmpeg -ss 14.5 -i movie.mp4 -frames:v 1 turn.png` | Check the pivot, stroke separation and text during motion. |

## Follow the symptom

- **Import or unknown-method error.** Print `python -c "import manim; print(manim.__version__, manim.__file__)"` from the rendering interpreter. Check for a local `manim.py` shadowing the package. Compare the exact release source when a keyword differs across editions or releases.
- **TeX fails but text renders.** Check `latex --version` and `dvisvgm --version` separately. Render a single `MathTex(r"x^2")` with `--no_latex_cleanup`, then inspect the first error in the TeX log. For example, on a minimal TeX Live install, Babel's “Unknown option 'english'” points to the `babel-english` package used by the default CE template. Check escaping and complete TeX groups when individual formulas fail. For a simple Unicode label use `Text`, or `DecimalNumber(..., mob_class=Text)` for a TeX-free readout. Keep fractions and matrices properly typeset.
- **Stale movie or wrong class.** Run the fully qualified interpreter, source path and class name into a fresh `--media_dir`. CE can select a lone available scene when a requested name cannot be found. Check the actual output name and timestamp. `--disable_caching` forces fresh partial renders.
- **Camera crop or off-screen caption.** In 2D Cairo, check coordinates relative to the current moving frame. In 3D, pin explanatory text with `add_fixed_in_frame_mobjects`. Inspect the most extreme zoom, the start and finish of a camera move, and the moving geometry halfway through.
- **Jitter, drift or a disappearing label.** Derive motion from model values and update labels from the same state. Avoid accumulating per-frame displacements during absolute-time animation. After replacement or token matching, bind later animations to the surviving object. Stop a camera-follow updater before restoring the frame.
- **Slow preview.** Time a representative shot. Moving a camera can force a large diagram to redraw. Replace per-frame TeX or layout construction with prebuilt terms, cached digits, a fixed graph layout or in-place updates. Sample at a resolution appropriate to the visible detail, then recheck at delivery quality.
- **Wrong mathematical picture.** Test the model at a negative input, a boundary, and an ordinary interior point. Check graph-to-scene units, numerical tolerances, sign, rounding, and zero-size strokes. A valid movie can still teach the wrong rule.

The entrypoint and resources use repository-local discovery and progressive loading. The canonical placement and invocation rules are documented in the [OpenAI Codex skills guide](https://developers.openai.com/codex/skills/).
