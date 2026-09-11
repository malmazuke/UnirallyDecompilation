"""Trace-derived memory access record (M1-02, D-0002 option 2).

Every executed instruction's effective addresses, access kinds, widths and
stored values are derived from the unchanged trace ring (pre-instruction
registers) and the ROM bytes at the pc; nothing is guessed and the residual
(indirect pointers, code in work RAM, DMA engine transfers) is counted.
"""
