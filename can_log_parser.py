"""Parse common candump text formats and export CAN frames as CSV."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, TextIO


_PREFIX = r"(?:\([^)]+\)\s+)?(?:\S+\s+)?"
_COMPACT_FRAME = re.compile(
    rf"^{_PREFIX}(?P<can_id>[0-9A-Fa-f]{{1,8}})#(?P<data>[0-9A-Fa-f]*)$"
)
_SPACED_FRAME = re.compile(
    rf"^{_PREFIX}(?P<can_id>[0-9A-Fa-f]{{1,8}})\s+"
    r"\[(?P<dlc>\d{1,2})\](?:\s+(?P<data>(?:[0-9A-Fa-f]{2}(?:\s+|$))*))?$"
)


@dataclass(frozen=True)
class CanFrame:
    """The fields retained from one CAN log frame."""

    can_id: str
    dlc: int
    data: str


def parse_line(line: str) -> CanFrame:
    """Parse one candump line, raising ``ValueError`` for an invalid frame."""
    text = line.strip()
    match = _COMPACT_FRAME.fullmatch(text)
    if match:
        data = match.group("data")
        if len(data) % 2:
            raise ValueError("DATA must contain complete hexadecimal bytes")
        dlc = len(data) // 2
        normalized_data = " ".join(data[index : index + 2] for index in range(0, len(data), 2))
    else:
        match = _SPACED_FRAME.fullmatch(text)
        if not match:
            raise ValueError("unsupported CAN frame format")
        normalized_data = " ".join((match.group("data") or "").split())
        dlc = int(match.group("dlc"))
        if dlc != (len(normalized_data.split()) if normalized_data else 0):
            raise ValueError("DLC does not match the number of DATA bytes")

    can_id_value = int(match.group("can_id"), 16)
    if can_id_value > 0x1FFFFFFF:
        raise ValueError("CAN ID exceeds the 29-bit maximum")
    if dlc > 64:
        raise ValueError("DLC exceeds the CAN FD maximum of 64 bytes")

    return CanFrame(match.group("can_id").upper(), dlc, normalized_data.upper())


def parse_log(lines: Iterable[str], error_stream: TextIO = sys.stderr) -> list[CanFrame]:
    """Parse log lines, reporting and skipping blank or malformed frames."""
    frames: list[CanFrame] = []
    for line_number, line in enumerate(lines, start=1):
        try:
            frames.append(parse_line(line))
        except ValueError as error:
            print(f"line {line_number}: {error}; skipped: {line.rstrip()}", file=error_stream)
    return frames


def export_csv(frames: Iterable[CanFrame], output: TextIO) -> None:
    """Write parsed frames to a CSV stream."""
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["ID", "DLC", "DATA"])
    for frame in frames:
        writer.writerow([frame.can_id, frame.dlc, frame.data])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="candump text file to parse")
    parser.add_argument("output", type=Path, help="destination CSV file")
    args = parser.parse_args(argv)

    with args.input.open(encoding="utf-8") as source:
        frames = parse_log(source)
    with args.output.open("w", encoding="utf-8", newline="") as destination:
        export_csv(frames, destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
