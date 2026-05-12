# Instructions

## 1) Setup

Requirements:

- Python 3.11+
- [Ollama](https://ollama.com/) running locally (default endpoint: `http://localhost:11434`)
- A pulled model (default in this repo: `qwen2.5-coder:7b`)

Run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
ollama pull qwen2.5-coder:7b
```

## 2) Create a new task

Basic:

```bash
python create_task.py "Hello World"
```

Custom example:

```bash
python create_task.py "Reverse String" \
  --slug reverse-string \
  --prompt "Modify the code so main.py prints the reversed input string." \
  --initial-file main.py \
  --initial-content 'print("TODO: implement task")' \
  --editable main.py \
  --validation-command bash run.sh \
  --max-attempts 5 \
  --timeout-seconds 10
```

This generates `tasks/<slug>/` with:

- `task.json`
- `prompt.txt`
- `run.sh`
- `initial/<initial-file>`

## 3) Run the harness on a task

Use `--task` (required):

```bash
python harness.py --task task1
```

Run with a different model:

```bash
python harness.py --task task1 --model qwen2.5-coder:7b
```

Run with a custom workspace root:

```bash
python harness.py --task task1 --workspace-root workspace
```

## 4) What happens during a run

For each attempt, the harness will:

1. Recreate a clean workspace from `tasks/<task>/initial/`
2. Read `task.json` for editable paths, validation command, limits, and timeout
3. Build a prompt from task instructions + current files + previous error output
4. Ask the model for a JSON edit plan (`{"edits": [...]}`)
5. Apply only allowed edits
6. Run validation and stop on success, or retry until `max_attempts`

## 5) Inspect attempt artifacts

Each run writes artifacts to:

`workspace/<task>/.attempts/`

Typical files:

- `attempt_1_prompt.txt`
- `attempt_1_model_output.txt`
- `attempt_1_edit_plan.json`
- `attempt_1_validation.txt`

## 6) Command reference

`create_task.py`:

- `name` (positional): Human-readable task name
- `--slug`: Folder name override
- `--editable`: One or more editable paths (default `main.py`)
- `--validation-command`: Validation command tokens (default `bash run.sh`)
- `--prompt`: Prompt content for `prompt.txt`
- `--initial-file`: Starter file path inside `initial/`
- `--initial-content`: Starter file content
- `--max-attempts`: Stored in `task.json` (default `5`)
- `--timeout-seconds`: Stored in `task.json` (default `10`)

`harness.py`:

- `--task` (required): Task folder under `tasks/`
- `--model`: Model name sent to Ollama (default `qwen2.5-coder:7b`)
- `--workspace-root`: Where per-task workspaces are created (default `workspace`)

## 7) Quick troubleshooting

- If `harness.py` fails immediately, confirm the task exists: `tasks/<task>/task.json`.
- If model requests fail, confirm Ollama is running and the model is pulled.
- If validation always fails, run the validation command manually in `workspace/<task>/`.
