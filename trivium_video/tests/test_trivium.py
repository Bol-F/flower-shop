import unittest

from src.measurements import (
    IV,
    KEY,
    MESSAGE,
    OTHER_IV,
    VECTORS,
    differences,
    evidence,
    history,
    output_difference,
    statistics,
)
from src.trivium_core import WARMUP, advance, clock, crypt, load_state, pack, signals, stream_bits


class TriviumTests(unittest.TestCase):
    def test_reference_blocks(self):
        for v in VECTORS:
            key, iv = bytes.fromhex(v['key']), bytes.fromhex(v['iv'])
            state = advance(load_state(key, iv), WARMUP)
            end = max(int(k) + len(bytes.fromhex(value)) for k, value in v['blocks'].items())
            result = pack(stream_bits(state, 8 * end))
            for k, expected in v['blocks'].items():
                with self.subTest(vector=(v['set'], v['vector']), offset=k):
                    start = int(k)
                    self.assertEqual(
                        result[start : start + len(expected) // 2], bytes.fromhex(expected)
                    )
            plaintext = bytes(range(64))
            expected_cipher = bytes(
                p ^ b for p, b in zip(plaintext, bytes.fromhex(v['blocks']['0']))
            )
            self.assertEqual(crypt(key, iv, plaintext), expected_cipher)
            self.assertEqual(crypt(key, iv, expected_cipher), plaintext)

    def test_boundary_and_byte_order(self):
        state = load_state(bytes.fromhex('80' + '00' * 9), bytes.fromhex('00' * 9 + '01'))
        self.assertEqual([i + 1 for i, bit in enumerate(state) if bit], [73, 101, 286, 287, 288])
        self.assertEqual(pack((1, 0, 1, 0, 0, 0, 0, 0)), b'\x05')
        self.assertEqual(sum(differences(history()[0], history(OTHER_IV)[0])), 1)

    def test_simultaneous_commit(self):
        for i in (0, 1, 287, 575, 1151, 1152):
            before = history()[i]
            bit, after = clock(before)
            sig = signals(before)
            self.assertEqual(bit, sig.output)
            self.assertEqual(
                (after[0], after[93], after[177]), (sig.feedback[2], *sig.feedback[:2])
            )
            self.assertEqual(
                (after[1:93], after[94:177], after[178:]),
                (before[:92], before[93:176], before[177:287]),
            )

    def test_hello(self):
        self.assertEqual(evidence()['recovered'], MESSAGE.decode())
        self.assertEqual(crypt(KEY, IV, b''), b'')

    def test_statistics(self):
        self.assertEqual(statistics((0, 0, 1, 1, 0, 1))['runs'], 4)
        self.assertIsNone(statistics((0,) * 128)['runs_p'])
        for n in (288, 576, 1152):
            curve = output_difference(n)
            self.assertEqual(len(curve), 129)
            self.assertTrue(all(b - a in (0, 1) for a, b in zip(curve, curve[1:])))

    def test_invalid_inputs(self):
        for k, v in [(b'', IV), (KEY, b'')]:
            with self.assertRaises(ValueError):
                load_state(k, v)
        with self.assertRaises(ValueError):
            pack((1,))
        with self.assertRaises(ValueError):
            advance(history()[0], -1)
