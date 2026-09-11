"""Instruction-coverage capture and the observed code/data map (M1-01).

``drain`` accumulates the core's trace ring once per frame, ``opcodes`` is the
65816 length/addressing table, ``mapping`` the LoROM address rule, ``derive``
turns a coverage file plus the ROM into the tracked map, and ``commands``
registers ``coverage capture|map``.
"""
