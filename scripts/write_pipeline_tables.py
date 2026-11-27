import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SIM = ROOT / "sim"
DOC = ROOT / "doc"


def parse_vcd(path):
    lines = path.read_text().splitlines()
    vars_by_name = {}
    scope = []
    end_header = 0

    wanted = {
        "s1_valid", "s1_pc", "s1_ir",
        "s2_valid", "s2_pc", "s2_ir",
        "s3_valid", "s3_pc", "s3_ir",
        "pipeline_stall", "load_use_stall", "branch_taken",
        "retire", "retire_pc", "io_stall",
    }
    for i, line in enumerate(lines):
        parts = line.split()
        if parts and parts[0] == "$scope":
            scope.append(parts[2])
        elif parts and parts[0] == "$upscope":
            scope.pop()
        elif parts and parts[0] == "$var":
            name = parts[4]
            if scope[-2:] == ["tb_dsd8", "uut"] and name in wanted:
                vars_by_name[name] = parts[3]
            elif name in {"clk", "rst_n", "retire", "retire_pc"} and scope[-1:] == ["tb_dsd8"]:
                vars_by_name.setdefault(name, parts[3])
        elif parts and parts[0] == "$enddefinitions":
            end_header = i + 1
            break

    state = {}
    samples = []
    rising = False
    time_ps = 0
    clk_id = vars_by_name.get("clk")
    rst_id = vars_by_name.get("rst_n")

    for line in lines[end_header:]:
        if line.startswith("#"):
            if (rising and clk_id and state.get(clk_id) == "1"
                    and rst_id and state.get(rst_id) == "1"):
                samples.append((time_ps, state.copy()))
            time_ps = int(line[1:])
            rising = False
        elif line and line[0] in "bB":
            parts = line.split()
            if len(parts) == 2:
                ident = parts[1]
                val = parts[0][1:].lower()
                old = state.get(ident)
                state[ident] = val
                if ident == clk_id and val == "1" and old == "0":
                    rising = True
        elif line and line[0] in "01xXzZ":
            ident = line[1:].strip()
            val = line[0].lower()
            old = state.get(ident)
            state[ident] = val
            if ident == clk_id and val == "1" and old == "0":
                rising = True

    return vars_by_name, samples


def bits(state, vars_by_name, name):
    ident = vars_by_name.get(name)
    if ident is None:
        return None
    value = state.get(ident, "x")
    if not value or any(ch not in "01" for ch in value):
        return None
    return int(value, 2)


def mnemonic(ir):
    if ir is None:
        return "-"
    op = (ir >> 12) & 0xf
    rd = (ir >> 9) & 7
    rs1 = (ir >> 6) & 7
    rs2 = (ir >> 3) & 7
    imm = ir & 0xff
    addr = ir & 0x1ff
    names = {
        0: "NOP", 1: f"LDI R{rd},0x{imm:02X}",
        2: f"LD R{rd},[R{rs1}]", 3: f"ST [R{rs1}],R{rd}",
        4: f"ADD R{rd},R{rs1},R{rs2}", 5: f"SUB R{rd},R{rs1},R{rs2}",
        6: f"AND R{rd},R{rs1},R{rs2}", 7: f"OR R{rd},R{rs1},R{rs2}",
        8: f"XOR R{rd},R{rs1},R{rs2}", 9: f"SHL R{rd},R{rs1}",
        10: f"SHR R{rd},R{rs1}", 11: f"CMP R{rs1},R{rs2}",
        12: f"JMP 0x{addr:03X}", 15: "HLT",
    }
    if op == 13:
        names[13] = ["BEQ", "BNE", "BCS", "BCC", "BMI", "BPL", "BVS", "BVC"][(ir >> 9) & 7] + f" 0x{addr:03X}"
    if op == 14:
        names[14] = f"{'OUT' if (ir >> 8) & 1 else 'IN'} 0x{imm:02X},R{rd}"
    return names.get(op, "???")


def stage(state, vars_by_name, stage_name):
    valid = bits(state, vars_by_name, stage_name + "_valid")
    if valid != 1:
        return "-"
    ir = bits(state, vars_by_name, stage_name + "_ir")
    pc = bits(state, vars_by_name, stage_name + "_pc")
    if ir is None:
        return "-"
    pc_text = f"{pc:03X}" if pc is not None else "???"
    return f"{pc_text} {mnemonic(ir)}"


def marker(state, vars_by_name):
    markers = []
    if bits(state, vars_by_name, "pipeline_stall") == 1:
        if bits(state, vars_by_name, "io_stall") == 1:
            markers.append("I/O stall")
        if bits(state, vars_by_name, "load_use_stall") == 1:
            markers.append("load-use stall")
    if bits(state, vars_by_name, "branch_taken") == 1:
        markers.append("flush taken")
    return ", ".join(markers) if markers else "-"


def build_table(path, title):
    vars_by_name, samples = parse_vcd(path)
    out = [f"## {title}", "", "| cycle | time (ns) | IF | ID/EX | EX-WB | marker | retire pc |",
           "|---:|---:|---|---|---|---|---|"]
    cycle = 0
    for time_ps, state in samples:
        cycle += 1
        retire = bits(state, vars_by_name, "retire")
        retire_pc = bits(state, vars_by_name, "retire_pc")
        retire_text = f"{retire_pc:03X}" if retire == 1 and retire_pc is not None else "-"
        out.append(
            f"| {cycle} | {time_ps // 1000} | {stage(state, vars_by_name, 's1')} "
            f"| {stage(state, vars_by_name, 's2')} | {stage(state, vars_by_name, 's3')} "
            f"| {marker(state, vars_by_name)} | {retire_text} |"
        )
    return out


def operation_times(path):
    vars_by_name, samples = parse_vcd(path)
    found = {}
    for time_ps, state in samples:
        ir = bits(state, vars_by_name, "s2_ir")
        valid = bits(state, vars_by_name, "s2_valid")
        if valid != 1 or ir is None:
            continue
        op = (ir >> 12) & 0xf
        label = mnemonic(ir)
        key = label.split()[0]
        if key in {"ADD", "SUB", "AND", "OR", "XOR", "SHL", "SHR", "CMP", "LD", "ST", "BEQ", "BNE", "BCC", "OUT", "HLT"}:
            found.setdefault(key, time_ps // 1000)
        if key == "LDI" and label.startswith("LDI"):
            pass
        if op == 4 and key == "ADD":
            rd = (ir >> 9) & 7
            rs1 = (ir >> 6) & 7
            rs2 = (ir >> 3) & 7
            if rs1 == rs2:
                pass
    return found


def main():
    demo = SIM / "demo_alu_pipeline.vcd"
    b1 = SIM / "b1_multiply_pipeline.vcd"
    lines = ["# DSD-8 Pipeline Tables", ""]
    lines += build_table(demo, "Demo ALU program")
    lines += [""] + build_table(b1, "B.1 Multiply")

    lines += ["", "## Operation timestamps", "",
              "The values below are rising-edge execution times in ns in the ID/EX stage.",
              ""]
    for name, path in (("demo_alu", demo), ("B.1 multiply", b1)):
        lines += [f"### {name}", ""]
        times = operation_times(path)
        if not times:
            lines.append("No operation timestamps found.")
        else:
            for key in ("ADD", "SUB", "AND", "OR", "XOR", "SHL", "SHR", "CMP", "LD", "ST", "BEQ", "BNE", "BCC", "OUT", "HLT"):
                if key in times:
                    lines.append(f"- {key}: {times[key]} ns")
        lines.append("")

    lines += ["- Demo RAW hazard: back-to-back `ADD R6,R5,R2` / `ADD R6,R6,R1`; first ADD reaches ID/EX at the timestamp of the matching ADD.",
              "- Demo load-use: `LD R5,[R4]` followed by `ADD R6,R5,R2`; load-use stall begins at the ADD following the LD.",
              "- Demo branches: `BEQ` and `BNE` execute in ID/EX; marker `flush taken` applies when a taken branch redirects PC.",
              ""]

    DOC.mkdir(parents=True, exist_ok=True)
    (DOC / "pipeline_table.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
