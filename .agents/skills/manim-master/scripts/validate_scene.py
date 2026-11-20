"""Check CE scene source; optionally render a fresh preview and a labelled contact sheet."""

import argparse
import ast
import math
import subprocess
import sys
import tempfile
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def check_source(path, scene):
    source = path.read_bytes()
    tree = ast.parse(source, filename=str(path))
    compile(tree, str(path), 'exec')
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules = [node.module or '']
        else:
            continue
        if any(module.split('.')[0] in {'manimlib', 'manimgl'} for module in modules):
            raise ValueError(f'{path}:{node.lineno} imports ManimGL. Use a CE scene here.')
    if scene not in {node.name for node in tree.body if isinstance(node, ast.ClassDef)}:
        raise ValueError(f'{path} does not define a top-level class named {scene!r}.')


def render(path, scene, directory):
    print(f'Rendering with Manim Community {version("manim")} into {directory}', flush=True)
    command = [
        sys.executable,
        '-m',
        'manim',
        'render',
        '-ql',
        '--renderer',
        'cairo',
        '--format',
        'mp4',
        '--progress_bar',
        'none',
        '--disable_caching',
        '--silent',
        '--media_dir',
        str(directory),
        str(path.resolve()),
        scene,
    ]
    subprocess.run(command, check=True, stdin=subprocess.DEVNULL)
    # CE may choose another scene if an invalid name is passed. Verify the actual filename.
    movies = [
        p
        for p in directory.rglob(f'{scene}.mp4')
        if not {'partial_movie_files', 'sections'}.intersection(p.relative_to(directory).parts)
    ]
    if len(movies) != 1:
        raise ValueError(
            f'Expected one fresh {scene}.mp4 under {directory}, found {len(movies)}. '
            'Check scene inheritance and your Manim output configuration.'
        )
    return movies[0]


def make_sheet(movie, destination, times):
    import av
    from PIL import Image, ImageDraw, ImageFont

    with av.open(str(movie)) as container:
        if not container.streams.video:
            raise ValueError('The rendered file contains no video stream.')
        stream = container.streams.video[0]
        count, fps = stream.frames, stream.average_rate
        if count < 1 or not fps or fps <= 0:
            raise ValueError('The preview has no usable video frame count or frame rate.')
        duration = float(count / fps)
        if any(t >= duration for t in times):
            raise ValueError(
                f'Sample times must be before the end of the preview ({duration:.3f}s).'
            )
        if times:
            indices = sorted({min(count - 1, int(t * fps)) for t in times})
        else:
            indices = sorted({round((count - 1) * i / 8) for i in range(9)})
        slots = {index: slot for slot, index in enumerate(indices)}
        columns = min(3, len(slots))
        cell_w, cell_h = 384, 216
        sheet = Image.new(
            'RGB', (columns * cell_w, math.ceil(len(slots) / columns) * (cell_h + 25)), '#152429'
        )
        draw, font = ImageDraw.Draw(sheet), ImageFont.load_default(size=16)
        decoded = 0
        for index, frame in enumerate(container.decode(stream)):
            decoded += 1
            if index not in slots:
                continue
            x = (slots[index] % columns) * cell_w
            y = (slots[index] // columns) * (cell_h + 25)
            thumbnail = frame.to_image()
            thumbnail.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
            sheet.paste(thumbnail, (x + (cell_w - thumbnail.width) // 2, y))
            seconds = frame.time if frame.time is not None else float(index / fps)
            draw.text((x + 8, y + cell_h + 3), f'{seconds:.2f}s', font=font, fill='white')
        if decoded != count:
            raise ValueError(f'Video header reports {count} frames, but decoded {decoded}.')
        sheet.save(destination)
        print(
            f'{stream.width}x{stream.height}, {float(fps):g} fps, {decoded} frames, {duration:.2f}s'
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    parser.add_argument('scene', help='Top-level scene class in FILE')
    parser.add_argument('--render', action='store_true', help='Run the scene using Manim CE/Cairo')
    parser.add_argument(
        '--output-dir', type=Path, help='Parent of a new run directory (default: system temp)'
    )
    parser.add_argument(
        '--at',
        type=float,
        default=[],
        action='append',
        metavar='SECONDS',
        help='Sample this preview time; repeat for important transitions',
    )
    args = parser.parse_args()
    if (args.at or args.output_dir) and not args.render:
        parser.error('--at and --output-dir apply to --render')
    if len(args.at) > 24 or any(not math.isfinite(t) or t < 0 for t in args.at):
        parser.error('Supply at most 24 finite, nonnegative sample times.')
    try:
        check_source(args.file, args.scene)
        print(f'Source check passed for {args.scene}.', flush=True)
        if args.render:
            if args.output_dir:
                args.output_dir.mkdir(parents=True, exist_ok=True)
            directory = Path(
                tempfile.mkdtemp(prefix=f'{args.scene}-', dir=args.output_dir)
            ).resolve()
            movie = render(args.file, args.scene, directory)
            print(f'Preview: {movie}', flush=True)
            sheet = directory / 'contact-sheet.png'
            make_sheet(movie, sheet, args.at)
            print(f'Contact sheet: {sheet}')
    except PackageNotFoundError:
        parser.exit(1, 'Install manim in the Python environment running this script to render.\n')
    except (OSError, ValueError, SyntaxError, ImportError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'Validation failed: {exc}\n')


if __name__ == '__main__':
    main()
