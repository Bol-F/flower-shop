# Motion that carries an explanation

## Decide what survives the beat

| Viewer needs to follow | Choose | Check on the next beat |
| --- | --- | --- |
| One object changing representation | `Transform(source, target)` mutates the on-screen source | Continue using `source`. For a rigid turn use `Rotate` or `Rotating` with a pivot so intermediate distances stay fixed. |
| A new object taking the previous one's place | `ReplacementTransform(source, target)` | Continue using `target`. To keep a diagram while sending a copy to its equation, use `TransformFromCopy`. |
| Algebraic terms that exchange positions | `TransformMatchingTex(old, new)` with corresponding isolated TeX strings | Reuse the target. For repeated identical tokens, animate explicitly paired parts when their mathematical roles differ. |
| Reordered geometric silhouettes | `TransformMatchingShapes` for genuinely corresponding shapes | It matches normalized point geometry. Visually similar shapes can represent different quantities. Pair those explicitly. |
| Coupled motion | Play together or use `AnimationGroup` with `lag_ratio=0` | Derive both positions from one parameter when they must satisfy an invariant at every frame. |
| A propagating wave or traversal layer | `LaggedStart(*animations, lag_ratio=...)` | Keep the logical order. The group `run_time` rescales the whole schedule. Use a small group for each simultaneous BFS frontier. |
| Dependent events | Consecutive `play` calls, or `Succession` for already independent animation states | Construct a dependent target after its preceding transform finishes. Avoid concurrent writers to the same geometry. |

CE's matching implementation uses TeX strings or normalized shape points. Its transform classes differ in which object survives cleanup. [Matching source](https://github.com/ManimCommunity/manim/blob/v0.22.1/manim/animation/transform_matching_parts.py) · [Transforms](https://github.com/ManimCommunity/manim/blob/v0.22.1/manim/animation/transform.py) · [Composition](https://github.com/ManimCommunity/manim/blob/v0.22.1/manim/animation/composition.py)

## Couple a curve, a point and its tangent

Inside `construct`, this shows the tangent turn as its point of contact moves. `t` is the mathematical x-coordinate. The tangent direction comes from the derivative and passes through the same `c2p` mapping as the curve.

```python
from manim import Axes, Create, Dot, Line, ValueTracker, always_redraw, smooth

axes = Axes(x_range=[-2, 2, 1], y_range=[-1, 4, 1], x_length=7, y_length=4)
curve = axes.plot(lambda x: x * x, x_range=[-1.7, 1.7])
t = ValueTracker(-1.2)
point = Dot(color='#F5C574')
point.add_updater(
    lambda dot: dot.move_to(axes.c2p(t.get_value(), t.get_value() ** 2)), call_updater=True
)


def tangent():
    x = t.get_value()
    step = 0.45
    ends = [axes.c2p(x + dx, x * x + 2 * x * dx) for dx in (-step, step)]
    return Line(*ends, color='#72D6C2')


line = always_redraw(tangent)
self.add(axes, t)
self.play(Create(curve))
self.add(line, point)
self.play(t.animate.set_value(1.2), run_time=3, rate_func=smooth)
line.clear_updaters()
point.clear_updaters()
```

Use `always_redraw` for small objects whose construction is clearer than in-place mutation. For many lines use `put_start_and_end_on` on existing nondegenerate segments, or set VMobject points directly. Handle coincident endpoints explicitly. Add a tracker to the scene if its own updater advances on `dt`. For a rate specified per second, multiply by `dt`. Pre-create equations and update just their moving parts. [Tracker](https://docs.manim.community/en/stable/reference/manim.mobject.value_tracker.ValueTracker.html) · [Updater implementation](https://github.com/ManimCommunity/manim/blob/v0.22.1/manim/animation/updaters/mobject_update_utils.py)

## Algebra that stays attached to the diagram

Give a geometric quantity and its symbol the same visual cue. For a commutativity demonstration, use `MathTex("u", "+", "v")` and `MathTex("v", "+", "u")`, apply the same colors to `u` and `v` in both, then call `self.play(TransformMatchingTex(old, new))`. Multiple arguments or `substrings_to_isolate` establish the match. Keep complete TeX groups compilable when splitting fractions or radicals. Check both equations individually first. Use a short arc or explicitly separated paths if two terms cross and become unreadable. [Text and formulas](https://docs.manim.community/en/stable/guides/using_text.html)

## A custom animation when parameter speed matters

This animation samples x uniformly when given `rate_func=linear`. This distinction matters in a lesson about speed along a graph. It also handles skipped frames and seeks because the pose is computed from absolute progress.

```python
from manim import Animation


class PlotWalk(Animation):
    def __init__(self, dot, axes, function, interval, **kwargs):
        self.axes = axes
        self.function = function
        self.start_x, self.end_x = interval
        super().__init__(dot, **kwargs)

    def interpolate_mobject(self, alpha):
        progress = self.rate_func(alpha)
        x = self.start_x + (self.end_x - self.start_x) * progress
        self.mobject.move_to(self.axes.c2p(x, self.function(x)))
```

Overriding `interpolate_mobject` takes over easing in CE. Apply `rate_func` once. For a deformation, compute geometry from `starting_mobject` or immutable model coordinates each frame. Check `alpha=0, 0.5, 1` and an intermediate sample where smooth easing differs from linear. Use `smooth` to arrive and settle, `linear` for elapsed time or constant parameter speed, and `there_and_back` when returning to the initial state is part of the explanation. [Animation lifecycle](https://github.com/ManimCommunity/manim/blob/v0.22.1/manim/animation/animation.py) · [Built-in rigid rotation](https://github.com/ManimCommunity/manim/blob/v0.22.1/manim/animation/rotation.py)

## Camera and cut

For a 2D detail, use `MovingCameraScene` with Cairo. Save `self.camera.frame.save_state()`, frame the detail with `self.camera.frame.animate.scale(0.7).move_to(detail)`, then `Restore(self.camera.frame)`. A moving target can drive the frame with a named updater. Remove that updater before restoring. Keep one landmark in both views and inspect the full motion envelope. A fixed camera makes a conservation proof easier to judge.

For depth, use `ThreeDScene.set_camera_orientation` for the opening view and `move_camera` for the transition. Angles are radians, so expressions such as `65 * DEGREES` communicate intent. Use `add_fixed_in_frame_mobjects` for a screen caption. Start an ambient rotation only for the interval over which parallax reveals geometry, then call `stop_ambient_camera_rotation()`. At a scene boundary, recreate the same anchor, palette, and camera pose in the next scene's opening frame. [Camera gallery](https://docs.manim.community/en/stable/examples.html#special-camera-settings) · [3D camera API](https://docs.manim.community/en/stable/reference/manim.scene.three_d_scene.ThreeDScene.html)
