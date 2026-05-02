from pathlib import Path
import time
import json
import re
from model_client import ask_model, ask_model_stream
from runner import run_command
from workspace import create_workspace, read_workspace_files


def build_prompt(
    task_prompt: str,
    files: dict[str, str],
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
        "Use this exact format:\n"
        '{ "edits": [ { "path": "main.py", "content": "full file contents here" } ] }\n'
        "Return ONLY valid JSON.\n"
        "Do not include markdown fences.\n"
        "Do not explain your answer.\n"
    )


# def clean_model_output(output: str) -> str:
#     output = output.strip()

#     if output.startswith("```"):
#         lines = output.splitlines()

#         if lines and lines[0].startswith("```"):
#             lines = lines[1:]

#         if lines and lines[-1].startswith("```"):
#             lines = lines[:-1]

#         output = "\n".join(lines).strip()

#     return output + "\n"

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

def apply_edits(workspace_dir: Path, edits: list[dict]) -> None:
    for edit in edits:
        path = edit["path"]
        content = edit["content"]

        target_path = workspace_dir / path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content)


def save_artifact(workspace_dir: Path, filename: str, content: str) -> None:
    attempts_dir = workspace_dir / ".attempts"
    attempts_dir.mkdir(exist_ok=True)

    output_file = attempts_dir / filename
    output_file.write_text(content)


def main() -> None:
    task_dir = Path("tasks/task1")
    workspace_dir = Path("workspace/task1")

    create_workspace(task_dir, workspace_dir)

    task_prompt = (task_dir / "prompt.txt").read_text()
    last_error = None

    for attempt in range(1, 6):
        print(f"\n=== ATTEMPT {attempt} ===")

        print("Reading workspace files...")
        files = read_workspace_files(workspace_dir)

        print("Building prompt...")
        prompt = build_prompt(task_prompt, files, last_error)
        save_artifact(workspace_dir, f"attempt_{attempt}_prompt.txt", prompt)

        print(f"Prompt size: {len(prompt)} characters")

        print("Asking model...")
        start = time.time()
        # raw_model_output = ask_model(prompt)
        chunks = []

        for chunk in ask_model_stream(prompt):
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

        apply_edits(workspace_dir, edits)

        print("\n=== MODEL EDIT PLAN ===")
        print(json.dumps(edit_plan, indent=2))

        print("\n=== MODEL FILE OUTPUTS ===")
        for edit in edits:
            print(f"\n--- FILE: {edit['path']} ---")
            print(edit["content"])

        print("\n=== RUNNING VALIDATION ===")
        start = time.time()
        result = run_command(["bash", "run.sh"], cwd=workspace_dir)
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

    print("Failed after max attempts.")


if __name__ == "__main__":
    main()