import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.unirally_lab.native.prepare import canonical_seed,validate_observation

class NativeSeedPreparationTests(unittest.TestCase):
    def test_canonical_width_header_and_frame(self):
        wram=bytearray(0x20000); sram=bytes(0x2000)
        for address in (0x4eb,0x4ed):wram[address]=1
        state=canonical_seed(bytes(wram),sram)
        self.assertEqual(len(state),295)
        self.assertEqual(state[:12],b"URMV0001\xfd\x05\x00\x00")

    def test_bad_seed_shape_and_identity_reject(self):
        with self.assertRaisesRegex(ValueError,"128 KiB"):canonical_seed(b"",b"")
        with self.assertRaises(ValueError):validate_observation(Path(__file__),Path(__file__),Path(__file__))

if __name__=="__main__":unittest.main()
