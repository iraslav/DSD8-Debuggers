import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RTL = ROOT / "rtl"
BUILD = ROOT / "build" / "wave"
SIM = ROOT / "sim"
TB = ROOT / "tb"


def run(cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr, file=sys.stderr)
        raise SystemExit(r.returncode)
    print(r.stdout, end="")
    print(r.stderr, end="", file=sys.stderr)


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    SIM.mkdir(parents=True, exist_ok=True)

    programs = [
        ("demo_alu", ROOT / "tests" / "demo_alu.asm"),
        ("b1_multiply", ROOT / "tests" / "conformance" / "sample01_multiply.asm"),
        ("b2_popcount", ROOT / "tests" / "conformance" / "sample02_popcount.asm"),
    ]

    rtl_sources = [str(p) for p in sorted(RTL.glob("*.v"))]
    rtl_sources += [str(ROOT / "sim" / "peripherals.v"),
                    str(TB / "tb_dsd8.v"), str(TB / "wave_dump.v")]

    for name, asm_path in programs:
        hex_path = BUILD / (name + ".hex")
        trace_path = BUILD / (name + ".trace")
        sim_bin = BUILD / (name + ".vvp")

        run([sys.executable, str(ROOT / "tools" / "dsd8asm.py"),
             str(asm_path), "-o", str(hex_path)])

        program_hex = ROOT / "program.hex"
        try:
            shutil.copyfile(hex_path, program_hex)
            compile_cmd = [
                "iverilog", "-g2005", "-o", str(sim_bin),
            ] + rtl_sources
            run(compile_cmd)
            run(["vvp", str(sim_bin)])
        finally:
            if program_hex.exists():
                program_hex.unlink()

        shutil.copyfile(SIM / "dsd8_pipeline.vcd",
                        SIM / (name + "_pipeline.vcd"))
        print(name + ": PASS")

    shutil.copyfile(SIM / "demo_alu_pipeline.vcd",
                    SIM / "dsd8_pipeline.vcd")


if __name__ == "__main__":
    main()
