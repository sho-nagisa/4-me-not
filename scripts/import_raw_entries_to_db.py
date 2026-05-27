from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy.orm import Session

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.account_context import (  # noqa: E402
    reset_current_account_id,
    set_current_account_id,
)
from backend.db.session import SessionLocal  # noqa: E402
from backend.models.account.account import Account  # noqa: E402
from backend.models.base.enums import InteractionType, ShareLevel  # noqa: E402
from backend.models.interaction.interaction import Interaction  # noqa: E402
from backend.models.person.person import Person  # noqa: E402
from backend.models.search.search_document import SearchDocument  # noqa: E402
from backend.services.auth_service import AuthService  # noqa: E402
from backend.services.search import SearchService  # noqa: E402
from scripts.parse_raw_entry_import import (  # noqa: E402
    ParseIssue,
    parse_raw_entry_text,
)


DEFAULT_ACCOUNT_EMAIL = "debug@samples"
DEFAULT_PERSON_NAME = "取り込みメモ"
DEFAULT_PERSON_CANONICAL_NAME = "__raw_entry_import__"
JST = timezone(timedelta(hours=9))


@dataclass
class ImportResult:
    account_email: str
    account_id: UUID
    person_name: str
    person_id: UUID
    parsed_count: int
    inserted_count: int
    skipped_count: int
    issue_count: int
    indexed_counts: dict[str, int] | None = None


class RawEntryParseError(ValueError):
    def __init__(self, issues: list[ParseIssue]) -> None:
        super().__init__(f"{len(issues)} parse issue(s) found")
        self.issues = issues


def import_raw_entries(
    input_path: Path,
    account_email: str = DEFAULT_ACCOUNT_EMAIL,
    person_name: str = DEFAULT_PERSON_NAME,
    person_canonical_name: str = DEFAULT_PERSON_CANONICAL_NAME,
    password: str | None = None,
    replace: bool = False,
    allow_duplicates: bool = False,
    rebuild_index: bool = True,
    strict: bool = False,
) -> tuple[ImportResult, list[ParseIssue]]:
    entries, issues = parse_raw_entry_text(input_path.read_text(encoding="utf-8"))
    if strict and issues:
        raise RawEntryParseError(issues)

    db: Session = SessionLocal()
    try:
        account = _get_or_create_account(db, account_email, password)
        person = _get_or_create_import_person(
            db=db,
            account_id=account.id,
            name=person_name,
            canonical_name=person_canonical_name,
        )

        if replace:
            _delete_existing_imported_interactions(db, account.id, person.id)

        inserted_count = 0
        skipped_count = 0
        for entry in entries:
            occurred_at = _entry_datetime(entry.captured_date)
            if (
                not allow_duplicates
                and _interaction_exists(
                    db=db,
                    account_id=account.id,
                    person_id=person.id,
                    occurred_at=occurred_at,
                    content=entry.raw_text,
                )
            ):
                skipped_count += 1
                continue

            db.add(
                Interaction(
                    account_id=account.id,
                    person_id=person.id,
                    type=InteractionType.EVENT,
                    share_level=ShareLevel.WITHHELD,
                    occurred_at=occurred_at,
                    content=entry.raw_text,
                    note=None,
                )
            )
            inserted_count += 1

        db.commit()
        account_id = account.id
        person_id = person.id
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    indexed_counts = None
    if rebuild_index:
        token = set_current_account_id(account_id)
        try:
            indexed_counts = SearchService().rebuild_account_index()
        finally:
            reset_current_account_id(token)

    return (
        ImportResult(
            account_email=account_email,
            account_id=account_id,
            person_name=person_name,
            person_id=person_id,
            parsed_count=len(entries),
            inserted_count=inserted_count,
            skipped_count=skipped_count,
            issue_count=len(issues),
            indexed_counts=indexed_counts,
        ),
        issues,
    )


def _get_or_create_account(
    db: Session,
    email: str,
    password: str | None,
) -> Account:
    normalized_email = email.strip().lower()
    if not normalized_email or "@" not in normalized_email:
        raise ValueError("Account email is invalid")

    account = db.query(Account).filter(Account.email == normalized_email).first()
    if account is not None:
        if password:
            account.password_hash = AuthService().hash_password(password)
            account.is_active = True
        return account

    account = Account(
        email=normalized_email,
        password_hash=AuthService().hash_password(password) if password else None,
        is_active=True,
    )
    db.add(account)
    db.flush()
    return account


def _get_or_create_import_person(
    db: Session,
    account_id: UUID,
    name: str,
    canonical_name: str,
) -> Person:
    person = (
        db.query(Person)
        .filter(
            Person.account_id == account_id,
            Person.canonical_name == canonical_name,
        )
        .first()
    )
    if person is not None:
        person.name = name.strip() or DEFAULT_PERSON_NAME
        person.is_hidden = False
        return person

    person = Person(
        account_id=account_id,
        name=name.strip() or DEFAULT_PERSON_NAME,
        canonical_name=canonical_name,
        description="RawEntry text import placeholder",
        is_hidden=False,
    )
    db.add(person)
    db.flush()
    return person


def _delete_existing_imported_interactions(
    db: Session,
    account_id: UUID,
    person_id: UUID,
) -> None:
    interaction_ids = [
        row[0]
        for row in db.query(Interaction.id)
        .filter(
            Interaction.account_id == account_id,
            Interaction.person_id == person_id,
        )
        .all()
    ]
    if not interaction_ids:
        return

    db.execute(
        sa_delete(SearchDocument).where(
            SearchDocument.account_id == account_id,
            SearchDocument.target_type == "interaction",
            SearchDocument.target_id.in_(interaction_ids),
        )
    )
    db.execute(
        sa_delete(Interaction).where(
            Interaction.account_id == account_id,
            Interaction.id.in_(interaction_ids),
        )
    )


def _interaction_exists(
    db: Session,
    account_id: UUID,
    person_id: UUID,
    occurred_at: datetime,
    content: str,
) -> bool:
    return (
        db.query(Interaction.id)
        .filter(
            Interaction.account_id == account_id,
            Interaction.person_id == person_id,
            Interaction.occurred_at == occurred_at,
            Interaction.content == content,
        )
        .first()
        is not None
    )


def _entry_datetime(captured_date: str | None) -> datetime:
    entry_date = date.fromisoformat(captured_date) if captured_date else date.today()
    return datetime.combine(entry_date, time(hour=12), tzinfo=JST)


def _print_result(result: ImportResult, issues: list[ParseIssue]) -> None:
    print(f"account: {result.account_email} ({result.account_id})")
    print(f"person: {result.person_name} ({result.person_id})")
    print(f"parsed entries: {result.parsed_count}")
    print(f"inserted interactions: {result.inserted_count}")
    print(f"skipped duplicates: {result.skipped_count}")
    print(f"parse issues: {result.issue_count}")
    if issues:
        print("issues:")
        for issue in issues[:20]:
            print(f"- entry {issue.source_index}: {issue.message}")
        if len(issues) > 20:
            print(f"- ... {len(issues) - 20} more")
    if result.indexed_counts is not None:
        print("search index:")
        for key, value in result.indexed_counts.items():
            print(f"- {key}: {value}")


def _print_parse_preview(input_path: Path, strict: bool = False) -> None:
    entries, issues = parse_raw_entry_text(input_path.read_text(encoding="utf-8"))
    print(f"parsed entries: {len(entries)}")
    print(f"parse issues: {len(issues)}")
    if issues:
        print("issues:")
        for issue in issues[:20]:
            print(f"- entry {issue.source_index}: {issue.message}")
        if len(issues) > 20:
            print(f"- ... {len(issues) - 20} more")
    if strict and issues:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import RawEntry text blocks into the database as interactions."
    )
    parser.add_argument("input", help="RawEntry text file path.")
    parser.add_argument(
        "--account-email",
        default=DEFAULT_ACCOUNT_EMAIL,
        help=f"Target account email. Defaults to {DEFAULT_ACCOUNT_EMAIL}.",
    )
    parser.add_argument(
        "--password",
        help="Optional password to set when creating/updating the target account.",
    )
    parser.add_argument(
        "--person-name",
        default=DEFAULT_PERSON_NAME,
        help=f"Placeholder person name. Defaults to {DEFAULT_PERSON_NAME}.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing interactions for the placeholder person before import.",
    )
    parser.add_argument(
        "--allow-duplicates",
        action="store_true",
        help="Insert exact duplicate entries instead of skipping them.",
    )
    parser.add_argument(
        "--skip-index",
        action="store_true",
        help="Skip rebuilding the account search index after import.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and report counts without writing to the database.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 when parse issues are found.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if args.dry_run:
        _print_parse_preview(input_path, strict=args.strict)
        return

    try:
        result, issues = import_raw_entries(
            input_path=input_path,
            account_email=args.account_email,
            person_name=args.person_name,
            password=args.password,
            replace=args.replace,
            allow_duplicates=args.allow_duplicates,
            rebuild_index=not args.skip_index,
            strict=args.strict,
        )
    except RawEntryParseError as exc:
        _print_parse_preview(input_path, strict=False)
        raise SystemExit(1) from exc

    _print_result(result, issues)


if __name__ == "__main__":
    main()
