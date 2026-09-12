"""Identity-bound private visual comparison for the native presentation.

The tracked manifest contains identities and thresholds, never private pixels
or game content. Authorized fixtures remain below ignored ``local/`` or
``artifacts/`` directories and are rehashed before and after every run.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import re
import sys

from .. import report as reports
from ..content import pack as packmod
from ..content import ppu
from ..procs import run_bounded
from . import commands as native_commands
from . import finish, protocol

ROOT = reports.repo_root()
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class PresentationContractError(ValueError):
    pass


def _integer(value: object) -> bool:
    return type(value) is int


def _fixture_name(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise PresentationContractError(f"{label} must be a relative fixture path")
    if ".." in Path(value).parts:
        raise PresentationContractError(f"{label} escapes the fixture directory")
    return value


def load_contract(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if ((data.get("schema_version"), data.get("kind")) !=
            (1, "native_presentation_contract")):
        raise PresentationContractError("unsupported presentation contract")
    if data.get("frame_size") != [256, 224] or data.get("pixel_format") != "rgb888":
        raise PresentationContractError("unsupported presentation pixel contract")
    cases = data.get("reference_cases")
    if not isinstance(cases, list) or not cases:
        raise PresentationContractError("presentation contract has no cases")
    seen: set[str] = set()
    for case in cases:
        case_id = case.get("id") if isinstance(case, dict) else None
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise PresentationContractError("presentation case IDs must be unique")
        seen.add(case_id)
        if not _integer(case.get("frame")) or case["frame"] < 0:
            raise PresentationContractError(f"{case_id} has an invalid frame")
        _fixture_name(case.get("state_file"), f"{case_id} state_file")
        _fixture_name(case.get("reference_file"), f"{case_id} reference_file")
        for field in ("state_sha256", "reference_png_sha256"):
            if not isinstance(case.get(field), str) or not SHA256.fullmatch(case[field]):
                raise PresentationContractError(f"{case_id} has an invalid {field}")
        if not _integer(case.get("camera_x")) or not -(1 << 31) <= case["camera_x"] < (1 << 31):
            raise PresentationContractError(f"{case_id} has an invalid camera_x")
        for field in ("bg1_scroll", "bg2_scroll"):
            values = case.get(field)
            if (not isinstance(values, list) or len(values) != 2 or
                    not all(_integer(v) and -(1 << 15) <= v < (1 << 15) for v in values)):
                raise PresentationContractError(f"{case_id} has an invalid {field}")
        rect = case.get("comparison_rect")
        if (not isinstance(rect, list) or len(rect) != 4 or
                not all(_integer(v) for v in rect)):
            raise PresentationContractError(f"{case_id} has an invalid rectangle")
        x, y, width, height = rect
        if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > 256 or y + height > 224:
            raise PresentationContractError(f"{case_id} rectangle exceeds the frame")
        limit = case.get("maximum_mismatch_fraction")
        if type(limit) is not float or not math.isfinite(limit) or not 0 <= limit <= 1:
            raise PresentationContractError(f"{case_id} has an invalid mismatch limit")
    return data


def parse_ppm(data: bytes) -> bytes:
    header = b"P6\n256 224\n255\n"
    expected = 256 * 224 * 3
    if not data.startswith(header) or len(data) != len(header) + expected:
        raise PresentationContractError("native runner emitted an invalid RGB PPM")
    return data[len(header):]


def compare_rgb(native: bytes, reference: bytes, rect: list[int], limit: float) -> dict:
    expected = 256 * 224 * 3
    if len(native) != expected or len(reference) != expected:
        raise PresentationContractError("visual comparison requires complete RGB frames")
    mismatches, pixels, _ = ppu.compare(native, reference, 256, tuple(rect))
    fraction = mismatches / pixels
    return {"mismatches": mismatches, "pixels": pixels, "fraction": fraction,
            "limit": limit, "passed": fraction <= limit}


def _fixture_path(fixture_root: Path, name: str) -> Path:
    path = (fixture_root / name).resolve()
    if not path.is_relative_to(fixture_root):
        raise PresentationContractError("fixture path escapes fixture directory")
    return path


def cmd_presentation_check(args) -> int:
    root = ROOT.resolve()
    rep = reports.Report(sys.argv, task_id=args.task)
    artifacts = Path(args.artifacts).resolve()
    report_path = Path(args.report).resolve() if args.report else artifacts / "report.json"
    allowed_fixture_roots = (root / "local", root / "artifacts")
    fixture_root = Path(args.fixtures).resolve()
    if (artifacts.exists() or not artifacts.is_relative_to(root / "artifacts") or
            artifacts == root / "artifacts" or not report_path.is_relative_to(artifacts) or
            not any(fixture_root.is_relative_to(base) for base in allowed_fixture_roots) or
            not math.isfinite(args.timeout) or args.timeout <= 0):
        print("presentation check requires fresh artifacts, authorized fixtures, and a positive timeout", file=sys.stderr)
        return 3
    artifacts.mkdir(parents=True)
    status = 0
    bound_inputs: list[tuple[str, Path, str]] = []
    try:
        manifest_path = Path(args.manifest).resolve()
        contract = load_contract(manifest_path)
        manifest_hash = reports.file_sha256(manifest_path)
        rep.add_input("presentation_manifest", manifest_path, manifest_hash)
        bound_inputs.append(("presentation_manifest", manifest_path, manifest_hash))
        pack_path = Path(args.content_pack).resolve()
        rules, rules_hash = packmod.load_rules(root / packmod.RULES_PATH)
        packmod.validate_pack(pack_path.read_bytes(), rules, rules_hash)
        pack_hash = reports.file_sha256(pack_path)
        rep.add_input("classic_pack", pack_path, pack_hash)
        bound_inputs.append(("classic_pack", pack_path, pack_hash))
        runner = root / "build" / args.preset / "src" / "core" / "presentation_runner"
        build = native_commands.build_runner(root, args.preset, args.timeout, artifacts)
        rep.add_check("native_build", build.outcome, detail=build.tail(1500))
        if build.returncode != 0 or build.missing or build.timed_out:
            status = 4 if build.timed_out else (2 if build.missing else 1)
        results = []
        if status == 0:
            rep.add_input("native_binary", runner, reports.file_sha256(runner))
            for case in contract["reference_cases"]:
                case_id = case["id"]
                state = _fixture_path(fixture_root, case["state_file"])
                reference = _fixture_path(fixture_root, case["reference_file"])
                for label, path, expected_hash in (
                        (f"state:{case_id}", state, case["state_sha256"]),
                        (f"reference:{case_id}", reference, case["reference_png_sha256"])):
                    actual_hash = reports.file_sha256(path)
                    if actual_hash != expected_hash:
                        raise PresentationContractError(f"{label} SHA-256 differs from contract")
                    rep.add_input(label, path, actual_hash)
                    bound_inputs.append((label, path, actual_hash))
                state_bytes = state.read_bytes()
                valid_state = ((len(state_bytes) == finish.STATE_V2_BYTES and
                                state_bytes[:8] == finish.STATE_MAGIC_V2) or
                               (len(state_bytes) == finish.STATE_V1_BYTES and
                                state_bytes[:8] == protocol.STATE_MAGIC))
                if (not valid_state or
                        int.from_bytes(state_bytes[8:12], "little") != case["frame"]):
                    raise PresentationContractError(f"{case_id} state width/frame is invalid")
                out = artifacts / f"{case_id}.ppm"
                command = [str(runner), "--content-pack", str(pack_path),
                           "--state", str(state), "--out", str(out),
                           "--camera-x", str(case["camera_x"]),
                           "--bg1-scroll-x", str(case["bg1_scroll"][0]),
                           "--bg1-scroll-y", str(case["bg1_scroll"][1]),
                           "--bg2-scroll-x", str(case["bg2_scroll"][0]),
                           "--bg2-scroll-y", str(case["bg2_scroll"][1])]
                run = run_bounded(command, timeout=args.timeout, cwd=artifacts)
                if run.returncode != 0 or run.missing or run.timed_out:
                    rep.add_check(f"render:{case_id}", run.outcome, detail=run.tail(1000))
                    status = 4 if run.timed_out else (2 if run.missing else 1)
                    break
                native = parse_ppm(out.read_bytes())
                width, height, reference_rgb = ppu.read_png(reference.read_bytes())
                if (width, height) != (256, 224):
                    raise PresentationContractError(f"{case_id} reference dimensions differ")
                result = {"id": case_id, "frame": case["frame"],
                          **compare_rgb(native, reference_rgb,
                                        case["comparison_rect"],
                                        case["maximum_mismatch_fraction"]),
                          "native_sha256": reports.file_sha256(out)}
                results.append(result)
                rep.add_check(f"visual:{case_id}",
                              "passed" if result["passed"] else "failed",
                              detail=(f"{result['mismatches']}/{result['pixels']} = "
                                      f"{result['fraction']:.6%}; limit {result['limit']:.6%}"))
                rep.add_artifact("native_frame", out)
                if not result["passed"]:
                    status = 1
            rep.data["visual_results"] = results
        for label, path, digest in bound_inputs:
            if reports.file_sha256(path) != digest:
                raise PresentationContractError(f"input changed during run: {label}")
    except FileNotFoundError as exc:
        rep.add_check("prerequisite", "missing", detail=str(exc)); status = 2
    except (PresentationContractError, ValueError, KeyError, TypeError, OSError) as exc:
        rep.add_check("contract_or_fixture", "failed", detail=str(exc)); status = 3
    if reports.source_state() != rep.data["source"]:
        rep.add_check("source_stable", "failed",
                      detail="source changed during presentation check")
        status = 1
    rep.finish("passed" if status == 0 else "failed")
    rep.write(report_path)
    reports.print_summary(rep)
    return status


def register(commands) -> None:
    check = commands.add_parser(
        "presentation-check",
        help="run identity-bound native presentation comparisons")
    check.add_argument("--manifest", required=True)
    check.add_argument("--fixtures", required=True,
                       help="authorized fixture directory below local/ or artifacts/")
    check.add_argument("--content-pack", required=True)
    check.add_argument("--preset", choices=("lab-debug", "lab-release", "lab-sanitize"),
                       default="lab-debug")
    check.add_argument("--artifacts", required=True)
    check.add_argument("--report")
    check.add_argument("--timeout", type=float, default=120)
    check.add_argument("--task", default="M3-02")
    check.set_defaults(func=cmd_presentation_check)
