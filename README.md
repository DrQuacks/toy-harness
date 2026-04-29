# toy-harness

A minimal code harness that uses a local language model to iteratively fix code until it passes a validation test.

## What It Does

1. Loads a task (a prompt, starter code, and a validation script)
2. Copies the starter code into a clean workspace
3. Asks a local model to rewrite the code so the task passes
4. Runs the validation script against the model's output
5. If it fails, feeds the error back to the model and retries (up to 5 times)

## Project Structure

```
toy-harness/
├── harness.py          # Main orchestrator — runs the solve-and-evaluate loop
├── model_client.py     # Sends prompts to a local model server and returns generated code
├── runner.py           # Executes shell commands and captures output/exit codes
├── workspace.py        # Creates and reads a clean sandbox directory for each run
└── tasks/
    └── task1/
        ├── prompt.txt      # The task description given to the model
        ├── run.sh          # Validation script — exits 0 if the code passes
        └── initial/
            └── main.py     # Starter code the model begins from
```

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com/) running locally (default: `http://localhost:11434`)
- The model `qwen2.5-coder:7b` pulled in Ollama
- The `requests` Python package

## Setup

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install requests

# Pull the model (if not already pulled)
ollama pull qwen2.5-coder:7b
```

## Running

Make sure Ollama is running, then:

```bash
python harness.py
```

You'll see output for each attempt:

```
=== ATTEMPT 1 ===
Reading workspace files...
Building prompt...
Prompt size: 412 characters
Asking model...
Model responded in 2.34s
Cleaning model output...
Saving attempt...
Writing main.py...

=== MODEL WROTE main.py ===
print("Hello, world!")

=== RUNNING VALIDATION ===
Validation finished in 0.21s
✅ Passed!
```

## How the Harness Works

- **Workspace isolation**: Each run starts by deleting and recreating `workspace/task1/` from the original task files. The source task is never modified.
- **Prompt construction**: The harness builds a prompt from the task description, current file contents, and (on retries) the previous failure output.
- **Attempt artifacts**: Every model response is saved to `workspace/task1/.attempts/` so you can review what the model tried.
- **Retry with feedback**: If validation fails, the combined stdout/stderr/exit code is included in the next prompt so the model can self-correct.

## Adding a New Task

1. Create a new folder under `tasks/`, e.g. `tasks/task2/`
2. Add a `prompt.txt` describing what the code should do
3. Add an `initial/` folder with starter code (at minimum `main.py`)
4. Add a `run.sh` that exits `0` on success and non-zero on failure
5. Update the `task_dir` and `workspace_dir` paths in `harness.py`
