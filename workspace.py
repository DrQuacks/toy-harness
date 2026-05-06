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

def read_workspace_files(
    workspace_dir: Path,
    included_paths: list[str],
) -> dict[str, str]:
    files: dict[str, str] = {}

    for path in workspace_dir.rglob("*"):
        if not path.is_file():
            continue

        relative_path = str(path.relative_to(workspace_dir))

        if not path_matches_allowed(relative_path, included_paths):
            continue

        files[relative_path] = path.read_text()

    return files

def path_matches_allowed(relative_path: str, allowed_paths: list[str]) -> bool:
    normalized = relative_path.strip("/")

    for allowed in allowed_paths:
        allowed = allowed.strip("/")

        if normalized == allowed:
            return True

        if allowed.endswith("/") and normalized.startswith(allowed):
            return True

    return False