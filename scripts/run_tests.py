import argparse
import os
from pathlib import Path
import subprocess
import sys
import unittest
from urllib.parse import quote


BASE_DIR = Path(__file__).resolve().parents[1]


class StopAfterSuccessesResult(unittest.TextTestResult):
    def __init__(
        self,
        stream,
        descriptions,
        verbosity,
        stop_after_successes: int | None = None,
    ):
        super().__init__(stream, descriptions, verbosity)
        self.stop_after_successes = stop_after_successes
        self.success_count = 0

    def addSuccess(self, test):
        super().addSuccess(test)
        self.success_count += 1
        if self.stop_after_successes and self.success_count >= self.stop_after_successes:
            self.stream.writeln(
                f"Stopped after {self.success_count} successful tests."
            )
            self.stop()


class ConfigurableTextTestRunner(unittest.TextTestRunner):
    def __init__(self, *args, stop_after_successes: int | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.stop_after_successes = stop_after_successes

    def _makeResult(self):
        result = StopAfterSuccessesResult(
            self.stream,
            self.descriptions,
            self.verbosity,
            self.stop_after_successes,
        )
        result.failfast = self.failfast
        result.buffer = self.buffer
        result.tb_locals = self.tb_locals
        return result


def read_dotenv() -> dict[str, str]:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        value = value.strip().strip('"').strip("'")
        values[key.strip()] = value
    return values


def env_value(dotenv: dict[str, str], key: str, default: str) -> str:
    return os.environ.get(key) or dotenv.get(key) or default


def build_local_database_url() -> str:
    dotenv = read_dotenv()
    user = env_value(dotenv, "POSTGRES_USER", "forme_not")
    password = env_value(dotenv, "POSTGRES_PASSWORD", "forme_not")
    database = env_value(dotenv, "POSTGRES_DB", "forme_not")
    port = env_value(dotenv, "POSTGRES_PORT", "5432")

    return (
        "postgresql://"
        f"{quote(user, safe='')}:{quote(password, safe='')}"
        f"@127.0.0.1:{port}/{quote(database, safe='')}"
    )


def cleanup_test_records() -> None:
    from tests.test_support import cleanup_test_data

    cleanup_test_data("[TEST:")


def configure_database(args: argparse.Namespace) -> None:
    database_url = args.db_url
    if args.local_db:
        database_url = build_local_database_url()

    if not database_url:
        return

    os.environ["DB_URL"] = database_url
    os.environ["DATABASE_URL"] = database_url


def run_migrations() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the backend unittest suite.")
    parser.add_argument(
        "-s",
        "--start-dir",
        default="tests",
        help="Directory to discover tests from. Defaults to tests.",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        default="test*.py",
        help="Test filename pattern. Defaults to test*.py.",
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        type=int,
        default=2,
        help="unittest verbosity. Defaults to 2.",
    )
    parser.add_argument(
        "--skip-cleanup",
        action="store_true",
        help="Skip cleanup of generated [TEST:] records before and after the run.",
    )
    parser.add_argument(
        "--local-db",
        action="store_true",
        help=(
            "Run against local Docker PostgreSQL using POSTGRES_* values from .env."
        ),
    )
    parser.add_argument(
        "--db-url",
        help="Override DB_URL/DATABASE_URL for this test run without editing .env.",
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Run alembic upgrade head before test discovery.",
    )
    parser.add_argument(
        "--stop-after-successes",
        type=int,
        help="Stop the run after this many successful tests.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_database(args)

    if args.migrate:
        run_migrations()

    if not args.skip_cleanup:
        cleanup_test_records()

    suite = unittest.defaultTestLoader.discover(
        start_dir=args.start_dir,
        pattern=args.pattern,
    )
    result = ConfigurableTextTestRunner(
        verbosity=args.verbosity,
        stop_after_successes=args.stop_after_successes,
    ).run(suite)

    if not args.skip_cleanup:
        cleanup_test_records()

    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
