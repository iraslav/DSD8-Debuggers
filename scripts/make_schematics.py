#!/usr/bin/env python3
"""Build appendix Yosys schematics and simple presentation figures."""

import os
import pathlib
import shutil
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "doc" / "schematics"
DOT_CANDIDATES = (
    pathlib.Path(r"C:\Program Files\Graphviz\bin\dot.exe"),
    pathlib.Path(r"C:\Program Files (x86)\Graphviz\bin\dot.exe"),
)

# Keep this list explicit and in sync with scripts/synth.ys.
RTL_SOURCES = (
    "../../rtl/alu.v",
    "../../rtl/control_unit.v",
    "../../rtl/data_memory.v",
    "../../rtl/dsd8_cpu.v",
    "../../rtl/dsd8_top.v",
    "../../rtl/flags_reg.v",
    "../../rtl/instr_decoder.v",
    "../../rtl/instr_memory.v",
    "../../rtl/io_bus.v",
    "../../rtl/prog_counter.v",
    "../../rtl/register_file.v",
    "../../sim/peripherals.v",
)

MODULES = (
    ("alu", "alu_schematic"),
    ("register_file", "register_file_schematic"),
    ("flags_reg", "flags_reg_schematic"),
    ("instr_decoder", "instr_decoder_schematic"),
    ("control_unit", "control_unit_schematic"),
    ("prog_counter", "prog_counter_schematic"),
    ("dsd8_cpu", "cpu_blocks"),
)


def find_dot_exe():
    for candidate in DOT_CANDIDATES:
        if candidate.is_file():
            return candidate
    for current, directories, files in os.walk("C:\\", onerror=lambda _: None):
        directories[:] = [name for name in directories if name not in ("$Recycle.Bin", "System Volume Information")]
        if "dot.exe" in files:
            return pathlib.Path(current) / "dot.exe"
    raise FileNotFoundError("Could not find dot.exe under C:\\.")


def yosys_script(top, prefix, output_format="png", stretch=False):
    sources = " ".join(RTL_SOURCES)
    options = " -stretch" if stretch else ""
    return (
        f"read_verilog -sv {sources}; "
        f"hierarchy -top {top}; "
        f"proc; opt; "
        f"show -format {output_format}{options} -prefix {prefix} {top}"
    )


def run_yosys(yosys, dot_exe, script):
    environment = os.environ.copy()
    # Yosys invokes `dot` by name; expose the discovered folder only to this
    # child process, without changing the user's persistent PATH.
    environment["PATH"] = str(dot_exe.parent) + os.pathsep + environment.get("PATH", "")
    result = subprocess.run(
        [str(yosys), "-Q", "-p", script],
        cwd=OUT,
        env=environment,
        text=True,
        capture_output=True,
    )
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)


def png_dimensions(path):
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Yosys did not create a valid PNG: {path}")
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def write_readme():
    descriptions = {
        "alu_schematic.png": "ALU gate-level logic; appendix (complex).",
        "register_file_schematic.png": "Register-file gate-level logic; appendix (complex).",
        "flags_reg_schematic.png": "Flags-register gate-level logic; appendix (complex).",
        "instr_decoder_schematic.png": "Instruction-decoder gate-level logic; appendix (complex).",
        "control_unit_schematic.png": "Control-unit gate-level logic; appendix (complex).",
        "prog_counter_schematic.png": "Program-counter gate-level logic; appendix (complex).",
        "cpu_blocks.png": "Hierarchical dsd8_cpu with its actual instances; appendix (complex).",
        "cpu_blocks.svg": "Zoomable hierarchical dsd8_cpu drawing; appendix (complex).",
        "alu_simple.png": "ALU input and output port names in one box; present this (simple).",
        "register_file_simple.png": "Register-file input and output port names in one box; present this (simple).",
        "flags_reg_simple.png": "Flags-register input and output port names in one box; present this (simple).",
        "instr_decoder_simple.png": "Decoder input and output port names in one box; present this (simple).",
        "control_unit_simple.png": "Control-unit input and output port names in one box; present this (simple).",
        "prog_counter_simple.png": "Program-counter input and output port names in one box; present this (simple).",
        "cpu_simple.png": "Five high-level CPU boxes with stage colors; present this (simple).",
    }
    lines = ["# DSD-8 schematics", ""]
    for filename, description in descriptions.items():
        if (OUT / filename).is_file():
            lines.append(f"- `{filename}` — {description}")
    lines += [
        "",
        "The `cpu_blocks` hierarchy contains `instr_decoder`, `register_file`, `alu`, `flags_reg`, and `data_memory` instances.",
        "`dsd8_cpu` does not instantiate `prog_counter` or `control_unit`; its PC and opcode control are implemented inside the CPU module.",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    yosys = shutil.which("yosys")
    if not yosys:
        raise FileNotFoundError("yosys is not on PATH.")
    dot_exe = find_dot_exe()
    print(f"Using Graphviz: {dot_exe}")
    OUT.mkdir(parents=True, exist_ok=True)

    # Yosys evaluates the instruction-memory $readmemh while parsing RTL.
    # Provide a temporary image only when the user has no program.hex.
    program_image = OUT / "program.hex"
    created_program_image = not program_image.exists()
    if created_program_image:
        program_image.write_text("0000\n", encoding="ascii")

    try:
        for top, name in MODULES:
            command = yosys_script(
                top,
                name,
                stretch=(top == "dsd8_cpu"),
            )
            print(f"Yosys: {name}.png")
            run_yosys(yosys, dot_exe, command)

            if top == "dsd8_cpu":
                png = OUT / "cpu_blocks.png"
                width, height = png_dimensions(png)
                print(f"cpu_blocks.png: {width} x {height}, {png.stat().st_size} bytes")
                if width > 3500 or height > 3500 or png.stat().st_size > 4_000_000:
                    print("Large hierarchy; also creating cpu_blocks.svg.")
                    run_yosys(
                        yosys,
                        dot_exe,
                        yosys_script(
                            top,
                            "cpu_blocks",
                            output_format="svg",
                            stretch=True,
                        ),
                    )

        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "make_module_boxes.py"),
             "--dot-exe", str(dot_exe)],
            cwd=ROOT,
            check=True,
        )
        write_readme()
        print(f"Wrote {OUT / 'README.md'}")
    finally:
        if created_program_image and program_image.exists():
            program_image.unlink()


if __name__ == "__main__":
    main()
