from pathlib import Path
import time
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
        "Rewrite the file main.py so the task passes.\n"
        "Return ONLY the full contents of main.py.\n"
        "Do not include markdown fences.\n"
        "Do not explain your answer.\n"
    )


def clean_model_output(output: str) -> str:
    output = output.strip()

    if output.startswith("```"):
        lines = output.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]

        output = "\n".join(lines).strip()

    return output + "\n"


def save_attempt(workspace_dir: Path, attempt: int, content: str) -> None:
    attempts_dir = workspace_dir / ".attempts"
    attempts_dir.mkdir(exist_ok=True)

    attempt_file = attempts_dir / f"attempt_{attempt}_main.py"
    attempt_file.write_text(content)


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
        elapsed = time.time() - start
        print(f"Model responded in {elapsed:.2f}s")

        print("Cleaning model output...")
        new_main_py = clean_model_output(raw_model_output)

        print("Saving attempt...")
        save_attempt(workspace_dir, attempt, new_main_py)

        print("Writing main.py...")
        target_file = workspace_dir / "main.py"
        target_file.write_text(new_main_py)

        print("\n=== MODEL WROTE main.py ===")
        print(new_main_py)

        print("\n=== RUNNING VALIDATION ===")
        start = time.time()
        result = run_command(["bash", "run.sh"], cwd=workspace_dir)
        elapsed = time.time() - start
        print(f"Validation finished in {elapsed:.2f}s")

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