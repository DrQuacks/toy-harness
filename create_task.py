import argparse
import json
import os
from pathlib import Path


def slugify(name: str) -> str:
    return name.strip().lower().replace(" ", "-")


def create_task(args: argparse.Namespace) -> None:
    task_slug = args.slug or slugify(args.name)
    task_dir = Path("tasks") / task_slug

    if task_dir.exists():
        raise FileExistsError(f"Task already exists: {task_dir}")

    initial_dir = task_dir / "initial"
    initial_dir.mkdir(parents=True)

    task_config = {
        "prompt_file": "prompt.txt",
        "validation_command": args.validation_command,
        "editable_paths": args.editable,
        "read_only_paths": args.read_only,
        "max_attempts": args.max_attempts,
        "timeout_seconds": args.timeout_seconds,
    }

    (task_dir / "task.json").write_text(
        json.dumps(task_config, indent=2) + "\n"
    )

    (task_dir / "prompt.txt").write_text(args.prompt + "\n")

    run_sh_path = task_dir / "run.sh"
    run_sh_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -e\n\n"
        "# Optional validation script. The harness uses task.json by default.\n"
        f"{' '.join(args.validation_command)}\n"
    )
    os.chmod(run_sh_path, 0o755)

    initial_file_path = initial_dir / args.initial_file
    initial_file_path.parent.mkdir(parents=True, exist_ok=True)
    initial_file_path.write_text(args.initial_content + "\n")

    print(f"Created task: {task_dir}")
    print()
    print("Generated:")
    print(f"  {task_dir / 'task.json'}")
    print(f"  {task_dir / 'prompt.txt'}")
    print(f"  {task_dir / 'run.sh'}")
    print(f"  {initial_file_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="Human-readable task name")

    parser.add_argument(
        "--slug",
        help="Optional folder name override",
    )

    parser.add_argument(
        "--editable",
        nargs="+",
        default=["main.py"],
        help="Editable file paths or directories",
    )

    parser.add_argument(
        "--validation-command",
        nargs="+",
        default=["python", "-m", "pytest"],
        help="Command used by the harness to validate the task",
    )

    parser.add_argument(
        "--prompt",
        default="Describe what the model should change.",
        help="Initial task prompt",
    )

    parser.add_argument(
        "--initial-file",
        default="main.py",
        help="Initial file path inside initial/",
    )

    parser.add_argument(
        "--initial-content",
        default='print("TODO: implement task")',
        help="Initial contents for the generated file",
    )

    parser.add_argument(
        "--max-attempts",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--read-only",
        nargs="+",
        default=[],
        help="Paths that the model can read but not edit",
    )

    args = parser.parse_args()
    if args.validation_command == ["pytest"]:
        args.validation_command = ["python", "-m", "pytest"]
    create_task(args)


if __name__ == "__main__":
    main()