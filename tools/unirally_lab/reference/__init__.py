"""Reference emulator adapter (M0-03).

The primary adapter drives a pinned bsnes libretro core, patched with a few
laboratory exports (see ``patches/``), from Python through ``ctypes``. Every
emulation run happens in a fresh worker process so that cold-start
determinism and save/restore can be checked across process boundaries and
so that a hung core can be killed by the bounded runner.
"""
