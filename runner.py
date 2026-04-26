from dataclasses import dataclass
import subprocess
from pathlib import Path


@dataclass
class RunResult:
    ok: bool
    exit_code: int
    stdout: str
    stderr: str


def run_command(command: list[str], cwd: Path, timeout_seconds: int = 10) -> RunResult:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
        )

        return RunResult(
            ok=completed.returncode == 0,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    except subprocess.TimeoutExpired as error:
        raw_stdout = error.stdout

        if raw_stdout is None:
            timeout_stdout = ""
        elif isinstance(raw_stdout, str):
            timeout_stdout = raw_stdout
        else:
            # Handles bytes, bytearray, memoryview
            timeout_stdout = bytes(raw_stdout).decode("utf-8", errors="replace")

        return RunResult(
            ok=False,
            exit_code=124,
            stdout=timeout_stdout,
            stderr=f"Command timed out after {timeout_seconds} seconds.",
        )