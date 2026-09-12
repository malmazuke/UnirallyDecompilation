import hashlib
import struct
import unittest

from unirally_lab.native import opponent_first


class OpponentFirstProjectionTests(unittest.TestCase):
    def state(self, frame: int, *, version: int = 3) -> bytes:
        data = bytearray(371 if version == 3 else 333)
        data[:8] = f"URMV000{version}".encode()
        data[8:12] = frame.to_bytes(4, "little")
        values = {16: 1088, 144: 25359, 146: 857, 148: 5, 216: 0x0A4A,
                  272: 0, 274: 3, 276: 3, 278: 9, 280: 2}
        for offset, value in values.items():
            data[offset:offset + 2] = value.to_bytes(2, "little")
        if version == 3:
            data[334] = 1
        return bytes(data)

    def test_projection_uses_canonical_rider_one_and_timer_offsets(self):
        self.assertEqual(opponent_first.projection(self.state(3231)),
                         [25359,857,5,0x0A4A,1088,0,1,0,0,3,3,9,2])

    def test_prefinish_v1_has_zero_finish_fields(self):
        values = opponent_first.projection(self.state(1533, version=1))
        self.assertEqual(values[5:8], [0,0,0])

    def test_digest_encoding_is_fixed_little_endian_rows(self):
        states = [self.state(3231), self.state(3232)]
        digest, rows = opponent_first.projection_digest(states, 3231)
        encoded = b"".join(struct.pack("<I13H", frame, *rows[str(frame)])
                           for frame in (3231,3232))
        self.assertEqual(digest, hashlib.sha256(encoded).hexdigest())


if __name__ == "__main__":
    unittest.main()
