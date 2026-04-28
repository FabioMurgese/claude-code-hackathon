import json
import sys
from src.agent.coordinator import process_claim


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "ingest":
        print("Usage: python -m src.agent ingest <claim_id>", file=sys.stderr)
        sys.exit(1)
    result = process_claim(sys.argv[2])
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
