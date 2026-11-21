"""Direct local Kokoro takes, chapter timing and sample-aligned English subtitles."""

import argparse
import filecmp
import hashlib
import json
import re
import subprocess
import textwrap
from pathlib import Path

import numpy as np
import soundfile as sf

from src.measurements import ROOT

RATE = 24000
DURATIONS = (55, 55, 55, 55, 100, 50, 65, 65, 55, 45)
VOICE = 'af_heart'
# Baseline speaking rates. A new take is spoken if a chapter cannot fit its time slot.
SPEEDS = (1.04, 1.03, 1.07, 1.08, 1.04, 1.06, 1.04, 1.06, 1.07, 1.0)


def script():
    chapters = []
    for line in (ROOT / 'docs/narration.md').read_text(encoding='utf8').splitlines():
        if line.startswith('## '):
            chapters.append({'title': line[6:], 'shots': {}})
        elif line.startswith('### '):
            shot = chapters[-1]['shots'].setdefault(line[4:], [])
        elif line.strip() and not line.startswith('#'):
            shot.extend(re.split(r'(?<=[.!?])\s+(?=[A-Z])', line.strip()))
    return chapters


def speech_text(text):
    for spelling, spoken in [
        ('XOR', 'ex or'),
        ('AND', 'and'),
        ('eSTREAM', 'ee stream'),
        ("L's", 'ells'),
        (' B C', ' bee see'),
        ('F four', 'eff four'),
    ]:
        text = text.replace(spelling, spoken)
    return text


def engine(folder, threads):
    import onnxruntime as ort
    from kokoro_onnx import Kokoro

    options = ort.SessionOptions()
    options.intra_op_num_threads = threads
    options.inter_op_num_threads = 1
    model = folder / 'kokoro-v1.0.int8.onnx'
    session = ort.InferenceSession(str(model), options, providers=['CPUExecutionProvider'])
    return Kokoro.from_session(session, str(folder / 'voices-v1.0.bin'))


def take(engine, cache, text, speed):
    spoken = speech_text(text)
    key = hashlib.sha256(f'v1-int8/{VOICE}/{speed:.3f}/{spoken}'.encode()).hexdigest()
    file = cache / f'{key}.flac'
    if not file.exists():
        samples, rate = engine.create(spoken, voice=VOICE, speed=speed, lang='en-us', trim=True)
        if rate != RATE or len(samples) < 100:
            raise ValueError(f'Unusable speech for {text}')
        sf.write(file, samples, RATE, subtype='PCM_16')
    return sf.read(file, dtype='float32')[0]


def record(chapter, model, work):
    cache = work / 'takes'
    cache.mkdir(parents=True, exist_ok=True)
    info = script()[chapter]
    rows = [(k, text) for k, lines in info['shots'].items() for text in lines]
    slot = DURATIONS[chapter]
    speed = SPEEDS[chapter]
    for attempt in range(5):
        chunks = [take(model, cache, text, speed) for _, text in rows]
        spoken = sum(map(len, chunks)) / RATE
        gap = (slot - spoken) / len(rows)
        print(
            f'Chapter {chapter + 1}: take at {speed:.3f}, voice {spoken:.2f}s, mean breathing space {gap:.2f}s',
            flush=True,
        )
        if 0.12 <= gap <= 0.92:
            break
        target = slot - 0.43 * len(rows)
        speed = round(speed * spoken / target, 3)
        if not 0.75 <= speed <= 1.35:
            raise ValueError(f'Edit chapter {chapter + 1} for a natural speaking rate.')
    else:
        raise ValueError('Chapter needs editorial retiming.')
    weights = np.array(
        [
            1.45 if j + 1 == len(rows) or rows[j + 1][0] != k else 0.8
            for j, (k, _) in enumerate(rows)
        ]
    )
    room = slot * RATE - sum(map(len, chunks))
    start = round(0.23 * RATE)
    gap_ends = np.rint(np.cumsum(weights) / sum(weights) * (room - start)).astype(int)
    gaps = np.diff(np.r_[0, gap_ends])
    track = np.zeros(slot * RATE, dtype='float32')
    cursor = start
    beats, captions = {}, []
    for (name, text), chunk, gap_n in zip(rows, chunks, gaps, strict=True):
        if name not in beats:
            beats[name] = cursor / RATE if beats else 0
        end = cursor + len(chunk)
        track[cursor:end] = chunk
        captions.append(dict(start=cursor / RATE, end=end / RATE, text=text, shot=name))
        cursor = end + int(gap_n)
    assert cursor == len(track)
    sf.write(work / f'{chapter + 1:02}.flac', track, RATE, subtype='PCM_16')
    (work / f'{chapter + 1:02}.json').write_text(
        json.dumps(
            dict(
                title=info['title'], seconds=slot, beats=beats, captions=captions, voice_speed=speed
            ),
            indent=2,
        ),
        encoding='utf8',
    )


def stamp(time):
    ms = round(time * 1000)
    return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'


def caption_pages(sentence):
    """Fit long takes on two lines and keep the original speech boundaries."""
    tokens = sentence['text'].split()
    pages = []
    while tokens:
        remaining = ' '.join(tokens)
        lines = textwrap.wrap(remaining, width=43, break_long_words=False)
        count = (len(lines) + 1) // 2
        if count == 1:
            page = remaining
            tokens = []
        else:
            goal = len(remaining) / count
            breaks = [
                i
                for i in range(1, len(tokens))
                if len(textwrap.wrap(' '.join(tokens[:i]), width=43)) <= 2
            ]
            split = min(
                breaks,
                key=lambda i: (
                    abs(len(' '.join(tokens[:i])) - goal)
                    - 7 * tokens[i - 1].endswith((',', ';', ':'))
                ),
            )
            page, tokens = ' '.join(tokens[:split]), tokens[split:]
        if len(page) > 43:
            pieces = page.split()
            choices = [(' '.join(pieces[:i]), ' '.join(pieces[i:])) for i in range(1, len(pieces))]
            left, right = min(
                (pair for pair in choices if max(map(len, pair)) <= 43),
                key=lambda pair: abs(len(pair[0]) - len(pair[1])),
            )
            page = left + '\n' + right
        pages.append(page)
    words = [len(page.split()) for page in pages]
    total = sum(words)
    span = sentence['end'] - sentence['start']
    elapsed = 0
    for page, count in zip(pages, words, strict=True):
        start = sentence['start'] + span * elapsed / total
        elapsed += count
        end = sentence['start'] + span * elapsed / total
        yield start, end, page


def write_subtitles(timeline):
    captions = []
    for ch in timeline:
        for cue in ch['captions']:
            for start, end, page in caption_pages(cue):
                lo, hi = stamp(ch['start'] + start), stamp(ch['start'] + end)
                captions.append(f'{len(captions) + 1}\n{lo} --> {hi}\n{page}\n')
    (ROOT / 'subtitles').mkdir(exist_ok=True)
    (ROOT / 'subtitles/Trivium.en.srt').write_text('\n'.join(captions), encoding='utf8')


def assemble(work):
    manifest, tracks, offset = [], [], 0
    for i, slot in enumerate(DURATIONS, 1):
        info = json.loads((work / f'{i:02}.json').read_text())
        samples, rate = sf.read(work / f'{i:02}.flac', dtype='float32')
        if rate != RATE or len(samples) != slot * RATE:
            raise ValueError('Audio duration changed.')
        tracks.append(samples)
        info['start'] = offset
        offset += slot
        manifest.append(info)
    out = ROOT / 'audio'
    out.mkdir(exist_ok=True)
    raw = work / 'unmastered.flac'
    sf.write(raw, np.concatenate(tracks), RATE, subtype='PCM_16')
    # EBU R128 speech mastering preserves timing and reserves true-peak headroom for AAC.
    mastered = work / 'mastered.flac'
    subprocess.run(
        [
            'ffmpeg',
            '-y',
            '-v',
            'error',
            '-i',
            str(raw),
            '-af',
            'loudnorm=I=-18:TP=-1.5:LRA=7',
            '-ar',
            str(RATE),
            '-sample_fmt',
            's16',
            str(mastered),
        ],
        check=True,
    )
    if sf.info(mastered).frames != offset * RATE:
        raise ValueError('Mastering changed the voice duration.')
    destination = out / 'narration.flac'
    if not destination.exists() or not filecmp.cmp(mastered, destination, shallow=False):
        mastered.replace(destination)
    write_subtitles(manifest)
    (ROOT / 'data/timing.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=ROOT / 'build/voice')
    parser.add_argument('--model-dir', type=Path)
    parser.add_argument('--chapters', type=int, nargs='+', choices=range(1, 11))
    parser.add_argument('--threads', type=int, default=3)
    parser.add_argument(
        '--captions-only',
        action='store_true',
        help='Reflow captions from the recorded timing data.',
    )
    args = parser.parse_args()
    if args.captions_only:
        write_subtitles(json.loads((ROOT / 'data/timing.json').read_text(encoding='utf8')))
    elif args.chapters:
        if not args.model_dir:
            parser.error('Recording requires --model-dir.')
        model = engine(args.model_dir, args.threads)
        for i in args.chapters:
            record(i - 1, model, args.work)
    else:
        assemble(args.work)
