import argparse
import json
import subprocess
from pathlib import Path


def run_harness(task: str, model: str, workspace_root: str) -> dict:
    command = [
        "python",
        "harness.py",
        "--task",
        task,
        "--model",
        model,
        "--workspace-root",
        workspace_root,
    ]

    print(f"\n=== Running {task} with {model} ===")

    completed = subprocess.run(
        command,
        text=True,
        capture_output=True,
    )

    workspace_dir = Path(workspace_root) / task
    summary_path = workspace_dir / "run_summary.json"

    if not summary_path.exists():
        return {
            "task": task,
            "model": model,
            "passed": False,
            "attempts_used": None,
            "total_duration_seconds": None,
            "error": "Missing run_summary.json",
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }

    summary = json.loads(summary_path.read_text())
    summary["harness_exit_code"] = completed.returncode

    return summary


def save_benchmark_results(results: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2) + "\n")


def print_results_table(results: list[dict]) -> None:
    print("\n=== Benchmark Results ===")
    print(f"{'Model':30} {'Passed':8} {'Attempts':10} {'Seconds':10}")
    print("-" * 65)

    for result in results:
        print(
            f"{result.get('model', ''):30} "
            f"{str(result.get('passed', False)):8} "
            f"{str(result.get('attempts_used', '')):10} "
            f"{str(result.get('total_duration_seconds', '')):10}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--task",
        required=True,
        help="Task folder name inside tasks/",
    )

    parser.add_argument(
        "--models",
        nargs="+",
        required=True,
        help="One or more Ollama model names",
    )

    parser.add_argument(
        "--workspace-root",
        default="workspace",
    )

    parser.add_argument(
        "--output",
        default="benchmarks/latest.json",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    results = []

    for model in args.models:
        result = run_harness(
            task=args.task,
            model=model,
            workspace_root=args.workspace_root,
        )
        results.append(result)

    output_path = Path(args.output)
    save_benchmark_results(results, output_path)
    print_results_table(results)

    print(f"\nSaved benchmark results to: {output_path}")


if __name__ == "__main__":
    main()