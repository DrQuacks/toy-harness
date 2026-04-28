from pathlib import Path

from runner import run_command
from workspace import create_workspace, read_workspace_files


def main() -> None:
    task_dir = Path("tasks/task1")
    workspace_dir = Path("workspace/task1")

    create_workspace(task_dir, workspace_dir)

    prompt = (task_dir / "prompt.txt").read_text()
    files = read_workspace_files(workspace_dir)

    print("=== TASK PROMPT ===")
    print(prompt)

    print("\n=== FILES ===")
    for path, content in files.items():
        print(f"\n--- {path} ---")
        print(content)

    print("\n=== RUNNING VALIDATION ===")
    result = run_command(["bash", "run.sh"], cwd=workspace_dir)

    print(f"Passed: {result.ok}")
    print(f"Exit code: {result.exit_code}")

    if result.stdout:
        print("\nSTDOUT:")
        print(result.stdout)

    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr)


if __name__ == "__main__":
    main()