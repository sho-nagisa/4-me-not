from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path


ENTRY_SEPARATOR = "--- entry ---"


@dataclass
class ParsedRawEntry:
    source_index: int
    raw_text: str
    captured_date: str | None
    source: str = "text_import"
    parse_status: str = "pending"


@dataclass
class ParseIssue:
    source_index: int
    message: str


def parse_raw_entry_text(content: str) -> tuple[list[ParsedRawEntry], list[ParseIssue]]:
    blocks = _split_entry_blocks(content)
    entries: list[ParsedRawEntry] = []
    issues: list[ParseIssue] = []

    for index, block in enumerate(blocks, start=1):
        entry, entry_issues = _parse_block(index, block)
        issues.extend(entry_issues)
        if entry is not None:
            entries.append(entry)

    return entries, issues


def _split_entry_blocks(content: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] | None = None

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if line == ENTRY_SEPARATOR:
            if current is not None:
                blocks.append(current)
            current = []
            continue
        if current is None:
            continue
        current.append(raw_line.rstrip())

    if current is not None:
        blocks.append(current)
    return blocks


def _parse_block(
    source_index: int,
    block: list[str],
) -> tuple[ParsedRawEntry | None, list[ParseIssue]]:
    issues: list[ParseIssue] = []
    captured_date: str | None = None
    text_lines: list[str] = []
    reading_text = False
    saw_text_label = False

    for raw_line in block:
        stripped = raw_line.strip()
        if not stripped and not reading_text:
            continue

        if stripped.lower().startswith("date:") and not reading_text:
            date_text = stripped.split(":", 1)[1].strip()
            if date_text:
                captured_date = _parse_date(date_text, source_index, issues)
            continue

        if stripped.lower().startswith("text:") and not reading_text:
            saw_text_label = True
            reading_text = True
            inline_text = raw_line.split(":", 1)[1].strip()
            if inline_text:
                text_lines.append(inline_text)
            continue

        text_lines.append(raw_line.strip() if not reading_text else raw_line)
        reading_text = reading_text or not saw_text_label

    raw_text = "\n".join(line.rstrip() for line in text_lines).strip()
    if not raw_text:
        issues.append(ParseIssue(source_index, "Entry text is empty"))
        return None, issues

    return (
        ParsedRawEntry(
            source_index=source_index,
            raw_text=raw_text,
            captured_date=captured_date,
        ),
        issues,
    )


def _parse_date(
    value: str,
    source_index: int,
    issues: list[ParseIssue],
) -> str | None:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        issues.append(ParseIssue(source_index, f"Date is invalid: {value}"))
        return None


def build_payload(
    input_name: str,
    entries: list[ParsedRawEntry],
    issues: list[ParseIssue],
) -> dict:
    return {
        "source_file": input_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entry_count": len(entries),
        "issue_count": len(issues),
        "entries": [asdict(entry) for entry in entries],
        "issues": [asdict(issue) for issue in issues],
    }


def read_input(path_text: str) -> tuple[str, str]:
    if path_text == "-":
        return "stdin", sys.stdin.read()
    path = Path(path_text)
    return str(path), path.read_text(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert RawEntry import text into structured JSON."
    )
    parser.add_argument(
        "input",
        help="Input text file path. Use '-' to read from stdin.",
    )
    parser.add_argument(
        "--out",
        help="Output JSON file path. Defaults to stdout.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 when parse issues are found.",
    )
    args = parser.parse_args()

    input_name, content = read_input(args.input)
    entries, issues = parse_raw_entry_text(content)
    payload = build_payload(input_name, entries, issues)
    output = json.dumps(payload, ensure_ascii=False, indent=2)

    if args.out:
        Path(args.out).write_text(f"{output}\n", encoding="utf-8")
    else:
        print(output)

    if args.strict and issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
