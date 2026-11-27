#!/usr/bin/env python3
"""Compile and run each self-checking module testbench under tb/."""
import pathlib
import shutil
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RTL = REPO_ROOT / "rtl"
PERIPHERALS = REPO_ROOT / "sim" / "peripherals.v"
TB_DIR = REPO_ROOT / "tb"
BUILD_DIR = REPO_ROOT / "build" / "unit"


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)


def main():
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    tb_files = sorted(
        p for p in TB_DIR.glob("tb_*.v")
        if p.name != "tb_dsd8.v"
    )

    if not tb_files:
        print(f"no unit testbenches found under {TB_DIR} (expected tb_<module>.v files)")
        sys.exit(0)  # nothing to run yet is not a failure at M1

    for tool in ("iverilog", "vvp"):
        if shutil.which(tool) is None:
            print(f"error: '{tool}' is not installed or not on PATH.", file=sys.stderr)
            print("Install Icarus Verilog first, e.g.: sudo apt-get install iverilog", file=sys.stderr)
            sys.exit(3)

    rtl_sources = [str(p) for p in sorted(RTL.glob("*.v"))] + [str(PERIPHERALS)]

    n_pass = 0
    results = []
    for tb_path in tb_files:
        sim_bin = BUILD_DIR / (tb_path.stem + ".vvp")
        compile_cmd = [
            "iverilog", "-g2005", "-s", tb_path.stem, "-o", str(sim_bin)
        ] + rtl_sources + [str(tb_path)]
        r = run(compile_cmd)
        if r.returncode != 0:
            results.append((tb_path.name, "ERROR", f"compile failed:\n{r.stdout}{r.stderr}"))
            continue

        r = run(["vvp", str(sim_bin)])
        output = r.stdout + r.stderr
        if r.returncode == 0 and "TESTBENCH: PASS" in output and "TESTBENCH: FAIL" not in output:
            results.append((tb_path.name, "PASS", None))
            n_pass += 1
            print(output, end="")
        elif "TESTBENCH: FAIL" in output or r.returncode != 0:
            fail_line = next((l for l in output.splitlines() if "TESTBENCH: FAIL" in l), "")
            details = fail_line or f"simulator exited {r.returncode}"
            if output.strip():
                details += "\n" + output.strip()
            results.append((tb_path.name, "FAIL", details))
        else:
            results.append((tb_path.name, "ERROR",
                             "no TESTBENCH: PASS/FAIL line found -- see tb/README.md for the convention\n" + output))

    print()
    print(f"{'TESTBENCH':30s} RESULT")
    print("-" * 50)
    for name, status, detail in results:
        print(f"{name:30s} {status}")
        if detail:
            for line in detail.splitlines():
                print(f"    {line}")
    print("-" * 50)
    print(f"{n_pass} / {len(results)} passed")
    print()

    sys.exit(0 if n_pass == len(results) else 1)


if __name__ == "__main__":
    main()
