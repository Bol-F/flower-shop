---
name: manim-master
description: Design, code, render, and critique educational math or algorithm animations with Manim. Use for visual proofs, narrated lessons, scene debugging, and editable slide companions to an animation.
---

# Manim Master

Invoke `$manim-master` with a concept, audience and target length, or describe a visual proof, mathematical animation or lesson to trigger the skill. [Codex skill discovery](https://developers.openai.com/codex/skills/)

Start with the question a viewer should be able to answer by the final frame. Choose one diagram whose movement can reveal the answer.

## Build the explanation

1. **Establish the engine.** Inspect imports, project dependencies and `python -m manim --version`. Default to Manim Community Edition with Cairo. The example targets CE 0.22.1. For an existing ManimGL project, keep its environment and consult its matching source before choosing methods. Keep each scene entirely within one engine. [API and edition guide](references/manim-api.md)
2. **Write the mathematical claim.** State the domain, units, hypotheses, invariant, and equality or boundary case. Work a numerical example independently of the drawing code. Decide which quantities are exact, sampled, or rounded.
3. **Storyboard the motion.** For each beat record the viewer's question, starting image, action, invariant, spoken cue or silent caption, duration, and ending image. Carry a recognizable object or location across the cut. For a 10–20 minute video, complete the chapter board and scratch narration before rendering individual chapters. [Storyboards, narration and assembly](references/storytelling.md)
4. **Choose a visual grammar.** Assign a color and a second cue to each quantity. Block out the diagram, equation and captions in a 16:9 frame. Preview the longest expression and the extreme positions first. Give a title its place alongside the first piece of mathematical evidence. [Composition and palettes](references/visual-design.md)
5. **Animate the reasoning.** Use one mathematical state to drive geometry, numbers and labels. Use a rigid motion for a dissection, a tracker for a changing parameter, and token matching for a rearranged equation. Hold reference axes or a witness point steady. Reserve fades for entrances, exits and changes of context. [Motion choices and working patterns](references/animation-patterns.md)
6. **Control render cost.** Build static objects once. Update existing points or positions for frequent changes. Rebuild only small derived shapes, precompute layouts and samples, and retire updaters at the end of the beat. Preview the most expensive shot before producing a full lesson.

For work that spans video, slides or print, choose tools by what the audience needs to view and what the recipient needs to edit. Verify access and export one representative object with the chosen toolchain. Preserve source data, editable slide objects and asset credits through handoff. [Professional tools, slide production and worked example](references/professional-workflow.md)

## Render and inspect

For the bundled example, run these commands from the skill's directory with the Python environment containing Manim. For an existing project, stay in its usual render working directory and call the validator by its full path. This preserves relative image, font and narration paths.

```sh
python scripts/validate_scene.py examples/advanced_animation.py EqualPerimeter
python scripts/validate_scene.py examples/advanced_animation.py EqualPerimeter --render --at 5.4 --at 14.5 --at 26.3 --at 36
```

The first command checks source without executing it. The second executes the scene, decodes a newly rendered low-quality MP4 and writes a timestamped contact sheet. Open the sheet, examine detailed frames at their native size, and check motion around cuts. Use the delivery frame rate for the final timing check. [Validator scope and render diagnostics](references/troubleshooting.md)

The [original example](examples/advanced_animation.py) takes a rectangle apart and carries the missing square into its equation. It runs without a TeX installation. Use it as a reference for object continuity, a rigid pivot, and the transition from one numerical case to a proof.

## Release check

- Can a viewer predict a change from the diagram before reading its formula? Replace text-only beats with visible evidence where possible.
- Do the diagram and equation agree at the start, midpoint, extrema, and final state? Check the equality case explicitly.
- Does every motion identify a change, a correspondence, or a cause? Remove ornamental moves, interchangeable slide fades, and holds longer than the reading or reasoning needs.
- At phone size, are subscripts, units and labels legible? Are intentional overlaps distinguishable? Check the midpoint of a turn or zoom as well as its ends.
- Do the spoken cue, visual emphasis, and subtitle agree in time? For multiple scenes, review the assembled transitions and the audio tail.
- Report the engine/version, the exact outputs inspected and any remaining limits. Distinguish a source check, a decoded movie, and a human-readable visual review.
