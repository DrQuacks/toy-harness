from pathlib import Path
import time
import json
import re
import argparse
from model_client import ask_model, ask_model_stream
from runner import run_command
from workspace import create_workspace, read_workspace_files


def build_prompt(
    task_prompt: str,
    files: dict[str, str],
    editable_paths: list[str],
    read_only_paths: list[str],
    last_error: str | None = None,
) -> str:
    file_sections = []

    for path, content in files.items():
        file_sections.append(
            f"File: {path}\n"
            f"----- BEGIN FILE -----\n"
            f"{content}\n"
            f"----- END FILE -----"
        )

    error_section = ""
    if last_error:
        error_section = (
            "\nThe previous attempt failed with this output:\n"
            "----- BEGIN ERROR -----\n"
            f"{last_error}\n"
            "----- END ERROR -----\n"
        )

    return (
        "You are editing code inside a small programming task.\n\n"
        f"Task:\n{task_prompt}\n\n"
        "Current files:\n"
        f"{chr(10).join(file_sections)}\n"
        f"{error_section}\n\n"
        "Return a JSON object describing the file edits needed to make the task pass.\n"
        "Editable paths:\n"
        f"{json.dumps(editable_paths, indent=2)}\n\n"
        "Read-only paths (DO NOT EDIT):\n"
        f"{json.dumps(read_only_paths, indent=2)}\n\n"
        "You may read all files, but you may only modify files listed in editable_paths.\n"
        "Never modify read_only_paths.\n"
        "Use this exact format:\n"
        '{ "edits": [ { "path": "main.py", "content": "full file contents here" } ] }\n'
        "Return ONLY valid JSON.\n"
        "Do not include markdown fences.\n"
        "Do not explain your answer.\n"
    )

def load_task_config(task_dir: Path) -> dict:
    config_path = task_dir / "task.json"

    if not config_path.exists():
        raise FileNotFoundError(f"Missing task config: {config_path}")

    return json.loads(config_path.read_text())


def extract_json_object(output: str) -> dict:
    output = output.strip()

    if output.startswith("```"):
        output = re.sub(r"^```(?:json)?\s*", "", output)
        output = re.sub(r"\s*```$", "", output)

    start = output.find("{")
    end = output.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("Model output did not contain a JSON object.")

    json_text = output[start : end + 1]
    return json.loads(json_text)

def resolve_safe_path(workspace_dir: Path, relative_path: str) -> Path:
    target_path = (workspace_dir / relative_path).resolve()
    workspace_root = workspace_dir.resolve()

    if not target_path.is_relative_to(workspace_root):
        raise ValueError(f"Unsafe edit path outside workspace: {relative_path}")

    return target_path

def is_allowed_edit_path(path: str, editable_paths: list[str]) -> bool:
    normalized = path.strip("/")

    for allowed in editable_paths:
        allowed = allowed.strip("/")

        if normalized == allowed:
            return True

        if allowed.endswith("/") and normalized.startswith(allowed):
            return True

    return False

def apply_edits(workspace_dir: Path, edits: list[dict], editable_paths: list[str]) -> None:
    for edit in edits:
        path = edit["path"]
        content = edit["content"]

        if not is_allowed_edit_path(path, editable_paths):
            raise ValueError(f"Model tried to edit disallowed path: {path}")

        target_path = resolve_safe_path(workspace_dir, path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content)


def save_artifact(workspace_dir: Path, filename: str, content: str) -> None:
    attempts_dir = workspace_dir / ".attempts"
    attempts_dir.mkdir(exist_ok=True)

    output_file = attempts_dir / filename
    output_file.write_text(content)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--task",
        required=True,
        help="Task folder name inside tasks/",
    )
    parser.add_argument(
        "--model",
        default="qwen2.5-coder:7b",
        help="Ollama model name",
    )
    parser.add_argument(
        "--workspace-root",
        default="workspace",
        help="Directory where task workspaces are created",
    )

    return parser.parse_args()

def save_run_summary(workspace_dir: Path, summary: dict) -> None:
    summary_path = workspace_dir / "run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")


def main() -> None:
    args = parse_args()

    task_dir = Path("tasks") / args.task
    workspace_dir = Path(args.workspace_root) / args.task
    model = args.model

    config = load_task_config(task_dir)

    prompt_file = config["prompt_file"]
    validation_command = config["validation_command"]
    editable_paths = config["editable_paths"]
    read_only_paths = config.get("read_only_paths", [])
    max_attempts = config.get("max_attempts", 5)
    timeout_seconds = config.get("timeout_seconds", 10)

    create_workspace(task_dir, workspace_dir)

    task_prompt = (task_dir / prompt_file).read_text()
    last_error = None

    run_start = time.time()

    for attempt in range(1, max_attempts + 1):
        print(f"\n=== ATTEMPT {attempt} ===")

        print("Reading workspace files...")
        included_paths = editable_paths + read_only_paths
        files = read_workspace_files(workspace_dir, included_paths)
        print("Building prompt...")
        prompt = build_prompt(task_prompt, files, editable_paths, read_only_paths, last_error)
        save_artifact(workspace_dir, f"attempt_{attempt}_prompt.txt", prompt)

        print(f"Prompt size: {len(prompt)} characters")

        print("Asking model...")
        start = time.time()
        # raw_model_output = ask_model(prompt)
        chunks = []

        for chunk in ask_model_stream(prompt,model=model):
            print(chunk, end="", flush=True)
            chunks.append(chunk)

        print()

        raw_model_output = "".join(chunks)
        save_artifact(workspace_dir, f"attempt_{attempt}_model_output.txt", raw_model_output)
        elapsed = time.time() - start
        print(f"Model responded in {elapsed:.2f}s")

        print("Parsing model edit JSON...")
        edit_plan = extract_json_object(raw_model_output)

        save_artifact(
            workspace_dir,
            f"attempt_{attempt}_edit_plan.json",
            json.dumps(edit_plan, indent=2),
        )

        edits = edit_plan.get("edits", [])

        if not edits:
            raise ValueError("Model returned no edits.")

        print("Applying edits...")
        for edit in edits:
            print(f"- {edit['path']}")

        apply_edits(workspace_dir, edits, editable_paths)

        print("\n=== MODEL EDIT PLAN ===")
        print(json.dumps(edit_plan, indent=2))

        print("\n=== MODEL FILE OUTPUTS ===")
        for edit in edits:
            print(f"\n--- FILE: {edit['path']} ---")
            print(edit["content"])

        print("\n=== RUNNING VALIDATION ===")
        start = time.time()
        result = run_command(
            validation_command,
            cwd=workspace_dir,
            timeout_seconds=timeout_seconds,
        )
        elapsed = time.time() - start
        print(f"Validation finished in {elapsed:.2f}s")

        validation_log = (
            f"Passed: {result.ok}\n"
            f"Exit code: {result.exit_code}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}\n"
        )

        save_artifact(workspace_dir, f"attempt_{attempt}_validation.txt", validation_log)

        if result.ok:
            total_duration = time.time() - run_start

            save_run_summary(
                workspace_dir,
                {
                    "task": args.task,
                    "model": model,
                    "passed": True,
                    "attempts_used": attempt,
                    "total_duration_seconds": round(total_duration, 2),
                    "validation_command": validation_command,
                },
            )
            print("✅ Passed!")
            return

        combined_output = (
            f"Exit code: {result.exit_code}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}\n"
        )

        print("❌ Failed.")
        print(combined_output)

        last_error = combined_output

    total_duration = time.time() - run_start

    save_run_summary(
        workspace_dir,
        {
            "task": args.task,
            "model": model,
            "passed": False,
            "attempts_used": max_attempts,
            "total_duration_seconds": round(total_duration, 2),
            "validation_command": validation_command,
        },
    )

    print("Failed after max attempts.")


if __name__ == "__main__":
    main()