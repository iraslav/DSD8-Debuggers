#!/usr/bin/env python3
"""Simulate the presentation examples and write a cycle-accurate SVG."""

import pathlib
import shutil
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parent.parent
RTL = ROOT / "rtl"
DOC = ROOT / "doc" / "simple"
TIMING_PROGRAM = """\
LDI R1, 10
LDI R2, 10
ADD R3, R1, R2
SUB R4, R3, R3
ST [R1], R3
LD R5, [R1]
BEQ DONE
DONE: HLT
"""
LOAD_USE_PROGRAM = """\
LDI R1, 10
LDI R2, 0
ST [R1], R2
LD R3, [R1]
ADD R4, R3, R2
ADD R6, R3, R2
HLT
"""
BRANCH_NAMES = ("BEQ", "BNE", "BCS", "BCC", "BMI", "BPL", "BVS", "BVC")


def require_tool(name):
    found = shutil.which(name)
    if not found:
        raise RuntimeError(f"Required tool '{name}' is not on PATH.")
    return found


def simulate(source, work, name, max_cycles=None):
    work.mkdir(parents=True, exist_ok=True)
    (work / "sim").mkdir(exist_ok=True)
    asm = work / (name + ".asm")
    image = work / "program.hex"
    asm.write_text(source, encoding="utf-8")
    subprocess.run(
        [sys.executable, str(ROOT / "tools" / "dsd8asm.py"),
         str(asm), "-o", str(image)],
        cwd=ROOT, check=True,
    )

    sources = [str(path) for path in sorted(RTL.glob("*.v"))]
    sources += [
        str(ROOT / "sim" / "peripherals.v"),
        str(ROOT / "tb" / "tb_dsd8.v"),
        str(ROOT / "tb" / "wave_dump.v"),
    ]
    binary = work / (name + ".vvp")
    command = [require_tool("iverilog"), "-g2005", "-o", str(binary)]
    if max_cycles is not None:
        command.insert(2, f"-Ptb_dsd8.MAX_CYCLES={max_cycles}")
    subprocess.run(command + sources, cwd=ROOT, check=True)
    run = subprocess.run(
        [require_tool("vvp"), str(binary)],
        cwd=work, text=True, capture_output=True,
    )
    if run.returncode:
        raise RuntimeError(run.stdout + run.stderr)
    vcd = work / "sim" / "dsd8_pipeline.vcd"
    if not vcd.exists():
        raise RuntimeError(f"Simulation did not create {vcd}")
    return vcd, run.stdout


def read_samples(path):
    wanted = {
        "s1_valid", "s1_pc", "s1_ir", "s2_valid", "s2_pc", "s2_ir",
        "s2_rs1", "s2_ra2", "s3_valid", "s3_pc", "s3_ir",
        "s3_rf_we", "s3_rf_addr", "load_use_stall", "branch_taken",
        "retire", "retire_pc", "io_stall", "io_ready",
    }
    names = {}
    scopes = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    header_end = 0
    for i, line in enumerate(lines):
        parts = line.split()
        if parts and parts[0] == "$scope":
            scopes.append(parts[2])
        elif parts and parts[0] == "$upscope":
            scopes.pop()
        elif parts and parts[0] == "$var":
            name = parts[4]
            if scopes[-2:] == ["tb_dsd8", "uut"] and name in wanted:
                names[name] = parts[3]
            elif scopes == ["tb_dsd8"] and name in {"clk", "rst_n", "retire", "retire_pc"}:
                names.setdefault(name, parts[3])
        elif parts and parts[0] == "$enddefinitions":
            header_end = i + 1
            break

    state = {}
    samples = []
    rising = False
    time_ps = 0
    clock = names["clk"]
    reset = names["rst_n"]
    for line in lines[header_end:]:
        if line.startswith("#"):
            if rising and state.get(clock) == "1" and state.get(reset) == "1":
                samples.append((time_ps, state.copy()))
            time_ps = int(line[1:])
            rising = False
        elif line.startswith(("b", "B")):
            parts = line.split()
            if len(parts) == 2:
                value, ident = parts[0][1:].lower(), parts[1]
                old = state.get(ident)
                state[ident] = value
                if ident == clock and value == "1" and old == "0":
                    rising = True
        elif line and line[0] in "01xXzZ":
            ident, value = line[1:].strip(), line[0].lower()
            old = state.get(ident)
            state[ident] = value
            if ident == clock and value == "1" and old == "0":
                rising = True
    return names, samples


def value(state, names, name):
    ident = names.get(name)
    if ident is None:
        return None
    bits = state.get(ident, "x")
    if not bits or any(bit not in "01" for bit in bits):
        return None
    return int(bits, 2)


def mnemonic(word):
    if word is None:
        return "-"
    op = (word >> 12) & 15
    rd, rs1, rs2 = (word >> 9) & 7, (word >> 6) & 7, (word >> 3) & 7
    imm, addr = word & 255, word & 511
    if op == 0:
        return "NOP"
    if op == 1:
        return f"LDI R{rd},{imm}"
    if op == 2:
        return f"LD R{rd},[R{rs1}]"
    if op == 3:
        return f"ST [R{rs1}],R{rd}"
    if op in (4, 5, 6, 7, 8):
        return f"{('ADD', 'SUB', 'AND', 'OR', 'XOR')[op - 4]} R{rd},R{rs1},R{rs2}"
    if op in (9, 10):
        return f"{'SHL' if op == 9 else 'SHR'} R{rd},R{rs1}"
    if op == 11:
        return f"CMP R{rs1},R{rs2}"
    if op == 12:
        return f"JMP {addr}"
    if op == 13:
        return f"{BRANCH_NAMES[rd]} {addr}"
    if op == 14:
        return f"{'OUT' if (word >> 8) & 1 else 'IN'} {imm}"
    if op == 15:
        return "HLT"
    return "?"


def stage(state, names, prefix):
    if value(state, names, prefix + "_valid") != 1:
        return "-"
    pc = value(state, names, prefix + "_pc")
    ir = value(state, names, prefix + "_ir")
    return f"{pc:03X} {mnemonic(ir)}" if pc is not None else mnemonic(ir)


def has_forwarding(state, names):
    if value(state, names, "s2_valid") != 1:
        return False
    if value(state, names, "s3_valid") != 1 or value(state, names, "s3_rf_we") != 1:
        return False
    dest = value(state, names, "s3_rf_addr")
    ir = value(state, names, "s2_ir")
    if dest is None or ir is None:
        return False
    opcode = (ir >> 12) & 15
    sources = []
    if opcode in (2, 9, 10):
        sources = [(ir >> 6) & 7]
    elif opcode == 3:
        sources = [(ir >> 6) & 7, (ir >> 9) & 7]
    elif opcode in (4, 5, 6, 7, 8, 11):
        sources = [(ir >> 6) & 7, (ir >> 3) & 7]
    elif opcode == 14 and (ir & 0x100):
        sources = [(ir >> 9) & 7]
    return dest in sources


def make_svg(main_names, main_samples, load_names, load_samples, io_names, io_samples):
    first_active = next(
        (i for i, (_, state) in enumerate(main_samples)
         if any(value(state, main_names, p + "_valid") == 1 for p in ("s1", "s2", "s3"))),
        None,
    )
    if first_active is None:
        raise RuntimeError("The timing simulation has no valid pipeline stages.")
    rows = main_samples[first_active:first_active + 8]
    if len(rows) < 8:
        raise RuntimeError("The timing simulation produced fewer than eight active cycles.")

    first_retire = next(
        (i for i, (_, state) in enumerate(rows, start=1)
         if value(state, main_names, "retire") == 1
         and value(state, main_names, "retire_pc") == 0),
        None,
    )
    forward_cycle = next(
        (i for i, (_, state) in enumerate(rows, start=1) if has_forwarding(state, main_names)),
        None,
    )
    branch_cycle = next(
        (i for i, (_, state) in enumerate(rows, start=1)
         if value(state, main_names, "branch_taken") == 1),
        None,
    )
    if (first_retire, forward_cycle, branch_cycle) != (3, 4, 8):
        raise RuntimeError(
            "The simulated timing changed: expected first retire at cycle 3, "
            f"forwarding at cycle 4, and branch at cycle 8; got "
            f"{first_retire}, {forward_cycle}, {branch_cycle}."
        )

    stall_indexes = [
        i for i, (_, state) in enumerate(load_samples)
        if value(state, load_names, "load_use_stall") == 1
    ]
    if len(stall_indexes) < 4:
        raise RuntimeError("The load-use repro did not show a repeated stall.")
    stall_times = [load_samples[i][0] // 1000 for i in stall_indexes[:3]]
    repeated_retire_pc = [
        value(load_samples[i][1], load_names, "retire_pc") for i in stall_indexes[1:4]
    ]
    if len(set(repeated_retire_pc)) != 1:
        raise RuntimeError("The expected repeated LD retirement was not observed.")

    io_stall_times = [
        time_ps // 1000 for time_ps, state in io_samples
        if value(state, io_names, "io_stall") == 1
    ]
    if not io_stall_times:
        raise RuntimeError("The slow-I/O simulation did not assert io_stall.")

    x = [230, 375, 700, 1025, 1350, 1745]
    widths = [140, 315, 315, 315, 375, 390]
    headers = ("Cycle", "Time (ns)", "Fetch (s1)", "Execute (s2)", "Writeback (s3)", "Event")
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="2160" height="850" viewBox="0 0 2160 850">',
        "<style>text{font-family:Arial,Helvetica,sans-serif;fill:#172033}.title{font-size:30px;font-weight:bold}.sub{font-size:18px}.head{font-size:18px;font-weight:bold}.cell{font-size:17px}.note{font-size:17px}.mono{font-family:Consolas,monospace}</style>",
        '<rect width="2160" height="850" fill="#fff"/>',
        '<text class="title" x="36" y="48">DSD-8 pipeline timing: first 8 active cycles from a real Icarus simulation</text>',
        '<text class="sub" x="36" y="80">Cycle 1 is the first valid fetch; each clock is 10 ns. Signal times below are simulator times.</text>',
    ]
    header_y, row_h = 110, 50
    for col, text in enumerate(headers):
        svg.append(f'<rect x="{x[col]}" y="{header_y}" width="{widths[col]}" height="42" fill="#e2e8f0" stroke="#94a3b8"/>')
        svg.append(f'<text class="head" x="{x[col] + 10}" y="{header_y + 27}">{text}</text>')

    fills = ("#dbeafe", "#fef3c7", "#dcfce7")
    stages = ("s1", "s2", "s3")
    for cycle, (time_ps, state) in enumerate(rows, start=1):
        y = header_y + 42 + (cycle - 1) * row_h
        event = []
        if cycle == first_retire:
            event.append("FIRST RETIRE (PC 000)")
        if has_forwarding(state, main_names):
            event.append("forward: s3_rf_data -> a,b")
        if value(state, main_names, "branch_taken") == 1:
            event.append("branch_taken; fetch flushed")
        cells = (
            str(cycle),
            str(time_ps // 1000),
            stage(state, main_names, "s1"),
            stage(state, main_names, "s2"),
            stage(state, main_names, "s3"),
            "  ".join(event) if event else "-",
        )
        for col, text in enumerate(cells):
            fill = fills[col - 2] if col in (2, 3, 4) else ("#fff7ed" if event else "#fff")
            svg.append(f'<rect x="{x[col]}" y="{y}" width="{widths[col]}" height="{row_h}" fill="{fill}" stroke="#cbd5e1"/>')
            weight = ' font-weight="bold"' if event and col == 5 else ""
            svg.append(f'<text class="cell" x="{x[col] + 10}" y="{y + 31}"{weight}>{text}</text>')

    panel_y = header_y + 42 + 8 * row_h + 28
    svg += [
        f'<rect x="36" y="{panel_y}" width="2078" height="145" rx="14" fill="#fff1f2" stroke="#be123c" stroke-width="3"/>',
        f'<text class="head" x="58" y="{panel_y + 34}">Load-use repro from a separate real simulation: repeated stall, not a one-cycle bubble</text>',
        f'<text class="note" x="58" y="{panel_y + 68}">load_use_stall = 1 at {", ".join(str(t) for t in stall_times)} ns and continues beyond these samples.</text>',
        f'<text class="note" x="58" y="{panel_y + 98}">s1 and s2 stay on the same instructions; then retire_pc={repeated_retire_pc[0]} repeats. This is a current RTL bug.</text>',
        f'<text class="note mono" x="58" y="{panel_y + 128}">Wave: doc/simple/load_use_repro.vcd   Slow I/O wave: doc/simple/slow_io_example.vcd, io_stall starts at {io_stall_times[0]} ns</text>',
        "</svg>",
    ]
    DOC.mkdir(parents=True, exist_ok=True)
    (DOC / "pipeline_timing.svg").write_text("\n".join(svg), encoding="utf-8")
    return stall_times, io_stall_times


def main():
    require_tool("iverilog")
    require_tool("vvp")
    build = ROOT / "build"
    build.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="dsd8-simple-", dir=build) as temp:
        work = pathlib.Path(temp)
        main_vcd, main_out = simulate(TIMING_PROGRAM, work / "timing", "timing")
        load_vcd, load_out = simulate(LOAD_USE_PROGRAM, work / "load_use", "load_use", 12)
        slow_source = (ROOT / "tests" / "conformance" / "extra_t34_slow_echo.asm").read_text(encoding="utf-8")
        io_vcd, io_out = simulate(slow_source, work / "slow_io", "slow_io")
        DOC.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(main_vcd, DOC / "pipeline_example.vcd")
        shutil.copyfile(load_vcd, DOC / "load_use_repro.vcd")
        shutil.copyfile(io_vcd, DOC / "slow_io_example.vcd")

        main_names, main_samples = read_samples(main_vcd)
        load_names, load_samples = read_samples(load_vcd)
        io_names, io_samples = read_samples(io_vcd)
        stall_times, io_stall_times = make_svg(
            main_names, main_samples, load_names, load_samples, io_names, io_samples
        )
        print("Timing simulation: 8-instruction program completed.")
        if "hit MAX_CYCLES" in load_out:
            print("Load-use reproduction: hit the short cycle limit as expected.")
        print(f"load_use_stall observed at {', '.join(map(str, stall_times))} ns and repeats.")
        print(f"io_stall observed at {io_stall_times[0]} ns in the slow-I/O example.")
        if "hit MAX_CYCLES" in main_out or "hit MAX_CYCLES" in io_out:
            raise RuntimeError("A required timing simulation did not reach HLT.")
    print(f"Wrote {DOC / 'pipeline_timing.svg'} and three presentation VCD files.")


if __name__ == "__main__":
    main()
