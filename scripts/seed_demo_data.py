import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.testing.demo_data import DEFAULT_PREFIX, cleanup_demo_data, seed_demo_data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Insert demo data for local UI checks, or remove it."
    )
    parser.add_argument(
        "--prefix",
        default=DEFAULT_PREFIX,
        help="Marker used to identify demo records for cleanup.",
    )
    parser.add_argument(
        "--clear-only",
        action="store_true",
        help="Remove existing demo data for the given prefix without inserting new rows.",
    )
    args = parser.parse_args()

    if args.clear_only:
        cleanup_demo_data(args.prefix)
        print(f"Removed demo data for prefix: {args.prefix}")
        return

    result = seed_demo_data(args.prefix)
    print("Demo data inserted successfully.")
    print(f"prefix: {result.prefix}")
    print(f"communities: {result.community_count}")
    print(f"topics: {result.topic_count}")
    print(f"persons: {result.person_count}")
    print(f"interactions: {result.interaction_count}")


if __name__ == "__main__":
    main()
