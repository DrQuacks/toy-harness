import json
import subprocess
from pathlib import Path

from model_client import ask_model


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
3. unknown

Return ONLY valid JSON.

Schema:
{{
  "action": "run_task" | "show_tasks" | "unknown",
  "task": string | null,
  "model": string | null
}}

Rules:
- If the user asks to run, execute, try, or test a task, use action "run_task".
- The task must be one of the available tasks.
- If the user mentions 3b, use model "qwen2.5-coder:3b".
- If the user mentions 7b, use model "qwen2.5-coder:7b".
- If no model is mentioned, use model "qwen2.5-coder:7b".
- If the user asks what tasks exist, use action "show_tasks".
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
    prompt = build_router_prompt(user_text)
    raw_output = ask_model(prompt, model=router_model)
    return parse_router_json(raw_output)


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


def main() -> None:
    router_model = "qwen2.5-coder:7b"

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