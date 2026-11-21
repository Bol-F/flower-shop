# From a mathematical question to a finished lesson

## Study the explanatory decision

In *The Essence of Calculus*, the question of measuring a circle motivates cutting it into measurable parts. A viewer has a reason to want the next approximation. In *Linear Transformations and Matrices*, following two basis vectors through a changing grid gives the matrix columns a visible job. Both lessons keep a familiar object on screen while changing what it means. In a new lesson, choose a different construction, script, palette and staging. Draw all assets or use assets with suitable rights. [Calculus lesson](https://www.3blue1brown.com/lessons/essence-of-calculus/) · [Linear transformations lesson](https://www.3blue1brown.com/lessons/linear-transformations/)

In the bundled rectangle proof the witness is a three-tile strip. A rigid turn makes each tile traceable. The empty corner motivates subtraction. The corner's dimension mark and its matching equation term then carry the example into the general case. The final frame answers the opening question by closing that corner.

## Board at the right scale

| Length | Plan | Completion test |
| --- | --- | --- |
| 30–90 seconds | One question, one construction, one generalization or answer. Draft 3–6 beats and time them aloud or with silent captions. | Someone watching muted can point to the evidence for the answer. |
| 3–7 minutes | Establish a concrete case, let the viewer predict a change, vary one parameter, derive the rule, and test a second case. Give each major change its own section. | Each section's exit image makes the next section's opening question natural. |
| 10–20 minutes | Complete a chapter-by-chapter storyboard, scratch narration, shot timings and ordered render list first. Reuse components, model functions, fonts, camera poses, and color roles. Budget time for a new example and an intentional recap. | The assembled cut sustains the argument across transitions and has enough reading time with the recorded voice. |

Each shot needs an entry image, the viewer's question, the invariant, the action that supplies evidence, the cue words or caption, a duration and an exit image. Mark a transition with the actual shared object and screen position. A beat that only displays a sentence is a good candidate for a diagram, counterexample, or deletion.

## Worked 12-minute board

**Why does the mean minimize squared distance?** Assume finitely many real measurements with equal weight and at least one observation. Write `μ` for their arithmetic mean. The table is a chapter board. Break each chapter into timed shots before production.

| Time | Entry image and question | Motion, narration cue and invariant | Exit to next chapter |
| --- | --- | --- | --- |
| 0:00–1:10 | Dots at 0, 2 and 7. Where should a shared marker sit? | Drag one teal marker. Grow a square from each distance as the voice says “each miss contributes its square.” The data dots stay still. | Three squares under one number line. |
| 1:10–3:00 | Can the middle data point win? | Park the marker at 2, then at 3. Keep the squares matched to the data. Show the cost dropping from `4+0+25=29` to `9+1+16=26`. | A point at `c=3` on a running cost curve. |
| 3:00–5:00 | Why is 3 special? | Draw signed deviations from 3 with direction arrows. Cue “left pays back right” as `−3−1+4=0`. Keep all three data points in place. | The signed arrows sum to zero. |
| 5:00–7:30 | What does a shift `d` cost? | Shift the candidate from `μ` to `μ+d`. Expand one square and carry its terms into a sum. Pair the cross terms using the zero sum. | Reveal `S(μ+d)=S(μ)+n d²` with `n>0`. |
| 7:30–9:30 | Does the identity predict new totals? | Move to `c=5` and predict an increase of `3·2²=12` before displaying `25+9+4=38`. Keep the old cost marked on the curve. | The vertical difference is linked to the same `n d²`. |
| 9:30–11:10 | What if two observations coincide? | Move one data dot onto another and recompute the mean from the new data. Show multiplicity with stacked marks. | Two coincident observations still contribute twice. |
| 11:10–12:00 | Where is the minimum? | Return to the opening marker. Set `d=0` and let the extra square collapse. Cue “any other position adds a positive cost.” | A clean final frame with the minimum and its equality condition. |

Time the voice against visible events. For a three-second turn, a cue might put “turn” at departure, “same three tiles” while the seams remain visible, and “one square short” after the piece lands. Read aloud and adjust the move or the wording. Give the viewer a prediction hold before the reveal. Place subtitles in a reserved band and avoid speaking a new idea over an unrelated camera move.

## Organize a long production

Keep a pure `model.py` for the math, `style.py` for named roles and text styles, `components.py` for reusable graphical objects, and small scene modules under `scenes/`. Maintain an ordered shot list with scene class, narration cue, audio take and expected duration. Store scratch audio, final audio and generated media separately. Set resolution, renderer, frame rate and fonts consistently across shots. Render from the same working directory when resolving project assets.

Use `self.next_section("The shift")` at a meaningful beat. With `--save_sections`, CE writes section movies and an index alongside the scene output. Use independent scene modules when chapters should render independently. Choose either section clips or whole-scene clips for a particular span. [CE sections and output](https://docs.manim.community/en/stable/tutorials/output_and_config.html) · [CE voiceover guide](https://docs.manim.community/en/stable/guides/add_voiceovers.html)

```sh
python -m manim render -qh --fps 30 --save_sections scenes/mean.py MeanCost
ffprobe -v error -show_streams chapter01.mp4
```

Arrange compatible silent chapters in narrative order. Put the following `order.ffconcat` file next to the clips.

```text
ffconcat version 1.0
file chapter01.mp4
file chapter02.mp4
```

```sh
ffmpeg -f concat -safe 1 -i order.ffconcat -c copy lesson.mp4
ffmpeg -i lesson.mp4 -i narration.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac lesson-narrated.mp4
```

For stream copy, verify matching streams, codec, dimensions, pixel format and time base. Normalize mismatched clips to the same encoding first. For one continuous voice track, line it up against the **assembled** movie, check spoken cues at the beginning, a join and the end, and trim or pad deliberately. If the shots contain their own audio, include the intended audio streams throughout the assembly. Check total duration, dropped or duplicated transition frames, subtitle clearance and the last audible word. [FFmpeg concat demuxer](https://ffmpeg.org/ffmpeg-formats.html#concat)
