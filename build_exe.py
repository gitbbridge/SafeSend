import subprocess
import sys
from pathlib import Path

import customtkinter


ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
ICON = ROOT / "app" / "assets" / "icon.ico"
CUSTOMTKINTER_DIR = Path(customtkinter.__file__).resolve().parent


def main() -> int:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--name",
        "SafeSend",
        "--add-data",
        f"{ROOT / 'data'};data",
        "--add-data",
        f"{ROOT / 'config'};config",
        "--add-data",
        f"{CUSTOMTKINTER_DIR};customtkinter",
    ]
    if ICON.exists() and ICON.stat().st_size > 100:
        command.extend(["--icon", str(ICON)])
    command.append(str(MAIN))
    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
