# Choosing the engine and the mathematical model

The reference implementation uses Community Edition 0.22.1, published for Python 3.11+. Match the installed release to its documentation before porting a scene. The original project's examples below were read at revision `fafa083`. ManimGL's latest tagged release at that time was 1.7.2. [CE release](https://github.com/ManimCommunity/manim/releases/tag/v0.22.1) · [CE package metadata](https://pypi.org/project/manim/0.22.1/) · [ManimGL release](https://github.com/3b1b/manim/releases/tag/v1.7.2)

| Decision | Community Edition | ManimGL |
| --- | --- | --- |
| Package and import | `manim`, e.g. `from manim import Scene` | `manimgl` distribution, `from manimlib import Scene` |
| Entry point | `python -m manim render -ql lesson.py MyScene` | `manimgl lesson.py MyScene`, with GL's own flags |
| Trace an outline | `Create(curve)` | Original examples use `ShowCreation(curve)` |
| Math typesetting | `MathTex` for math, `Tex` for text-mode LaTeX | GL examples use `Tex` for math and `TexText` for text |
| Camera | Cairo 2D framing uses `MovingCameraScene.camera.frame`. Use the methods on `ThreeDScene` for 3D | The original examples animate the scene's `self.frame`. Follow the pinned GL implementation |

CE also offers an OpenGL renderer. Selecting it keeps CE's imports and CLI. When porting, translate the model, coordinate mapping, object identities and timing into the target edition. Re-render a representative shot before porting the rest. [CE installation FAQ](https://docs.manim.community/en/stable/faq/installation.html) · [CE example source](https://github.com/ManimCommunity/manim/blob/v0.22.1/example_scenes/basic.py) · [Original engine and examples](https://github.com/3b1b/manim/blob/fafa083a4fb274bba9cabde0b6e2f50ba6da0622/example_scenes.py)

## Scene and geometry

`Scene.construct` owns the timeline. `add` establishes a state, `play` changes it, and `wait` gives the viewer time to resolve it. `Mobject` holds geometry and children. `VMobject` supplies vector paths, curves, fill and stroke. Use `VGroup` for vector objects and `Group` when including objects such as raster images. A closed polygon needs an explicit return to its first point when constructed with `set_points_as_corners`. Keep mathematical values separate from display sizes. [CE building blocks](https://docs.manim.community/en/stable/tutorials/building_blocks.html) · [Vector geometry](https://github.com/ManimCommunity/manim/blob/v0.22.1/manim/mobject/types/vectorized_mobject.py)

## Choose a representation

| Topic | CE implementation | Accuracy check |
| --- | --- | --- |
| Graph of a function | Use `Axes.plot(f, x_range=...)` and `axes.c2p(x, f(x))` for attached marks. Split branches at a pole. | Check units and a known intercept. Unequal axis scales change a line's screen angle. |
| Derivative | Move a second sample with `ValueTracker` and `axes.get_secant_slope_group(x, graph, dx=h)`. End with a separate analytic tangent through the point. | Keep `h` nonzero during the quotient. Test both sides where the derivative might fail to exist. |
| Integral | Use `axes.get_riemann_rectangles(graph, x_range=[a,b], dx=...)` for estimates and `axes.get_area(graph, x_range=[a,b])` for the region. | Name the sample rule and compare an actual sum to a known integral. Shading alone does not encode the sign of an integral crossing zero. |
| Vector field / flow | `ArrowVectorField(F)` samples arrows. `StreamLines(F)` traces trajectories. State whether displayed lengths have been normalized or compressed. | Check a known equilibrium and the sign of the velocity there or nearby. A particle step and a field arrow represent different quantities. |
| Linear maps / matrices | Use `NumberPlane` and `LinearTransformationScene.apply_matrix(A)` for a linear map. `Matrix` displays coefficients. Anchor basis vectors to the same origin as the plane. | Check both matrix columns as images of the basis, the origin, and the determinant for oriented area. For a nonlinear warp, use `prepare_for_nonlinear_transform()` before deforming a plane. |
| Euclidean geometry | Compute vertices once in math space, then map each vertex. Use solid edges for the moving piece and a dashed reference contour. | Preserve distances during rigid motions and use equal physical scales on both axes for angles or circles. Check degenerate endpoints. |
| Probability / statistics | `BarChart` accepts values and `change_bar_values` changes them. Use a fixed domain and y-range across comparisons. Use an explicit seeded generator for a simulation. | Distinguish sample frequency from probability. Probabilities sum to one. For unequal histogram bins, **area** carries mass when height is density. |
| Graph algorithms | Build `Graph` or `DiGraph` with an explicit layout dictionary. Keep stable vertex IDs, then animate edges from an independently computed traversal. | Confirm predecessor edges, tie order, disconnected components and direction. A BFS layer advances by one edge in an unweighted graph. |
| Dynamic equations | Isolate semantically meaningful arguments to `MathTex` before `TransformMatchingTex`. Use `DecimalNumber.set_value` for changing numeric values. | Check sign, units and displayed precision. Keep denominators nonzero throughout the illustrated domain. |

The coordinate-system source contains the calculus examples and signatures. The individual field, geometry, statistical and graph implementations document their sampling and layout semantics. [Coordinate systems](https://github.com/ManimCommunity/manim/blob/v0.22.1/manim/mobject/graphing/coordinate_systems.py) · [Fields](https://github.com/ManimCommunity/manim/blob/v0.22.1/manim/mobject/vector_field.py) · [Linear maps](https://github.com/ManimCommunity/manim/blob/v0.22.1/manim/scene/vector_space_scene.py) · [Bar charts](https://github.com/ManimCommunity/manim/blob/v0.22.1/manim/mobject/graphing/probability.py) · [Graphs](https://github.com/ManimCommunity/manim/blob/v0.22.1/manim/mobject/graph.py)

## Before committing to a shot

For a parabola `f(x)=x²` at `x=1`, the exact forward secant slope is `2+h`. At `h=1, 0.1, −0.1` expect `3, 2.1, 1.9`. Draw the tangent with mathematical points `(1,1)` and `(2,3)` through `c2p`. For a matrix with rows `[2,1]` and `[0,1]`, the second basis vector ends at `(1,1)` and the unit square doubles its area. Use concrete checks like these before tuning the animation.
