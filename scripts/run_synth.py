import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    image = ROOT / "build" / "conformance" / "sample01_multiply.hex"
    if not image.exists():
        run_assembler = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "dsd8asm.py"),
             str(ROOT / "tests" / "conformance" / "sample01_multiply.asm"),
             "-o", str(image)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if run_assembler.returncode != 0:
            print(run_assembler.stdout)
            print(run_assembler.stderr, file=sys.stderr)
            raise SystemExit(run_assembler.returncode)

    program_hex = ROOT / "program.hex"
    try:
        shutil.copyfile(image, program_hex)
        result = subprocess.run(
            ["yosys", "-s", str(ROOT / "scripts" / "synth.ys")],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        if result.returncode != 0:
            raise SystemExit(result.returncode)
    finally:
        if program_hex.exists():
            program_hex.unlink()


if __name__ == "__main__":
    main()
