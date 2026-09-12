"""Reproduce the single end1533 WRAM/SRAM seed in a fresh original process."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from ...reference.bsnes import BsnesCore
from ...reference.worker import inputs_for_frame
from ...replay.manifest import derive_script


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--samples',type=Path,required=True,help='unchanged primary reference sample metadata identifying the built core')
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();samples=json.loads(a.samples.read_text())
    manifest_path=Path('tests/manifests/replay/race-crawler-dragster-3000-fields.json')
    manifest=json.loads(manifest_path.read_text());script=derive_script(manifest)
    if samples['sample_digest']!=manifest['expected']['sample_digest']:raise ValueError('samples do not reproduce the frozen primary')
    rom=Path(Path('local/rom-location.txt').read_text().strip());library=Path(samples['core']['library'])
    if hashlib.sha256(rom.read_bytes()).hexdigest()!=manifest['rom']['sha256']:raise ValueError('ROM identity mismatch')
    if hashlib.sha256(library.read_bytes()).hexdigest()!=samples['core']['sha256']:raise ValueError('core library identity mismatch')
    a.out.mkdir(parents=True,exist_ok=True)
    if (a.out/'wram.bin').exists():raise ValueError('refusing to overwrite an existing seed observation')
    with tempfile.TemporaryDirectory(prefix='fresh-',dir=a.out) as private_system:
        core=BsnesCore(library,Path(private_system),script.get('core_options'))
        try:
            core.load(rom);core.set_serialization_method('Strict')
            for frame in range(1534):
                for port,buttons in inputs_for_frame(script,frame).items():core.set_inputs(port,buttons)
                core.run_frame()
            wram=core.wram();sram=core.cartridge_ram()
            if hashlib.sha256(wram).hexdigest()!=samples['frames'][1533]['wram_sha256']:raise ValueError('seed WRAM differs from frozen primary process')
        finally:core.unload()
    (a.out/'wram.bin').write_bytes(wram);(a.out/'cartridge.bin').write_bytes(sram)
    result={'schema_version':1,'kind':'original_single_seed','after_frame':1533,'rom_sha256':manifest['rom']['sha256'],'core_library_sha256':samples['core']['sha256'],'reference_samples_sha256':hashlib.sha256(a.samples.read_bytes()).hexdigest(),'manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),'wram_sha256':hashlib.sha256(wram).hexdigest(),'cartridge_sha256':hashlib.sha256(sram).hexdigest(),'cartridge_bytes':len(sram),'feature_total_770825':int.from_bytes(sram[0x825:0x827],'little'),'event_one_weight_7e2102':wram[0x2102]}
    (a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
