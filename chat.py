import json
import subprocess
import time
from pathlib import Path

from model_client import ask_model_stream
from hardware import get_default_models


def list_tasks() -> list[str]:
    tasks_dir = Path("tasks")

    if not tasks_dir.exists():
        return []

    return sorted(
        path.name
        for path in tasks_dir.iterdir()
        if path.is_dir()
    )


def build_router_prompt(user_text: str) -> str:
    tasks = list_tasks()

    return f"""
You are a command router for a local AI code harness.

Available tasks:
{json.dumps(tasks, indent=2)}

Available actions:
1. run_task
2. show_tasks
3. create_task
3. unknown

Return ONLY valid JSON.

Schema:
{
  "action": "run_task" | "show_tasks" | "create_task" | "unknown",
  "task": string | null,
  "model": string | null,
  "prompt": string | null,
  "initial_file": string | null,
  "initial_content": string | null,
  "editable_paths": list[string] | null,
  "read_only_paths": list[string] | null
}

Rules:
- If the user asks to run, execute, try, or test a task, use action "run_task".
- The task must be one of the available tasks.
- If the user mentions 3b, use model "qwen2.5-coder:3b".
- If the user mentions 7b, use model "qwen2.5-coder:7b".
- If no model is mentioned, use model "qwen2.5-coder:7b".
- If the user asks what tasks exist, use action "show_tasks".
- If the user asks to create, make, scaffold, or generate a new task, use action "create_task".
- For create_task, "task" should be a short slug-like task name, e.g. "string-utils".
- If no initial file is specified, use "main.py".
- If no editable paths are specified, use the initial file.
- If no read-only paths are specified, use [].
- If you cannot determine the task, use action "unknown".

User request:
{user_text}
"""


def parse_router_json(output: str) -> dict:
    output = output.strip()

    start = output.find("{")
    end = output.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("Router model did not return JSON.")

    return json.loads(output[start : end + 1])


def route_user_text(user_text: str, router_model: str) -> dict:
    total_start = time.time()

    print("Building router prompt...")
    prompt_start = time.time()
    prompt = build_router_prompt(user_text)
    print(f"Built prompt in {time.time() - prompt_start:.2f}s")
    print(f"Router prompt size: {len(prompt)} characters")

    print(f"Routing request through local model: {router_model}")
    model_start = time.time()

    chunks = []
    first_chunk_time = None

    for chunk in ask_model_stream(prompt, model=router_model):
        if first_chunk_time is None:
            first_chunk_time = time.time()
            print(f"\nFirst token after {first_chunk_time - model_start:.2f}s")

        print(chunk, end="", flush=True)
        chunks.append(chunk)

    print()

    raw_output = "".join(chunks)

    model_elapsed = time.time() - model_start
    print(f"Router model finished in {model_elapsed:.2f}s")
    print(f"Router output size: {len(raw_output)} characters")

    print("Parsing router JSON...")
    parse_start = time.time()
    command = parse_router_json(raw_output)
    print(f"Parsed JSON in {time.time() - parse_start:.2f}s")

    print(f"Total routing time: {time.time() - total_start:.2f}s")

    return command


def run_task(task: str, model: str) -> None:
    subprocess.run(
        [
            "python",
            "harness.py",
            "--task",
            task,
            "--model",
            model,
        ]
    )


def handle_command(user_text: str, router_model: str) -> None:
    command = route_user_text(user_text, router_model)

    action = command.get("action")
    task = command.get("task")
    model = command.get("model") or "qwen2.5-coder:7b"

    print("\nRouter command:")
    print(json.dumps(command, indent=2))

    if action == "show_tasks":
        print("\nAvailable tasks:")
        for task_name in list_tasks():
            print(f"- {task_name}")
        return
    
    if action == "create_task":
        create_task_from_command(command)
        return

    if action == "run_task":
        if not task:
            print("No task was selected.")
            return

        if task not in list_tasks():
            print(f"Unknown task: {task}")
            return

        run_task(task, model)
        return

    print("I could not determine what to do.")

def create_task_from_command(command: dict) -> None:
    task = command.get("task")
    prompt = command.get("prompt") or "Describe what the model should change."
    initial_file = command.get("initial_file") or "main.py"
    initial_content = command.get("initial_content") or 'print("TODO: implement task")'
    editable_paths = command.get("editable_paths") or [initial_file]
    read_only_paths = command.get("read_only_paths") or []

    if not task:
        print("No task name was provided.")
        return

    cli_command = [
        "python",
        "create_task.py",
        task,
        "--prompt",
        prompt,
        "--initial-file",
        initial_file,
        "--initial-content",
        initial_content,
        "--editable",
        *editable_paths,
    ]

    if read_only_paths:
        cli_command.extend(["--read-only", *read_only_paths])

    subprocess.run(cli_command)


def main() -> None:
    models = get_default_models()
    router_model = models["router_model"]

    print("Toy Harness Chat")
    print("Examples:")
    print("  run the sales summary task with 7b")
    print("  show me available tasks")
    print("  run add numbers with 3b")
    print("Type 'exit' to quit.")

    while True:
        user_text = input("\n> ").strip()

        if user_text.lower() in {"exit", "quit", "q"}:
            print("Goodbye.")
            break

        try:
            handle_command(user_text, router_model)
        except Exception as error:
            print(f"Error: {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()