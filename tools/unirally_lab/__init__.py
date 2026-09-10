"""Repository tooling for the Unirally reconstruction laboratory.

Standard library only. Every command is noninteractive, bounded and can
write a JSON report (see :mod:`unirally_lab.report`).
"""

__version__ = "0.1.0"

# Process exit codes shared by every subcommand.
EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_MISSING_PREREQUISITE = 2
EXIT_INVALID_INPUT = 3
EXIT_TIMEOUT = 4
