import argparse
import json
from pathlib import Path


def slugify(name: str) -> str:
    return name.strip().lower().replace(" ", "-")


def create_task(task_name: str) -> None:
    task_slug = slugify(task_name)
    task_dir = Path("tasks") / task_slug

    if task_dir.exists():
        raise FileExistsError(f"Task already exists: {task_dir}")

    initial_dir = task_dir / "initial"
    initial_dir.mkdir(parents=True)

    task_config = {
        "prompt_file": "prompt.txt",
        "validation_command": ["bash", "run.sh"],
        "editable_paths": ["main.py"],
        "max_attempts": 5,
        "timeout_seconds": 10,
    }

    (task_dir / "task.json").write_text(
        json.dumps(task_config, indent=2) + "\n"
    )

    (task_dir / "prompt.txt").write_text(
        "Describe what the model should change.\n"
    )

    (task_dir / "run.sh").write_text(
        "#!/usr/bin/env bash\n"
        "set -e\n\n"
        "# Replace this with your validation command.\n"
        "python main.py\n"
    )

    (initial_dir / "main.py").write_text(
        'print("TODO: implement task")\n'
    )

    print(f"Created task: {task_dir}")
    print("Next steps:")
    print(f"  1. Edit {task_dir / 'prompt.txt'}")
    print(f"  2. Edit {task_dir / 'initial' / 'main.py'}")
    print(f"  3. Edit {task_dir / 'run.sh'}")
    print(f"  4. Run: chmod +x {task_dir / 'run.sh'}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="Name of the task to create")

    args = parser.parse_args()
    create_task(args.name)


if __name__ == "__main__":
    main()