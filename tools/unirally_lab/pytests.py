"""Run Python unittest discovery and emit one JSON record per test.

Invoked as a subprocess by ``project.py test`` so that the outer report can
attribute an outcome to every individual check.
"""

from __future__ import annotations

import json
import sys
import time
import unittest
from pathlib import Path


class JsonResult(unittest.TestResult):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[dict] = []
        self._start = 0.0

    def startTest(self, test):  # noqa: N802
        super().startTest(test)
        self._start = time.monotonic()

    def _record(self, test, outcome: str, detail: str = "") -> None:
        self.records.append({
            "name": test.id(),
            "outcome": outcome,
            "elapsed": round(time.monotonic() - self._start, 3),
            "detail": detail[-1500:],
        })

    def addSuccess(self, test):  # noqa: N802
        super().addSuccess(test)
        self._record(test, "passed")

    def addFailure(self, test, err):  # noqa: N802
        super().addFailure(test, err)
        self._record(test, "failed", self._exc_info_to_string(err, test))

    def addError(self, test, err):  # noqa: N802
        super().addError(test, err)
        self._record(test, "failed", self._exc_info_to_string(err, test))

    def addSubTest(self, test, subtest, err):  # noqa: N802
        """A failing subtest is a failure of its own; unittest reports it here
        instead of through addFailure/addError and then never calls addSuccess
        for the enclosing test, so without this override the whole test
        vanished from the records (M0-04 review 1, finding M2)."""
        super().addSubTest(test, subtest, err)
        if err is not None:
            self._record(subtest, "failed", self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):  # noqa: N802
        super().addSkip(test, reason)
        self._record(test, "skipped", reason)

    def addExpectedFailure(self, test, err):  # noqa: N802
        super().addExpectedFailure(test, err)
        self._record(test, "passed", "expected failure")

    def addUnexpectedSuccess(self, test):  # noqa: N802
        super().addUnexpectedSuccess(test)
        self._record(test, "failed", "unexpected success")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: pytests.py <start-dir>", file=sys.stderr)
        return 3
    start = Path(argv[1])
    suite = unittest.defaultTestLoader.discover(str(start), top_level_dir=str(start))
    result = JsonResult()
    suite.run(result)
    json.dump({"records": result.records, "tests_run": result.testsRun, "successful": result.wasSuccessful()}, sys.stdout)
    sys.stdout.write("\n")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
