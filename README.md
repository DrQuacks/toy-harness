# toy-harness

A minimal code harness that uses a local language model to iteratively fix code until it passes a validation test.

## What It Does

1. Loads a task configuration, prompt, starter code, and validation command
2. Copies the starter code into a clean workspace
3. Asks a local model for a JSON edit plan describing which files to update
4. Applies those file edits inside the workspace
5. Runs the validation command against the edited code
6. If it fails, feeds the error back to the model and retries (up to 5 times)

## Project Structure

```
toy-harness/
├── create_task.py      # CLI for generating new task folders and starter files
├── harness.py          # Main orchestrator — runs the solve-and-evaluate loop
├── model_client.py     # Sends prompts to a local model server and returns generated code
├── runner.py           # Executes shell commands and captures output/exit codes
├── workspace.py        # Creates and reads a clean sandbox directory for each run
└── tasks/
    └── task1/
        ├── task.json       # Task config: prompt file, validation command, editable paths, limits
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
{"edits":[{"path":"main.py","content":"print(\"Hello, world!\")\n"}]}
Model responded in 2.34s
Parsing model edit JSON...
Applying edits...
- main.py

=== RUNNING VALIDATION ===
Validation finished in 0.21s
✅ Passed!
```

## How the Harness Works

- **Workspace isolation**: Each run starts by deleting and recreating `workspace/task1/` from the original task files. The source task is never modified.
- **Task config**: `task.json` tells the harness which prompt file to read, which paths may be edited, which command validates success, and how many attempts/timeouts to allow.
- **Prompt construction**: The harness builds a prompt from the task description, current file contents, editable paths, and (on retries) the previous failure output.
- **Structured model output**: The model is asked to return JSON with an `edits` array, and the harness applies only those edits that target allowed paths.
- **Attempt artifacts**: Every prompt, model response, parsed edit plan, and validation log is saved to `workspace/task1/.attempts/` so you can review what happened.
- **Retry with feedback**: If validation fails, the combined stdout/stderr/exit code is included in the next prompt so the model can self-correct.

## Adding a New Task

Use `create_task.py` to scaffold a new task instead of creating the files by hand.

### Basic usage

```bash
python create_task.py "Hello World"
```

This creates `tasks/hello-world/` with:

- `task.json` — task metadata such as editable paths, validation command, max attempts, and timeout
- `prompt.txt` — the task instructions shown to the model
- `run.sh` — an executable validation script
- `initial/main.py` — starter code copied into the workspace before each run

The generated `task.json` is read by `harness.py` to control the solve-and-validate loop.

### Example with custom options

```bash
python create_task.py "Reverse String" \
    --prompt "Modify the code so main.py prints the reversed input string." \
    --initial-file "main.py" \
    --initial-content 'print("TODO: implement task")' \
    --editable main.py \
    --validation-command python main.py
```

### Available options

- `name` — human-readable task name used to generate the folder slug
- `--slug` — override the generated folder name
- `--prompt` — initial task instructions written to `prompt.txt`
- `--initial-file` — path to the starter file inside `initial/`
- `--initial-content` — contents of the starter file
- `--editable` — one or more editable file paths or directories
- `--validation-command` — command stored in `task.json` and written into `run.sh`
- `--max-attempts` — maximum model attempts stored in `task.json`
- `--timeout-seconds` — validation timeout stored in `task.json`

### After creating a task

The harness is still hardcoded to `tasks/task1` in `harness.py`, so after generating a new task you should update:

- `task_dir = Path("tasks/<your-task-slug>")`
- `workspace_dir = Path("workspace/<your-task-slug>")`

If you want a new task to validate through `run.sh`, make the generated `run.sh` check for success and exit non-zero on failure.

You can also point `validation_command` in `task.json` at a different command if your task needs something more specific than `bash run.sh`.
