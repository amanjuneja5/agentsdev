import json
import shelve
import sys
from datetime import datetime
from config  import Config
from checker import run_checks


def load_snapshot(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def save_report(report, path: str = "k8s_reports"):
    key = f"{report.cluster_id}:{datetime.now().isoformat(timespec='seconds')}"
    with shelve.open(path) as db:
        db[key] = report
    print(f"Saved: {key}")


def print_report(report):
    if not report:
        print("No issues found — cluster looks healthy.")
        return

    print(f"\n{'='*55}")
    print(f"  Cluster Report: {report.cluster_id}")
    print(f"{'='*55}")

    for finding in report:
        print(f"  {finding}")

    print(f"{'='*55}")
    print(f"  {report}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <snapshot.json>")
        sys.exit(1)

    config = Config.from_env()

    # if not config.is_valid():
    #     print("Error: ANTHROPIC_API_KEY not set.")
    #     sys.exit(1)

    snapshot = load_snapshot(sys.argv[1])
    report   = run_checks(snapshot, config)

    print_report(report)

    if report:
        save_report(report)