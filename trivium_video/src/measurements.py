"""Reproducible inputs, snapshots and measurements used in the film."""

import json
from functools import cache
from itertools import accumulate
from math import erfc, sqrt
from pathlib import Path

from src.trivium_core import WARMUP, clock, crypt, load_state, pack, signals, stream_bits

ROOT = Path(__file__).resolve().parents[1]
VECTORS = json.loads((ROOT / 'data/estream.json').read_text(encoding='utf8'))
DEMO = next(v for v in VECTORS if v['set'] == 6)
KEY, IV = bytes.fromhex(DEMO['key']), bytes.fromhex(DEMO['iv'])
OTHER_IV = IV[:-1] + bytes([IV[-1] ^ 0x80])
MESSAGE = b'HELLO'


@cache
def history(iv=IV):
    states = [load_state(KEY, iv)]
    for _ in range(WARMUP + 40):
        states.append(clock(states[-1])[1])
    return tuple(states)


def differences(left, right):
    return tuple(a ^ b for a, b in zip(left, right, strict=True))


def output_difference(cycles, length=128):
    left, right = (stream_bits(history(iv)[cycles], length) for iv in (IV, OTHER_IV))
    return tuple(accumulate(differences(left, right), initial=0))


def statistics(bits):
    n = len(bits)
    if n < 2:
        raise ValueError('At least two observations are needed.')
    ones = sum(bits)
    pi = ones / n
    runs = 1 + sum(a != b for a, b in zip(bits, bits[1:]))
    freq = erfc(abs(2 * ones - n) / sqrt(2 * n))
    runs_p = None
    if abs(pi - 0.5) < 2 / sqrt(n) and 0 < pi < 1:
        runs_p = erfc(abs(runs - 2 * n * pi * (1 - pi)) / (2 * sqrt(2 * n) * pi * (1 - pi)))
    return {
        'n': n,
        'ones': ones,
        'zeros': n - ones,
        'runs': runs,
        'frequency_p': freq,
        'runs_p': runs_p,
    }


@cache
def evidence():
    states = history()
    ready = states[WARMUP]
    bits = stream_bits(ready, 4096)
    ciphertext = crypt(KEY, IV, MESSAGE)
    detail = signals(ready)
    expected = bytes.fromhex(DEMO['blocks']['0'])
    actual = pack(bits[:512])
    if actual != expected:
        raise ValueError("The film's reference vector failed.")
    return {
        'key': KEY.hex().upper(),
        'iv': IV.hex().upper(),
        'flipped_iv': OTHER_IV.hex().upper(),
        'preclock': ''.join(map(str, ready)),
        'postclock': ''.join(map(str, states[WARMUP + 1])),
        'linear': detail.taps,
        'and': detail.products,
        'feedback': detail.feedback,
        'z': detail.output,
        'keystream': pack(bits[:40]).hex().upper(),
        'ciphertext': ciphertext.hex().upper(),
        'recovered': crypt(KEY, IV, ciphertext).decode(),
        'distance_128': {n: output_difference(n)[-1] for n in (288, 576, 1152)},
        'statistics': statistics(bits),
        'expected': expected.hex().upper(),
        'actual': actual.hex().upper(),
    }


if __name__ == '__main__':
    (ROOT / 'data/measurements.json').write_text(
        json.dumps(evidence(), indent=2) + '\n', encoding='utf8'
    )
