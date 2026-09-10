"""M0-03 evaluation probe: drive the Mesen Community Edition core library headlessly.

Not a supported adapter (see docs/decisions/D-0001-reference-emulator.md).
Kept so the Mesen side of the comparison can be reproduced.

Usage: mesen_probe.py MesenCore.dylib <MesenCE checkout> <rom> <frames> <out.json>
                      [state_in.mss] [save_after] [state_out.mss]
Environment: MESEN_STEP=scanline (stop at scanline 240 instead of counting PPU
dots), MESEN_MAXSPEED=1, MESEN_LIMIT=<seconds per step>, MESEN_VERBOSE=1,
MESEN_SCRIPT='[[from,to,port,["Start"]], ...]'.

Struct layouts mirror Core/Shared/SettingTypes.h at commit 20f497c9 and are
checked at start-up against sizes printed by mesen_layout_check.cpp.
"""
import ctypes as C, hashlib, json, os, re, struct, sys, time
CORE, SRC, ROM, FRAMES, OUT = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
STATE_IN = sys.argv[6] if len(sys.argv) > 6 and sys.argv[6] else None; SAVE_AT = int(sys.argv[7]) if len(sys.argv) > 7 else -1; STATE_OUT = sys.argv[8] if len(sys.argv) > 8 else None
def enum_index(header, name, member):
    body = re.search(r"enum class %s\b[^{]*\{(.*?)\}" % name, open(header).read(), re.S).group(1)
    names = [l.strip().rstrip(",").split("=")[0].strip() for l in body.splitlines() if l.strip() and not l.strip().startswith("//")]
    names = [n for n in names if re.match(r"^[A-Za-z_]\w*$", n)]
    return names.index(member)
ST = os.path.join(SRC, "Core/Shared/SettingTypes.h"); MT = os.path.join(SRC, "Core/Shared/MemoryType.h")
SNES_CTRL = enum_index(ST, "ControllerType", "SnesController"); WRAM = enum_index(MT, "MemoryType", "SnesWorkRam"); PRG = enum_index(MT, "MemoryType", "SnesPrgRom")
RAM_ZEROS = 1; CONSOLE_MODE = 0x10; CPU_SNES = 0; STEP_PPU_FRAME = 6
u16, u32, i32, i64, b8 = C.c_uint16, C.c_uint32, C.c_int32, C.c_int64, C.c_bool
class KeyMapping(C.Structure): _fields_ = [("keys", u16 * 23), ("custom", u16 * 100)]
class KeyMappingSet(C.Structure): _fields_ = [("m", KeyMapping * 4), ("turbo", u32)]
class ControllerConfig(C.Structure): _fields_ = [("keys", KeyMappingSet), ("type", C.c_int)]
class Overscan(C.Structure): _fields_ = [("l", u32), ("r", u32), ("t", u32), ("b", u32)]
class SnesConfig(C.Structure):
    _fields_ = [("port1", ControllerConfig), ("port2", ControllerConfig), ("p1sub", ControllerConfig * 4), ("p2sub", ControllerConfig * 4),
                ("region", C.c_int), ("allow_invalid", b8), ("color_correction", C.c_int), ("hires_blend", C.c_int), ("deinterlace", C.c_int),
                ("hide1", b8), ("hide2", b8), ("hide3", b8), ("hide4", b8), ("hide_sprites", b8), ("no_frameskip", b8), ("fixed_res", b8), ("no_sprite_limit", b8),
                ("overscan", Overscan), ("interp", C.c_int), ("volumes", u32 * 8), ("random_poweron", b8), ("strict_boards", b8), ("ram_state", C.c_int),
                ("spc_adj", i32), ("ppu_before", u32), ("ppu_after", u32), ("gsu", u32), ("bsx_date", i64)]
assert C.sizeof(SnesConfig) == 10032 and SnesConfig.ram_state.offset == 10004 and SnesConfig.region.offset == 9920, (C.sizeof(SnesConfig), SnesConfig.ram_state.offset)
class CpuState(C.Structure): _fields_ = [("cycles", C.c_uint64), ("A", u16), ("X", u16), ("Y", u16), ("SP", u16), ("D", u16), ("PC", u16), ("K", C.c_uint8), ("DBR", C.c_uint8), ("PS", C.c_uint8), ("pad", C.c_uint8 * 9)]
assert C.sizeof(CpuState) == 32
class TimingInfo(C.Structure): _fields_ = [("fps", C.c_double), ("master_clock", C.c_uint64), ("master_clock_rate", u32), ("frame_count", u32), ("scanline_count", u32), ("first_scanline", i32), ("cycle_count", u32)]
class Pad(C.Structure): _fields_ = [(n, b8) for n in "A B X Y L R U D Up Down Left Right Select Start".split()]

lib = C.CDLL(CORE)
for name, res in (("LoadRom", b8), ("IsExecutionStopped", b8), ("IsRunning", b8), ("IsPaused", b8), ("GetMemorySize", u32), ("GetMesenVersion", u32)):
    getattr(lib, name).restype = res
lib.InitializeEmu.argtypes = [C.c_char_p, C.c_void_p, C.c_void_p, b8, b8, b8, b8]
lib.SetSnesConfig.argtypes = [SnesConfig]; lib.SetEmulationFlag.argtypes = [C.c_int, b8]
lib.Step.argtypes = [C.c_int, u32, C.c_int]; lib.GetMemoryState.argtypes = [C.c_int, C.c_void_p]; lib.GetCpuState.argtypes = [C.c_void_p, C.c_int]
lib.SetInputOverrides.argtypes = [u32, Pad]; lib.GetTimingInfo.restype = TimingInfo; lib.GetTimingInfo.argtypes = [C.c_int]; lib.GetRomHash.argtypes = [C.c_int, C.c_char_p, u32]
home = os.path.join(os.path.dirname(OUT), "mesen-home"); os.makedirs(home, exist_ok=True)
lib.InitDll(); lib.InitializeEmu(home.encode(), None, None, False, True, True, True)
cfg = SnesConfig(); cfg.port1.type = SNES_CTRL; cfg.ram_state = RAM_ZEROS; cfg.volumes[:] = [100] * 8; cfg.gsu = 100; cfg.bsx_date = -1
lib.SetSnesConfig(cfg)
lib.SetEmulationFlag(CONSOLE_MODE, True)
if os.environ.get("MESEN_MAXSPEED"): lib.SetEmulationFlag(0x04, True)
STEP_MODE = os.environ.get("MESEN_STEP", "frame")
lib.Pause()
t0 = time.monotonic()
ok = lib.LoadRom(ROM.encode(), None)
assert ok, "load failed"
def wait_stopped(target_frame=None, limit=30.0):
    t = time.monotonic()
    while True:
        ti = lib.GetTimingInfo(CPU_SNES)
        if lib.IsExecutionStopped() and lib.IsPaused() and (target_frame is None or ti.frame_count >= target_frame):
            return ti
        if time.monotonic() - t > limit:
            st = CpuState(); lib.GetCpuState(C.byref(st), CPU_SNES)
            raise RuntimeError(f"step did not stop (frame {ti.frame_count}, target {target_frame}, stopped={lib.IsExecutionStopped()}, paused={lib.IsPaused()}, running={lib.IsRunning()}, pc={st.K:02x}{st.PC:04x} cycles={st.cycles} master={ti.master_clock})")
        time.sleep(0.0002)
ti = wait_stopped(); result_timing = {"fps": ti.fps, "master_clock_rate": ti.master_clock_rate, "frame_count_at_load": ti.frame_count, "scanline_count": ti.scanline_count}
version = lib.GetMesenVersion(); hb = C.create_string_buffer(64); lib.GetRomHash(0, hb, 64)
wsz = lib.GetMemorySize(WRAM); wbuf = C.create_string_buffer(wsz); psz = lib.GetMemorySize(PRG); pbuf = C.create_string_buffer(psz); lib.GetMemoryState(PRG, pbuf)
result = {"mesen_version": f"{version>>16}.{(version>>8)&0xff}.{version&0xff}", "rom_sha1": hb.value.decode(), "prg_rom_size": psz, "prg_rom_sha256": hashlib.sha256(pbuf.raw).hexdigest(), "wram_size": wsz, "timing": result_timing, "frames": []}
def sample():
    lib.GetMemoryState(WRAM, wbuf); st = CpuState(); lib.GetCpuState(C.byref(st), CPU_SNES)
    return hashlib.sha256(wbuf.raw).hexdigest()[:16], {"pc": f"{st.K:02x}{st.PC:04x}", "a": st.A, "x": st.X, "y": st.Y, "s": st.SP, "d": st.D, "b": st.DBR, "p": st.PS, "cycles": st.cycles}
w, regs = sample(); result["initial"] = {"wram": w, "regs": regs}
lib.SaveStateFile.argtypes = [C.c_char_p]; lib.LoadStateFile.argtypes = [C.c_char_p]
start = 0
if STATE_IN:
    lib.LoadStateFile(STATE_IN.encode()); ti = wait_stopped(); start = int(os.path.basename(STATE_IN).split("-")[-1].split(".")[0]) + 1
    w, regs = sample(); result["restored"] = {"wram": w, "regs": regs, "frame_count": ti.frame_count, "master_clock": ti.master_clock}
SCRIPT = json.loads(os.environ.get("MESEN_SCRIPT", "[]"))
t1 = time.monotonic()
VERBOSE = os.environ.get("MESEN_VERBOSE")
try:
  for i in range(start, FRAMES):
    pad = Pad()
    for lo, hi, port, names in SCRIPT:
        if lo <= i <= hi and port == 0:
            for n in names: setattr(pad, n, True)
    lib.SetInputOverrides(0, pad)
    before = lib.GetTimingInfo(CPU_SNES)
    ts = time.monotonic(); lib.Step(CPU_SNES, 240, 7) if STEP_MODE == "scanline" else lib.Step(CPU_SNES, 1, STEP_PPU_FRAME); ti = wait_stopped(before.frame_count + 1, limit=float(os.environ.get("MESEN_LIMIT", "30")))
    w, regs = sample(); result["frames"].append({"i": i, "wram": w, "regs": regs, "frame_count": ti.frame_count, "master_clock": ti.master_clock})
    if i == SAVE_AT and STATE_OUT:
        lib.SaveStateFile(STATE_OUT.encode()); result["state_sha256"] = hashlib.sha256(open(STATE_OUT, "rb").read()).hexdigest(); result["state_size"] = os.path.getsize(STATE_OUT)
    if VERBOSE: print(f"step {i}: frame {before.frame_count}->{ti.frame_count} master +{ti.master_clock - before.master_clock} in {time.monotonic()-ts:.4f}s pc={regs['pc']} wram={w}", flush=True)
except Exception as exc:
  print("ERROR:", exc, flush=True); result["error"] = str(exc)
finally:
  lib.Stop(); lib.Release()
result["elapsed_load"] = round(t1 - t0, 3); result["elapsed_run"] = round(time.monotonic() - t1, 3)
json.dump(result, open(OUT, "w"), indent=1)
print(json.dumps({k: v for k, v in result.items() if k != "frames"}), "last=", result["frames"][-1] if result["frames"] else None)
