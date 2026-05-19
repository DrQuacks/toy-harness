import argparse
import json
from pathlib import Path

from model_client import ask_model_stream
from runner import run_command
from workspace import create_workspace


MAX_STEPS = 10


def load_task(task_name: str) -> tuple[Path, dict]:
    task_dir = Path("tasks") / task_name

    if not task_dir.exists():
        raise ValueError(f"Task does not exist: {task_name}")

    config_path = task_dir / "task.json"

    config = json.loads(config_path.read_text())

    return task_dir, config


def read_file(workspace_dir: Path, path: str) -> str:
    target = workspace_dir / path

    if not target.exists():
        return f"ERROR: File does not exist: {path}"

    return target.read_text()


def write_file(
    workspace_dir: Path,
    path: str,
    content: str,
    editable_paths: list[str],
) -> str:
    if path not in editable_paths:
        return f"ERROR: Cannot edit non-editable path: {path}"

    target = workspace_dir / path
    target.write_text(content)

    return f"Wrote file: {path}"


def run_tests(
    workspace_dir: Path,
    validation_command: list[str],
    timeout_seconds: int,
) -> str:
    result = run_command(
        validation_command,
        cwd=workspace_dir,
        timeout_seconds=timeout_seconds,
    )

    output = []

    output.append(f"Passed: {result.ok}")
    output.append(f"Exit code: {result.exit_code}")

    if result.stdout:
        output.append("\nSTDOUT:\n")
        output.append(result.stdout)

    if result.stderr:
        output.append("\nSTDERR:\n")
        output.append(result.stderr)

    return "\n".join(output)


def build_prompt(
    history: list[dict],
    editable_paths: list[str],
) -> str:
    return f"""
You are an AI coding agent.

You may use these actions:

1. read_file
2. write_file
3. run_tests
4. finish

Editable paths:
{json.dumps(editable_paths, indent=2)}

Return ONLY valid JSON.

Action schemas:

Read file:
{{
  "action": "read_file",
  "path": "sales_summary.py"
}}

Write file:
{{
  "action": "write_file",
  "path": "sales_summary.py",
  "content": "full file contents here"
}}

Run tests:
{{
  "action": "run_tests"
}}

Finish:
{{
  "action": "finish"
}}

Previous history:
{json.dumps(history, indent=2)}
"""


def ask_agent(prompt: str, model: str) -> dict:
    chunks = []

    for chunk in ask_model_stream(prompt, model=model):
        print(chunk, end="", flush=True)
        chunks.append(chunk)

    print()

    raw_output = "".join(chunks)

    start = raw_output.find("{")
    end = raw_output.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("Model did not return JSON.")

    return json.loads(raw_output[start : end + 1])


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--task", required=True)

    parser.add_argument(
        "--model",
        default="qwen2.5-coder:3b",
    )

    args = parser.parse_args()

    task_dir, config = load_task(args.task)

    workspace_dir = Path("workspace") / args.task

    create_workspace(task_dir, workspace_dir)

    editable_paths = config["editable_paths"]
    validation_command = config["validation_command"]
    timeout_seconds = config["timeout_seconds"]

    history = []

    for step in range(MAX_STEPS):
        print(f"\n=== STEP {step + 1} ===")

        prompt = build_prompt(
            history,
            editable_paths,
        )

        command = ask_agent(prompt, args.model)

        print("\nParsed command:")
        print(json.dumps(command, indent=2))

        action = command.get("action")

        if action == "read_file":
            observation = read_file(
                workspace_dir,
                command["path"],
            )

        elif action == "write_file":
            observation = write_file(
                workspace_dir,
                command["path"],
                command["content"],
                editable_paths,
            )

        elif action == "run_tests":
            observation = run_tests(
                workspace_dir,
                validation_command,
                timeout_seconds,
            )

        elif action == "finish":
            print("Agent finished.")
            break

        else:
            observation = f"Unknown action: {action}"

        print("\nObservation:")
        print(observation)

        history.append(
            {
                "command": command,
                "observation": observation,
            }
        )


if __name__ == "__main__":
    main()