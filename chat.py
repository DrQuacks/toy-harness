import subprocess


def normalize_model(text: str) -> str:
    if "3b" in text:
        return "qwen2.5-coder:3b"

    if "7b" in text:
        return "qwen2.5-coder:7b"

    return "qwen2.5-coder:7b"


def normalize_task(text: str) -> str | None:
    if "sales" in text:
        return "sales-summary"

    if "add numbers" in text or "add-numbers" in text:
        return "add-numbers"

    if "hello" in text:
        return "hello-world"

    return None


def handle_command(text: str) -> None:
    lowered = text.lower().strip()

    if lowered in {"exit", "quit", "q"}:
        raise KeyboardInterrupt

    if lowered.startswith("run "):
        task = normalize_task(lowered)
        model = normalize_model(lowered)

        if task is None:
            print("I could not determine which task to run.")
            return

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
        return

    print("I do not know how to handle that yet.")


def main() -> None:
    print("Toy Harness Chat")
    print("Example: run the sales summary task with 7b")
    print("Type 'exit' to quit.")

    while True:
        try:
            text = input("\n> ")
            handle_command(text)
        except KeyboardInterrupt:
            print("\nGoodbye.")
            break


if __name__ == "__main__":
    main()