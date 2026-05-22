import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.services.search import SearchService


def main() -> None:
    result = SearchService().rebuild_account_index()
    print("Search index rebuilt successfully.")
    print(f"people: {result['people']}")
    print(f"communities: {result['communities']}")
    print(f"topics: {result['topics']}")
    print(f"interactions: {result['interactions']}")
    print(f"tasks: {result.get('tasks', 0)}")
    print(f"calendar_events: {result.get('calendar_events', 0)}")


if __name__ == "__main__":
    main()
