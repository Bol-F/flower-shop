"""Build the editable teaching deck for EqualPerimeter and an optional SVG chart."""

import argparse
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile

import av
from PIL import Image
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_TICK_MARK
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls, qn
from pptx.util import Inches, Pt

from perimeter_palette import (
    BLUSH,
    CHARCOAL,
    CORAL,
    CREAM,
    GOLD,
    HONEY,
    INK,
    JADE,
    MINT,
    OCEAN,
    OCHRE,
    PAPER,
    QUIET,
    RUST,
    SLATE,
    TEAL,
    WHEAT,
)

WIDTH, HEIGHT = 40 / 3, 7.5
MARGIN = 0.78
DISPLAY, BODY = 'Georgia', 'Segoe UI'
TRADES = (0, 1, 2, 3)
LOSSES = tuple(t * t for t in TRADES)


def rgb(color):
    return RGBColor.from_string(color.removeprefix('#'))


def write_text(shape, text, size, color, family, align, bold):
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.auto_size = MSO_AUTO_SIZE.NONE
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    frame.text = text
    for paragraph in frame.paragraphs:
        paragraph.alignment = align
        paragraph.line_spacing = 1.05
        paragraph.space_before = paragraph.space_after = Pt(0)
        paragraph.font.name = family
        paragraph.font.size = Pt(size)
        paragraph.font.bold = bold
        paragraph.font.color.rgb = rgb(color)
    return shape


def label(
    slide, text, x, y, w, h, size, color=CHARCOAL, *, family=BODY, align=PP_ALIGN.LEFT, bold=False
):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    shape.name = text.replace('\n', ' ')
    return write_text(shape, text, size, color, family, align, bold)


def page(deck, title, notes, *, dark=False, title_box=None, title_size=39):
    slide = deck.slides.add_slide(deck.slide_layouts.get_by_name('Title Only'))
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = rgb(PAPER if dark else CREAM)
    heading = slide.shapes.title
    x, y, w, h = title_box or (MARGIN, 0.4, WIDTH - 2 * MARGIN, 0.92)
    heading.left, heading.top, heading.width, heading.height = map(Inches, (x, y, w, h))
    write_text(heading, title, title_size, INK if dark else CHARCOAL, DISPLAY, PP_ALIGN.LEFT, False)
    slide.notes_slide.notes_text_frame.text = notes
    return slide


def rect(shapes, name, x, y, w, h, fill, edge, *, dashed=False):
    shape = shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.name = name
    shape.shadow.inherit = False
    if fill is None:
        shape.fill.background()
    else:
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(fill)
    shape.line.color.rgb = rgb(edge)
    shape.line.width = Pt(1.55)
    if dashed:
        shape.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    return shape


def rule(shapes, x1, y1, x2, y2, color, weight=1):
    mark = shapes.add_connector(MSO_CONNECTOR.STRAIGHT, *map(Inches, (x1, y1, x2, y2)))
    mark.shadow.inherit = False
    mark.line.color.rgb = rgb(color)
    mark.line.width = Pt(weight)
    return mark


def measure(slide, symbol, x, y, width, *, above=False):
    tick = 0.085 if above else -0.085
    color = RUST if above else SLATE
    for end in (x, x + width):
        rule(slide.shapes, end, y, end, y + tick, color)
    rule(slide.shapes, x, y, x + width, y, color)
    label(
        slide,
        symbol,
        x + width / 2 - 0.33,
        y - 0.43 if above else y + 0.04,
        0.66,
        0.36,
        19,
        color,
        family=DISPLAY,
        align=PP_ALIGN.CENTER,
    )


def tiled_region(slide, name, x, y, cols, rows, unit, fill, edge):
    # Group editable pieces so a presenter can move a whole region or one individual tile.
    region = slide.shapes.add_group_shape()
    region.name = name
    for row in range(rows):
        for col in range(cols):
            rect(
                region.shapes,
                f'{name}, row {row + 1}, column {col + 1}',
                x + unit * col,
                y + unit * row,
                unit,
                unit,
                fill,
                edge,
            )
    return region


def predict(deck):
    slide = page(
        deck,
        'Which rectangle\nhas more area?',
        'Give the audience time to predict. Four plus four and five plus three '
        'both equal eight, so both perimeters are sixteen. The diagrams use the same scale.',
        title_box=(MARGIN, 1.72, 5.35, 2.15),
        title_size=47,
    )
    label(slide, 'Perimeter held at 16 units', MARGIN, 1.10, 5, 0.45, 20, TEAL)
    label(
        slide, 'One side gains a unit.\nThe other gives one up.', MARGIN, 4.05, 5.1, 1.36, 23, SLATE
    )
    unit, baseline = 0.59, 4.66
    for x, width, height in [(6.20, 4, 4), (9.32, 5, 3)]:
        rect(
            slide.shapes,
            f'{width} by {height} rectangle',
            x,
            baseline - height * unit,
            width * unit,
            height * unit,
            MINT,
            TEAL,
        )
        label(
            slide,
            f'{width} × {height}',
            x,
            baseline + 0.22,
            width * unit,
            0.55,
            26,
            family=DISPLAY,
            align=PP_ALIGN.CENTER,
        )


def dissect(deck):
    slide = page(
        deck,
        'A quarter turn reveals the missing square',
        'On the left are twelve base tiles and an extra column of three. Rotate the '
        'gold column through ninety degrees, then translate it left. The fifteen tiles '
        'are congruent to the pieces on the right. The outlined corner contains no tile.',
        dark=True,
        title_size=37,
    )
    unit, top = 0.73, 2.06
    x1, x2 = 1.45, 8.10
    for x in (x1, x2):
        rect(
            slide.shapes,
            'Original four-by-four outline',
            x,
            top,
            4 * unit,
            4 * unit,
            None,
            QUIET,
            dashed=True,
        )
        tiled_region(slide, 'Twelve base tiles', x, top + unit, 4, 3, unit, OCEAN, JADE)
    tiled_region(slide, 'Movable column', x1 + 4 * unit, top + unit, 1, 3, unit, HONEY, GOLD)
    tiled_region(slide, 'Column after the turn', x2 + unit, top, 3, 1, unit, HONEY, GOLD)
    rect(slide.shapes, 'One empty unit square', x2, top, unit, unit, None, CORAL, dashed=True)
    arrow = slide.shapes.add_shape(
        MSO_SHAPE.RIGHT_ARROW, Inches(6.12), Inches(3.41), Inches(0.78), Inches(0.30)
    )
    arrow.name = 'Turn and slide the column'
    arrow.shadow.inherit = False
    arrow.fill.solid()
    arrow.fill.fore_color.rgb = rgb(GOLD)
    arrow.line.fill.background()
    label(slide, '5 × 3 rectangle', x1, 5.33, 4.4, 0.57, 28, INK, family=DISPLAY)
    label(slide, '15 unit tiles', x1, 6.02, 4.0, 0.59, 20, QUIET)
    label(slide, '4 × 4 outline', x2, 5.33, 4.35, 0.57, 28, INK, family=DISPLAY)
    label(slide, 'The same 15 tiles leave one space.', x2, 6.02, 4.54, 0.59, 19, QUIET)


def generalize(deck):
    slide = page(
        deck,
        'The missing corner has area t²',
        'For positive sides w and h, set m = (w+h)/2 and t = |w−h|/2. Then 0 ≤ t < m. '
        'Keeping perimeter fixed keeps m fixed because P = 4m. Rearrangement leaves '
        'one t-by-t square empty. Equality occurs exactly when t = 0.',
    )
    x, y, side, gap = 1.58, 2.32, 3.34, 1.05
    rect(slide.shapes, 'Unchanged base region', x, y + gap, side, side - gap, MINT, TEAL)
    rect(slide.shapes, 'Repositioned strip', x + gap, y, side - gap, gap, WHEAT, OCHRE)
    rect(slide.shapes, 'Area missing from the square', x, y, gap, gap, BLUSH, RUST, dashed=True)
    label(slide, 't²', x, y, gap, gap, 31, RUST, family=DISPLAY, align=PP_ALIGN.CENTER)
    measure(slide, 't', x, y - 0.16, gap, above=True)
    measure(slide, 'm', x, y + side + 0.18, side)
    label(slide, 'Side lengths', 6.24, 1.82, 5.8, 0.39, 17, SLATE)
    label(slide, 'm + t  and  m − t', 6.24, 2.27, 6.05, 0.76, 34, family=DISPLAY)
    label(slide, 'Their perimeter stays at 4m.', 6.24, 3.11, 6.05, 0.46, 21)
    rule(slide.shapes, 6.24, 3.94, 12.24, 3.94, '#B8C6BD')
    equation = label(slide, 'A = m² − ', 6.24, 4.22, 6.10, 0.76, 38, family=DISPLAY)
    term = equation.text_frame.paragraphs[0].add_run()
    term.text = 't²'
    term.font.color.rgb = rgb(RUST)
    label(
        slide,
        'Equal sides make t zero.\nThe rectangle then fills the square.',
        6.24,
        5.33,
        6.08,
        1.14,
        22,
        SLATE,
    )


def chart_axis(axis, title):
    axis.has_title = True
    axis.axis_title.text_frame.text = title
    title_font = axis.axis_title.text_frame.paragraphs[0].font
    title_font.name, title_font.size = BODY, Pt(15)
    title_font.bold = False
    title_font.color.rgb = rgb(SLATE)
    axis.tick_labels.font.name = BODY
    axis.tick_labels.font.size = Pt(14)
    axis.tick_labels.font.color.rgb = rgb(CHARCOAL)
    axis.major_tick_mark = XL_TICK_MARK.NONE
    axis.format.line.color.rgb = rgb(SLATE)


def compare_losses(deck):
    slide = page(
        deck,
        'Doubling the trade quadruples the lost area',
        'Compare t = 1 and t = 2 on the chart. With m = 4, a 5-by-3 rectangle loses '
        'one unit of area. A 6-by-2 rectangle loses four. Values shown are exact samples '
        'of t squared. The relationship also holds for non-integer side lengths.',
        title_size=36,
    )
    label(slide, 'Perimeter held at 16 units', MARGIN, 2.03, 4.75, 0.38, 18, TEAL)
    label(slide, '6 × 2', MARGIN, 2.54, 4.5, 1.02, 56, family=DISPLAY)
    label(
        slide,
        'Trade two units and the rectangle covers 12 of the original 16 square units.',
        MARGIN,
        3.94,
        4.45,
        1.70,
        23,
    )
    values = CategoryChartData()
    values.categories = [str(t) for t in TRADES]
    values.add_series('Missing area', LOSSES)
    graph = slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED,
        Inches(5.56),
        Inches(1.67),
        Inches(6.97),
        Inches(5.09),
        values,
    )
    graph.name = 'Editable chart of missing area by length traded'
    graph.element.xpath('./p:nvGraphicFramePr/p:cNvPr')[0].set(
        'descr', 'Trading 0, 1, 2, or 3 units loses 0, 1, 4, or 9 square units, respectively.'
    )
    chart = graph.chart
    chart.font.name = BODY
    chart.has_legend = chart.has_title = False
    # The python-pptx column template writes signed IDs. DrawingML axes use unsigned IDs.
    # Renumber both declarations and cross-references so stricter readers can open the chart.
    axis_ids = {}
    for axis_ref in chart._chartSpace.xpath('.//c:axId | .//c:crossAx'):
        original = axis_ref.get('val')
        axis_ref.set('val', axis_ids.setdefault(original, str(len(axis_ids) + 1)))
    # The library exposes styling for axes and series. Set the outer chart canvas transparent.
    chart._chartSpace.chart.addnext(
        parse_xml(f'<c:spPr {nsdecls("c", "a")}><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr>')
    )
    chart_axis(chart.category_axis, 'Length traded, t (units)')
    chart_axis(chart.value_axis, 'Missing area (square units)')
    chart.value_axis.minimum_scale, chart.value_axis.maximum_scale = 0, 10
    chart.value_axis.major_unit = 2
    chart.value_axis.has_major_gridlines = True
    chart.value_axis.major_gridlines.format.line.color.rgb = rgb('#D6DBD0')
    plot = chart.plots[0]
    plot.gap_width = 85
    plot.has_data_labels = True
    labels = plot.data_labels
    labels.show_value = True
    labels.position = XL_LABEL_POSITION.OUTSIDE_END
    labels.font.name, labels.font.size = BODY, Pt(15)
    labels.font.color.rgb = rgb(CHARCOAL)
    series = chart.series[0]
    series.format.fill.solid()
    series.format.fill.fore_color.rgb = rgb(RUST)
    series.format.line.fill.background()


def read_movie(movie):
    with av.open(str(movie)) as container:
        if not container.streams.video:
            raise ValueError('The source movie needs a video stream.')
        stream = container.streams.video[0]
        if (
            stream.codec_context.name != 'h264'
            or abs(stream.width / stream.height - WIDTH / HEIGHT) > 0.01
        ):
            raise ValueError('Supply the 16:9 H.264 MP4 of EqualPerimeter.')
        if stream.duration is None or stream.duration <= 0:
            raise ValueError('The MP4 needs a video duration for timed slide playback.')
        duration_ms = round(stream.duration * stream.time_base * 1000)
        target = round(0.40 * stream.duration)
        container.seek(target, stream=stream)
        for frame in container.decode(stream):
            if frame.pts is not None and frame.pts < target:
                continue
            pixels = frame.to_image()
            pixels.thumbnail((1280, 720), Image.Resampling.LANCZOS)
            image = BytesIO()
            pixels.save(image, format='PNG')
            image.seek(0)
            return image, duration_ms
    raise ValueError('The source movie has no decodable poster frame.')


def play_on_entry(slide, video, duration_ms):
    # PowerPoint uses a main-sequence media command to start the separate video timing node.
    # This slide is constructed with one movie. The library created timing IDs 1 and 2.
    (media_node,) = slide.element.xpath('.//p:video')
    media_node.addprevious(
        parse_xml(f"""
        <p:seq {nsdecls('p')} concurrent="1" nextAc="seek">
          <p:cTn id="3" dur="indefinite" nodeType="mainSeq"><p:childTnLst><p:par>
            <p:cTn id="4" fill="hold"><p:stCondLst>
              <p:cond delay="indefinite"/>
              <p:cond evt="onBegin" delay="0"><p:tn val="3"/></p:cond>
            </p:stCondLst><p:childTnLst><p:par>
              <p:cTn id="5" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst>
                <p:childTnLst><p:par>
                  <p:cTn id="6" presetID="1" presetClass="mediacall" presetSubtype="0"
                         fill="hold" nodeType="withEffect">
                    <p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>
                      <p:cmd type="call" cmd="playFrom(0.0)"><p:cBhvr>
                        <p:cTn id="7" dur="1" fill="hold"/>
                        <p:tgtEl><p:spTgt spid="{video.shape_id}"/></p:tgtEl>
                      </p:cBhvr></p:cmd>
                    </p:childTnLst>
                  </p:cTn>
                </p:par></p:childTnLst>
              </p:cTn>
            </p:par></p:childTnLst></p:cTn>
          </p:par></p:childTnLst></p:cTn>
          <p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>
          <p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>
        </p:seq>""")
    )
    # Retain media click controls without an empty external hyperlink relationship.
    (click,) = video.element.xpath('./p:nvPicPr/p:cNvPr/a:hlinkClick')
    click.attrib.pop(qn('r:id'), None)
    (timing,) = slide.element.xpath('./p:timing')
    timing.addprevious(parse_xml(f'<p:transition {nsdecls("p")} advTm="{duration_ms + 300}"/>'))


def replay(deck, movie):
    slide = page(
        deck,
        'Where does the area go?',
        'The silent film starts on entry in PowerPoint. Watch the outer column rotate '
        'as a rigid piece, then trace the labelled empty corner into the area equation.',
        dark=True,
    )
    # The movie contains the visible title. Keep the native title beneath it for the slide outline.
    poster, duration_ms = read_movie(movie)
    video = slide.shapes.add_movie(
        str(movie),
        0,
        0,
        deck.slide_width,
        deck.slide_height,
        poster_frame_image=poster,
        mime_type='video/mp4',
    )
    video.name = 'EqualPerimeter geometric proof'
    video.element.xpath('./p:nvPicPr/p:cNvPr')[0].set(
        'descr',
        'A 5 by 3 rectangle rearranges inside a 4 by 4 square. The missing corner '
        'has side t and area t squared. It disappears when the two sides are equal.',
    )
    play_on_entry(slide, video, duration_ms)


def vector_chart():
    import matplotlib as mpl
    from matplotlib.figure import Figure

    with mpl.rc_context(
        {
            'font.family': [BODY, 'DejaVu Sans'],
            'svg.fonttype': 'none',
            'svg.hashsalt': 'equal-perimeter',
            'font.size': 13,
        }
    ):
        fig = Figure(figsize=(7.8, 4.75), facecolor=CREAM, layout='constrained')
        fig.get_layout_engine().set(w_pad=0.20, h_pad=0.18)
        axes = fig.subplots()
        axes.set_facecolor(CREAM)
        bars = axes.bar(TRADES, LOSSES, width=0.54, color=RUST)
        axes.bar_label(bars, padding=4, color=CHARCOAL)
        axes.set(
            xlabel='Length traded, t (units)',
            ylabel='Missing area (square units)',
            xticks=TRADES,
            ylim=(0, 10.1),
        )
        axes.set_title(
            'Area lost from a square of side 4',
            loc='left',
            fontfamily=[DISPLAY, 'DejaVu Serif'],
            fontsize=18,
            color=CHARCOAL,
            pad=11,
        )
        axes.set_axisbelow(True)
        axes.grid(axis='y', color='#D6DBD0')
        axes.spines[['top', 'right']].set_visible(False)
        for spine in axes.spines.values():
            spine.set_color(SLATE)
        axes.tick_params(length=0, colors=CHARCOAL)
        axes.xaxis.label.set_color(SLATE)
        axes.yaxis.label.set_color(SLATE)
        buffer = BytesIO()
        fig.savefig(
            buffer,
            format='svg',
            metadata={
                'Title': 'Area lost from a square of side 4',
                'Description': 'Length trades of 0, 1, 2, and 3 units lose 0, 1, 4, and 9 square units.',
                'Date': None,
            },
        )
        # Matplotlib adds trailing spaces to multiline path coordinates in its SVG output.
        return b'\n'.join(line.rstrip() for line in buffer.getvalue().splitlines()) + b'\n'


def publish_file(destination, content):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
        temp = Path(stream.name)
    try:
        temp.write_bytes(content)
        temp.replace(destination)
    finally:
        temp.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('movie', type=Path, help='Rendered EqualPerimeter H.264 MP4')
    parser.add_argument('output', type=Path, help='Destination .pptx file')
    parser.add_argument(
        '--chart-svg', type=Path, metavar='FILE', help='Also export the chart as SVG'
    )
    args = parser.parse_args()
    if not args.movie.is_file() or args.movie.suffix.lower() != '.mp4':
        parser.error('Supply an existing .mp4 as the first argument.')
    if args.output.suffix.lower() != '.pptx' or (
        args.chart_svg and args.chart_svg.suffix.lower() != '.svg'
    ):
        parser.error('Use .pptx for the deck and .svg for the optional chart.')
    try:
        deck = Presentation()
        deck.slide_width, deck.slide_height = Inches(WIDTH), Inches(HEIGHT)
        deck.core_properties.title = 'Where does the area go?'
        deck.core_properties.author = deck.core_properties.last_modified_by = 'Manim Master'
        deck.core_properties.created = deck.core_properties.modified = datetime.now(UTC)
        deck.core_properties.subject = (
            'An editable geometric proof for rectangles with equal perimeter'
        )
        predict(deck)
        dissect(deck)
        generalize(deck)
        compare_losses(deck)
        replay(deck, args.movie)
        presentation = BytesIO()
        deck.save(presentation)
        figure = vector_chart() if args.chart_svg else None
        publish_file(args.output, presentation.getvalue())
        if args.chart_svg:
            publish_file(args.chart_svg, figure)
    except (OSError, ValueError, ImportError) as exc:
        parser.exit(1, f'Deck generation failed: {exc}\n')
    print(args.output.resolve())
    if args.chart_svg:
        print(args.chart_svg.resolve())


if __name__ == '__main__':
    main()
