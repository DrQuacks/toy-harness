from pathlib import Path
import shutil


def create_workspace(task_dir: Path, workspace_dir: Path) -> Path:
    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)

    initial_dir = task_dir / "initial"

    if not initial_dir.exists():
        raise FileNotFoundError(f"Missing initial directory: {initial_dir}")

    shutil.copytree(initial_dir, workspace_dir)

    run_script = task_dir / "run.sh"
    if run_script.exists():
        shutil.copy2(run_script, workspace_dir / "run.sh")

    return workspace_dir

def read_workspace_files(workspace_dir: Path) -> dict[str, str]:
    files: dict[str, str] = {}

    for path in workspace_dir.rglob("*"):
        if path.is_file() and path.name != "run.sh":
            relative_path = path.relative_to(workspace_dir)
            files[str(relative_path)] = path.read_text()

    return files