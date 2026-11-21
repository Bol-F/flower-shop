"""A scalar Trivium clock, using specification positions and the reference byte convention."""

from dataclasses import dataclass

REGISTERS = ((1, 93), (94, 177), (178, 288))
TAPS = ((66, 93), (162, 177), (243, 288))
NONLINEAR = ((91, 92, 171), (175, 176, 264), (286, 287, 69))
WARMUP = 4 * 288
State = tuple[int, ...]


def register_input(value: bytes) -> State:
    """In default eSTREAM byte order s1 is bit 7 of the final key byte."""
    if len(value) != 10:
        raise ValueError('Trivium requires a ten-byte key and a ten-byte IV.')
    return tuple((byte >> shift) & 1 for byte in reversed(value) for shift in range(7, -1, -1))


def load_state(key: bytes, iv: bytes) -> State:
    return register_input(key) + (0,) * 13 + register_input(iv) + (0,) * 4 + (0,) * 108 + (1, 1, 1)


@dataclass(frozen=True)
class Signals:
    taps: tuple[int, ...]
    products: tuple[int, ...]
    feedback: tuple[int, ...]
    output: int


def signals(state: State) -> Signals:
    taps = tuple(state[left - 1] ^ state[right - 1] for left, right in TAPS)
    products = tuple(state[left - 1] & state[right - 1] for left, right, _ in NONLINEAR)
    feedback = tuple(t ^ p ^ state[c - 1] for t, p, (_, _, c) in zip(taps, products, NONLINEAR))
    return Signals(taps, products, feedback, taps[0] ^ taps[1] ^ taps[2])


def clock(state: State) -> tuple[int, State]:
    """Compute every signal from the old snapshot and commit the three shifts together."""
    s = signals(state)
    t1, t2, t3 = s.feedback
    return s.output, (t3,) + state[:92] + (t1,) + state[93:176] + (t2,) + state[177:287]


def advance(state: State, count: int) -> State:
    if count < 0:
        raise ValueError('Clock count must be nonnegative.')
    for _ in range(count):
        _, state = clock(state)
    return state


def stream_bits(state: State, length: int) -> State:
    if length < 0:
        raise ValueError('Bit count must be nonnegative.')
    bits = []
    for _ in range(length):
        bit, state = clock(state)
        bits.append(bit)
    return tuple(bits)


def pack(bits: State) -> bytes:
    if len(bits) % 8:
        raise ValueError('Packing requires complete bytes.')
    return bytes(
        sum(bit << j for j, bit in enumerate(bits[i : i + 8])) for i in range(0, len(bits), 8)
    )


def crypt(key: bytes, iv: bytes, message: bytes) -> bytes:
    state = advance(load_state(key, iv), WARMUP)
    mask = pack(stream_bits(state, len(message) * 8))
    return bytes(p ^ k for p, k in zip(message, mask, strict=True))
