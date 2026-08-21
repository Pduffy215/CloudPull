import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
APP_NAME = "StreamSender"
ENTRY_SCRIPT = PROJECT_ROOT / "rawStreamPoster.py"
ICON_PATH = PROJECT_ROOT / "assets" / "vsc_icon.ico"
EXE_FOLDER = PROJECT_ROOT / "dist" / APP_NAME  # PyInstaller's default onedir output location

FOLDERS_TO_COPY = ["config", "assets", "mdbtools-win-1.0.0"]


def run(command, description):
    print(f"\n=== {description} ===")
    result = subprocess.run(command, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print(f"FAILED: {description} (exit code {result.returncode})")
        sys.exit(result.returncode)


def main():
    if not ENTRY_SCRIPT.exists():
        print(f"{ENTRY_SCRIPT} not found")
        sys.exit(1)

    cmd = [
        "uv", "run", "pyinstaller",
        f"--icon={ICON_PATH}",
        "--windowed",
        "--onedir",
        "--name", APP_NAME,
        str(ENTRY_SCRIPT),
    ]
    run(cmd, f"Building {APP_NAME} (onedir)")

    print(f"\n=== Copying resource folders into {EXE_FOLDER} ===")
    for folder_name in FOLDERS_TO_COPY:
        src = PROJECT_ROOT / folder_name
        dst = EXE_FOLDER / folder_name
        if not src.is_dir():
            print(f"  SKIPPED: {folder_name} (not found at {src})")
            continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"  Copied {folder_name} -> {dst}")

    print(f"\nDone. Run: {EXE_FOLDER / (APP_NAME + '.exe')}")


if __name__ == "__main__":
    main()