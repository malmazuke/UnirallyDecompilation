import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.unirally_lab.native.prepare import STATIC_CONTENT,canonical_seed,validate_observation,validate_static_content

class NativeSeedPreparationTests(unittest.TestCase):
    def test_canonical_width_header_and_frame(self):
        wram=bytearray(0x20000); sram=bytes(0x2000)
        for address in (0x4eb,0x4ed):wram[address]=1
        for address,value in ((0x211e,0x1234),(0x2122,0x5678),(0x2126,0x9abc),
                              (0x2120,0x1357),(0x2124,0x2468),(0x2128,0xabcd)):
            wram[address:address+2]=value.to_bytes(2,"little")
        state=canonical_seed(bytes(wram),sram)
        self.assertEqual(len(state),297)
        self.assertEqual(state[:12],b"URMV0001\xfd\x05\x00\x00")
        self.assertEqual(state[90:96],bytes.fromhex("34127856bc9a"))
        self.assertEqual(state[200:206],bytes.fromhex("57136824cdab"))

    def test_bad_seed_shape_and_identity_reject(self):
        with self.assertRaisesRegex(ValueError,"128 KiB"):canonical_seed(b"",b"")
        with self.assertRaises(ValueError):validate_observation(Path(__file__),Path(__file__),Path(__file__))

    def test_static_content_identity_is_checked_before_output(self):
        with tempfile.TemporaryDirectory(dir=ROOT/"local") as temporary:
            temporary=Path(temporary); bindings=[]
            for name,(size,_) in STATIC_CONTENT.items():
                source=temporary/name; source.write_bytes(bytes(size))
                bindings.append(f"{name}={source}")
            out=temporary/"runtime"
            with self.assertRaisesRegex(ValueError,"static content identity"):
                validate_static_content(bindings,out)
            self.assertFalse(out.exists())

if __name__=="__main__":unittest.main()
