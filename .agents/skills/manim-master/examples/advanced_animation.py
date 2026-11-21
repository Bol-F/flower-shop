"""An original silent visual proof. Render with Manim Community Edition and Cairo."""

import numpy as np
from manim import (
    LEFT,
    PI,
    RIGHT,
    Create,
    DashedVMobject,
    DecimalNumber,
    Dot,
    FadeIn,
    FadeOut,
    LaggedStart,
    Line,
    Polygon,
    Rotating,
    Scene,
    Text,
    TransformFromCopy,
    ValueTracker,
    VGroup,
    VMobject,
    always_redraw,
    smooth,
)

from perimeter_palette import CLAY, CORAL, GOLD, HONEY, INK, JADE, OCEAN, PAPER, QUIET

M = 4.0
UNIT = 0.92
PANEL_X = 1.25


def point(x, y):
    """Map mathematical lengths to the screen with equal scale on both axes."""
    return np.array([-5.85 + UNIT * x, -1.83 + UNIT * y, 0.0])


def corners(x, y, width, height):
    return [point(x, y), point(x + width, y), point(x + width, y + height), point(x, y + height)]


def tile(x, y, width, height, fill, edge):
    return Polygon(
        *corners(x, y, width, height),
        fill_color=fill,
        fill_opacity=1,
        stroke_color=edge,
        stroke_width=2.5,
    )


def reshape(mob, x, y, width, height):
    vertices = corners(x, y, width, height)
    mob.set_points_as_corners([*vertices, vertices[0]])
    # A collapsed rectangle otherwise leaves a bright stroke on the boundary.
    mob.set_opacity(float(min(width, height) > 1e-7))
    return mob


def lettering(words, size, color=INK, *, serif=False):
    return Text(
        words,
        font='serif' if serif else 'sans-serif',
        font_size=size,
        color=color,
        warn_missing_font=False,
    )


def at_left(mob, x, y):
    return mob.move_to([x, y, 0], aligned_edge=LEFT)


def caption(words):
    return at_left(lettering(words, 30), -6.30, -3.22)


def measure(length, y, tick, color):
    return VMobject(stroke_color=color, stroke_width=2).set_points_as_corners(
        [point(0, y + tick), point(0, y), point(length, y), point(length, y + tick)]
    )


def live_number(value, anchor, size):
    """Rebuild Pango digits only when the displayed tenth actually changes."""
    number = DecimalNumber(value(), mob_class=Text, num_decimal_places=1, font_size=size, color=INK)

    def update(mob):
        rounded = round(value(), 1)
        if rounded != mob.get_value():
            mob.set_value(rounded)
        mob.move_to(anchor(), aligned_edge=LEFT)

    number.add_updater(update, call_updater=True)
    return number


class EqualPerimeter(Scene):
    """Dissect a 5-by-3 rectangle, then vary the general dissection continuously."""

    def construct(self):
        self.camera.background_color = PAPER
        offset = ValueTracker(0)
        self.add(offset)
        t = offset.get_value
        title = at_left(lettering('Where does the area go?', 54, serif=True), -6.30, 3.05)
        fixed = at_left(lettering('FIXED PERIMETER', 23, QUIET), PANEL_X, 1.68)
        perimeter = at_left(lettering('16 units', 45, serif=True), PANEL_X, 0.98)
        area_label = at_left(lettering('AREA  /  SQUARE UNITS', 23, QUIET), PANEL_X, -0.12)
        area = live_number(lambda: (M + t()) * (M - t()), lambda: [PANEL_X, -0.85, 0], 46)
        rectangle = tile(0, 0, M, M, OCEAN, JADE)
        rectangle.add_updater(lambda mob: reshape(mob, 0, 0, M + t(), M - t()))
        width = live_number(lambda: M + t(), lambda: point((M + t()) / 2 - 0.25, -0.48), 29)
        height = live_number(lambda: M - t(), lambda: point(-0.89, (M - t()) / 2), 29)
        guide = DashedVMobject(
            tile(0, 0, M, M, PAPER, QUIET).set_fill(opacity=0), num_dashes=56, dashed_ratio=0.55
        )

        self.next_section('The trade')
        self.add(title, fixed, perimeter, area_label, area)
        cue = caption('Give the width what you take from the height.')
        self.play(
            LaggedStart(FadeIn(rectangle), FadeIn(width), FadeIn(height), lag_ratio=0.18),
            FadeIn(cue),
            run_time=1.5,
        )
        self.play(Create(guide), run_time=1.0)
        self.play(offset.animate.set_value(1), run_time=3.7, rate_func=smooth)
        self.wait(1.4)
        next_cue = caption('Can these fifteen squares fill the original frame?')
        self.play(FadeOut(cue), run_time=0.9)
        self.play(FadeIn(next_cue), run_time=0.45)

        self.next_section('The dissection')
        base = tile(0, 0, M, M - 1, OCEAN, JADE)
        strip = tile(M, 0, 1, M - 1, HONEY, GOLD)
        cuts = VGroup(
            *(Line(point(M, k), point(M + 1, k), color=GOLD, stroke_width=2) for k in (1, 2))
        )
        grid = VGroup(
            *(Line(point(k, 0), point(k, 3), color=JADE, stroke_width=1.2) for k in (1, 2, 3)),
            *(Line(point(0, k), point(4, k), color=JADE, stroke_width=1.2) for k in (1, 2)),
        )
        rectangle.clear_updaters()
        self.add(base)
        self.play(
            FadeIn(strip),
            LaggedStart(*(Create(line) for line in [*grid, *cuts]), lag_ratio=0.12),
            run_time=1.7,
        )
        self.remove(rectangle)
        self.wait(1.3)
        self.play(FadeOut(width), FadeOut(height), FadeOut(next_cue), run_time=0.5)
        cue = caption('Turn the extra column and slide it into the frame.')
        hinge = Dot(point(M, M - 1), radius=0.065, color=INK)
        piece = VGroup(strip, cuts)
        self.add(piece)
        self.play(FadeIn(cue), FadeIn(hinge), run_time=0.5)
        self.play(
            Rotating(piece, angle=PI / 2, about_point=point(M, M - 1), rate_func=smooth),
            run_time=2.9,
        )
        self.play(piece.animate.shift((M - 1) * UNIT * LEFT), FadeOut(hinge), run_time=2.2)
        gap = tile(0, M - 1, 1, 1, CLAY, CORAL)
        self.play(FadeIn(gap), FadeOut(cue), run_time=0.7)
        cue = caption('The missing area is one small square.')
        self.play(FadeIn(cue), run_time=0.5)
        self.wait(2.0)

        self.next_section('The general case')
        side_label = at_left(lettering('ORIGINAL SIDE LENGTHS', 23, QUIET), PANEL_X, 1.68)
        sides = at_left(lettering('m + t,   m − t', 41, serif=True), PANEL_X, 0.92)
        area_title = at_left(lettering('RECTANGLE AREA', 23, QUIET), PANEL_X, -0.12)
        formula = at_left(lettering('A = m²', 45, serif=True), PANEL_X, -0.88)
        minus = lettering('−', 45, serif=True).next_to(formula, RIGHT, buff=0.16)
        penalty = lettering('t²', 45, CORAL, serif=True).next_to(minus, RIGHT, buff=0.16)
        gap_name = lettering('t²', 37, INK, serif=True).move_to(point(0.5, M - 0.5))
        square_side = VGroup(
            measure(M, -0.23, 0.11, QUIET),
            lettering('m', 31, QUIET, serif=True).move_to(point(M / 2, -0.58)),
        )
        gap_side = always_redraw(lambda: measure(t(), M + 0.17, -0.09, CORAL))
        side_t = lettering('t', 30, CORAL, serif=True)
        side_t.add_updater(lambda mob: mob.move_to(point(t() / 2, M + 0.45)), call_updater=True)
        area.clear_updaters()
        self.play(
            FadeOut(VGroup(fixed, perimeter, area_label, area, cue, cuts, grid)), run_time=0.65
        )
        cue = caption('Keep m fixed. The missing square has side t.')
        self.play(
            FadeIn(side_label),
            FadeIn(sides),
            FadeIn(cue),
            FadeIn(gap_name),
            FadeIn(square_side),
            FadeIn(gap_side),
            FadeIn(side_t),
            run_time=1.0,
        )
        self.wait(1.6)
        self.play(
            FadeIn(area_title),
            FadeIn(formula),
            FadeIn(minus),
            TransformFromCopy(gap_name, penalty),
            run_time=1.6,
        )
        self.wait(1.5)

        # The three regions exactly partition an m-by-m square for every 0 <= t < m.
        self.remove(piece)
        self.add(strip, gap_name)
        base.add_updater(lambda mob: reshape(mob, 0, 0, M, M - t()))
        strip.add_updater(lambda mob: reshape(mob, t(), M - t(), M - t(), t()))
        gap.add_updater(lambda mob: reshape(mob, 0, M - t(), t(), t()))
        gap_name.add_updater(lambda mob: mob.move_to(point(t() / 2, M - t() / 2)))
        self.play(offset.animate.set_value(1.65), run_time=2.45)
        self.play(
            FadeOut(gap_name), FadeOut(gap_side), FadeOut(side_t), FadeOut(cue), run_time=0.55
        )
        cue = caption('Equal sides close the gap and give the greatest area.')
        self.play(FadeIn(cue), run_time=0.6)
        self.play(offset.animate.set_value(0), run_time=3.1)
        equality = at_left(lettering('m,   m', 41, serif=True), PANEL_X, 0.92)
        self.play(FadeOut(penalty), FadeOut(minus), FadeOut(sides), run_time=0.45)
        self.play(FadeIn(equality), run_time=0.55)
        self.wait(2.0)
