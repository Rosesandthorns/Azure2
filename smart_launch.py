import os
import platform
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import Iterable, Optional, Tuple

MIN_PYTHON = (3, 10)
PROJECT_ROOT = Path(__file__).resolve().parent
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
MAIN_FILE = PROJECT_ROOT / "main.py"


def log(message: str) -> None:
    print(f"[smart-launch] {message}", flush=True)


def run_command(command: Iterable[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        check=False,
        capture_output=True,
        text=True,
    )


def version_tuple(text: str) -> Optional[Tuple[int, int, int]]:
    match = re.search(r"(\\d+)\\.(\\d+)\\.(\\d+)", text)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def check_python(executable: str) -> Optional[Tuple[int, int, int]]:
    result = run_command([executable, "-c", "import sys; print(sys.version.split()[0])"])
    if result.returncode != 0:
        return None
    return version_tuple(result.stdout.strip())


def is_version_supported(version: Tuple[int, int, int]) -> bool:
    return version >= MIN_PYTHON


def find_supported_python() -> Optional[str]:
    candidates = [
        sys.executable,
        "python3.12",
        "python3.11",
        "python3.10",
        "python3",
        "python",
    ]
    for candidate in candidates:
        path = shutil.which(candidate) if candidate != sys.executable else candidate
        if not path:
            continue
        version = check_python(path)
        if version and is_version_supported(version):
            return path
    return None


def install_python_if_possible() -> None:
    system = platform.system().lower()
    if system == "linux" and shutil.which("apt-get"):
        log("Attempting to install Python via apt-get (requires sudo).")
        subprocess.run(["sudo", "apt-get", "update"], check=False)
        for version in ("3.11", "3.10"):
            subprocess.run(
                ["sudo", "apt-get", "install", "-y", f"python{version}", f"python{version}-venv"],
                check=False,
            )
    elif system == "darwin" and shutil.which("brew"):
        log("Attempting to install Python via Homebrew.")
        subprocess.run(["brew", "update"], check=False)
        subprocess.run(["brew", "install", "python@3.11"], check=False)
    elif system == "windows" and shutil.which("winget"):
        log("Attempting to install Python via winget.")
        subprocess.run(
            ["winget", "install", "-e", "--id", "Python.Python.3.11"],
            check=False,
        )
    else:
        log("No supported package manager found to install Python automatically.")


def ensure_supported_python() -> str:
    supported = find_supported_python()
    if supported:
        return supported

    log("No supported Python found. Attempting to install one.")
    install_python_if_possible()
    supported = find_supported_python()
    if supported:
        return supported

    raise RuntimeError(
        "Unable to locate a supported Python version (3.10+). "
        "Please install Python 3.10+ and re-run smart_launch.py."
    )


def ensure_pip(python: str) -> None:
    result = run_command([python, "-m", "pip", "--version"])
    if result.returncode == 0:
        return
    log("pip not available; attempting to bootstrap with ensurepip.")
    run_command([python, "-m", "ensurepip", "--upgrade"])


def install_requirements(python: str) -> None:
    if not REQUIREMENTS_FILE.exists():
        log("requirements.txt not found; skipping dependency installation.")
        return
    run_command([python, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    log("Installing dependencies from requirements.txt.")
    result = run_command([python, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])
    if result.returncode != 0:
        log("Dependency installation reported errors:")
        log(result.stdout.strip())
        log(result.stderr.strip())


def ensure_project_paths() -> None:
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    if not MAIN_FILE.exists():
        raise FileNotFoundError(f"main.py not found at {MAIN_FILE}")


def parse_missing_module(output: str) -> Optional[str]:
    match = re.search(r"No module named ['\"]([^'\"]+)['\"]", output)
    if match:
        return match.group(1)
    return None


def stream_process(command: Iterable[str]) -> Tuple[int, str]:
    proc = subprocess.Popen(
        list(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    captured: list[str] = []

    def reader(stream, name: str) -> None:
        for line in iter(stream.readline, ""):
            print(line, end="")
            captured.append(line)
        stream.close()

    threads = [
        threading.Thread(target=reader, args=(proc.stdout, "stdout"), daemon=True),
        threading.Thread(target=reader, args=(proc.stderr, "stderr"), daemon=True),
    ]
    for thread in threads:
        thread.start()
    proc.wait()
    for thread in threads:
        thread.join()
    return proc.returncode, "".join(captured)


def launch_bot(python: str, args: Iterable[str]) -> int:
    log("Launching bot.")
    return_code, combined_output = stream_process([python, "-u", str(MAIN_FILE), *args])
    if return_code == 0:
        return 0

    missing_module = parse_missing_module(combined_output)
    if missing_module:
        log(f"Detected missing module '{missing_module}'. Attempting install.")
        run_command([python, "-m", "pip", "install", missing_module])
        return_code, _ = stream_process([python, "-u", str(MAIN_FILE), *args])
        return return_code

    if "LoginFailure" in combined_output:
        log("Discord login failed. Check your token in config.yaml.")
    if "KeyError" in combined_output and "config" in combined_output.lower():
        log("Configuration error detected. Verify config.yaml has all required keys.")
    return return_code


def main() -> int:
    try:
        ensure_project_paths()
        target_python = ensure_supported_python()
    except Exception as exc:
        log(str(exc))
        return 1

    if os.path.abspath(target_python) != os.path.abspath(sys.executable):
        log(f"Re-launching with supported Python: {target_python}")
        os.execv(target_python, [target_python, str(Path(__file__).resolve()), *sys.argv[1:]])

    ensure_pip(target_python)
    install_requirements(target_python)

    try:
        return launch_bot(target_python, sys.argv[1:])
    except Exception as exc:
        log(f"Unhandled error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
