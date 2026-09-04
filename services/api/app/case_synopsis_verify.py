# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
from pathlib import Path
import re
import sys


_MAX_EXPORT_BYTES = 2 * 1024 * 1024
_MAX_SIDECAR_BYTES = 512
_CHECKSUM_LINE = re.compile(r"^([0-9a-f]{64})  ([^\r\n]+)\n?$")


def _regular_file(path: Path, *, label: str, max_bytes: int) -> bytes:
    if path.is_symlink():
        raise ValueError(f"{label} must not be a symbolic link.")
    if not path.exists() or not path.is_file():
        raise ValueError(f"{label} is missing or is not a regular file.")
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(f"{label} exceeds the verification size limit.")
    return path.read_bytes()


def verify_case_synopsis_export(source: str | Path) -> str:
    """Verify a PersonaLattice synopsis against its adjacent SHA-256 sidecar.

    This proves local file integrity relative to the sidecar. It is deliberately not
    described as authorship, signature or provenance authentication.
    """

    path = Path(source).expanduser()
    if path.name in {"", ".", ".."}:
        raise ValueError("Synopsis path must name a file.")

    checksum_path = path.with_name(f"{path.name}.sha256")
    content = _regular_file(path, label="Synopsis export", max_bytes=_MAX_EXPORT_BYTES)
    checksum_bytes = _regular_file(
        checksum_path,
        label="Synopsis checksum sidecar",
        max_bytes=_MAX_SIDECAR_BYTES,
    )

    try:
        checksum_line = checksum_bytes.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError("Synopsis checksum sidecar must be ASCII.") from exc

    match = _CHECKSUM_LINE.fullmatch(checksum_line)
    if match is None:
        raise ValueError("Synopsis checksum sidecar has an invalid format.")
    expected_digest, expected_name = match.groups()
    if expected_name != path.name:
        raise ValueError("Synopsis checksum sidecar names a different export file.")

    actual_digest = hashlib.sha256(content).hexdigest()
    if not hmac.compare_digest(actual_digest, expected_digest):
        raise ValueError("Synopsis checksum does not match the export content.")

    try:
        payload = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Synopsis export is not valid UTF-8 JSON.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Synopsis export must contain a JSON object.")
    if not isinstance(payload.get("synopsis_version"), str):
        raise ValueError("Synopsis export is missing a synopsis_version.")
    if not isinstance(payload.get("case"), dict):
        raise ValueError("Synopsis export is missing case metadata.")
    if not isinstance(payload.get("evidence_summary"), dict):
        raise ValueError("Synopsis export is missing its evidence summary.")
    if not isinstance(payload.get("method_limits"), list):
        raise ValueError("Synopsis export is missing method limits.")

    return actual_digest


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify a PersonaLattice retained-case synopsis and its adjacent SHA-256 sidecar."
    )
    parser.add_argument("path", type=Path, help="path to the exported synopsis JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        digest = verify_case_synopsis_export(args.path)
    except (OSError, ValueError) as exc:
        print(f"Synopsis verification failed: {exc}", file=sys.stderr)
        return 2

    print(f"VERIFIED {digest}  {args.path.name}")
    print("Integrity verified against the sidecar; this checksum is not an authorship signature.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
