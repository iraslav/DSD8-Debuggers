#!/usr/bin/env python3
"""Serve a local browser UI for cycle-by-cycle DSD-8 RTL simulations."""

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


ROOT = pathlib.Path(__file__).resolve().parent.parent
WEB = ROOT / "tools" / "visualizer"
RTL_SOURCES = (
    "rtl/alu.v",
    "rtl/control_unit.v",
    "rtl/data_memory.v",
    "rtl/dsd8_cpu.v",
    "rtl/dsd8_top.v",
    "rtl/flags_reg.v",
    "rtl/instr_decoder.v",
    "rtl/instr_memory.v",
    "rtl/io_bus.v",
    "rtl/prog_counter.v",
    "rtl/register_file.v",
    "sim/peripherals.v",
    "tb/tb_dsd8.v",
    "tb/wave_dump.v",
)
MAX_BODY_BYTES = 64 * 1024
MAX_CYCLES = 1000
BRANCH_NAMES = ("BEQ", "BNE", "BCS", "BCC", "BMI", "BPL", "BVS", "BVC")

TOP_SIGNALS = {
    "clk", "rst_n", "retire", "retire_pc", "retire_ir", "retire_rf_we",
    "retire_rf_addr", "retire_rf_data", "retire_mem_we", "retire_mem_addr",
    "retire_mem_data", "retire_flags", "halted", "io_port", "io_wdata",
    "io_rdata", "io_rd", "io_wr", "io_ready", "leds",
}
CPU_SIGNALS = {
    "pc",
    "s1_pc", "s1_ir", "s1_valid",
    "s2_pc", "s2_ir", "s2_valid", "s2_opcode", "s2_rs1", "s2_ra2",
    "s3_pc", "s3_ir", "s3_valid", "s3_rf_we", "s3_rf_addr", "s3_rf_data",
    "pipeline_stall", "load_use_stall", "io_stall", "branch_taken",
    "a", "b", "alu_result", "alu_flags", "flags_out",
}


class SimulationError(Exception):
    pass


def run_command(command, cwd, timeout=30):
    command_line = subprocess.list2cmdline([str(part) for part in command])
    try:
        result = subprocess.run(
            command, cwd=cwd, env=os.environ.copy(), text=True, capture_output=True,
            timeout=timeout
        )
    except OSError as error:
        raise SimulationError(
            f"Failed to start command:\n{command_line}\n{error}"
        ) from error
    except subprocess.TimeoutExpired as error:
        raise SimulationError(
            f"Command timed out after {timeout} seconds:\n{command_line}"
        ) from error
    if result.returncode:
        details = []
        if result.stdout.strip():
            details.append("stdout:\n" + result.stdout.strip())
        if result.stderr.strip():
            details.append("stderr:\n" + result.stderr.strip())
        message = f"Command failed with exit code {result.returncode}:\n{command_line}"
        if details:
            message += "\n\n" + "\n\n".join(details)
        raise SimulationError(message)
    return result


def decode_instruction(word):
    opcode = (word >> 12) & 15
    rd = (word >> 9) & 7
    rs1 = (word >> 6) & 7
    rs2 = (word >> 3) & 7
    imm = word & 255
    address = word & 511
    if opcode == 0:
        return "NOP"
    if opcode == 1:
        return f"LDI R{rd},{imm}"
    if opcode == 2:
        return f"LD R{rd},[R{rs1}]"
    if opcode == 3:
        return f"ST [R{rs1}],R{rd}"
    if opcode in (4, 5, 6, 7, 8):
        names = ("ADD", "SUB", "AND", "OR", "XOR")
        return f"{names[opcode - 4]} R{rd},R{rs1},R{rs2}"
    if opcode in (9, 10):
        return f"{'SHL' if opcode == 9 else 'SHR'} R{rd},R{rs1}"
    if opcode == 11:
        return f"CMP R{rs1},R{rs2}"
    if opcode == 12:
        return f"JMP 0x{address:03X}"
    if opcode == 13:
        return f"{BRANCH_NAMES[rd]} 0x{address:03X}"
    if opcode == 14:
        return f"{'OUT' if (word >> 8) & 1 else 'IN'} 0x{imm:02X},R{rd}"
    return "HLT"


def read_vcd_samples(path):
    names = {}
    scopes = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    data_start = 0
    for index, line in enumerate(lines):
        parts = line.split()
        if parts and parts[0] == "$scope":
            scopes.append(parts[2])
        elif parts and parts[0] == "$upscope":
            scopes.pop()
        elif parts and parts[0] == "$var" and len(parts) >= 5:
            name, identifier = parts[4], parts[3]
            if scopes == ["tb_dsd8"] and name in TOP_SIGNALS:
                names[name] = identifier
            elif scopes == ["tb_dsd8", "uut"] and name in CPU_SIGNALS:
                names["uut." + name] = identifier
        elif parts and parts[0] == "$enddefinitions":
            data_start = index + 1
            break

    required = ("clk", "rst_n", "retire", "retire_pc", "retire_ir")
    missing = [name for name in required if name not in names]
    if missing:
        raise SimulationError("VCD lacks required signals: " + ", ".join(missing))

    state = {}
    samples = []
    rising = False
    time_ps = 0
    clock_id = names["clk"]
    reset_id = names["rst_n"]
    for line in lines[data_start:]:
        if line.startswith("#"):
            if rising and state.get(clock_id) == "1" and state.get(reset_id) == "1":
                samples.append((time_ps, state.copy()))
            time_ps = int(line[1:])
            rising = False
        elif line.startswith(("b", "B")):
            parts = line.split()
            if len(parts) == 2:
                value, identifier = parts[0][1:].lower(), parts[1]
                old = state.get(identifier)
                state[identifier] = value
                if identifier == clock_id and value == "1" and old == "0":
                    rising = True
        elif line and line[0] in "01xXzZ":
            identifier, value = line[1:].strip(), line[0].lower()
            old = state.get(identifier)
            state[identifier] = value
            if identifier == clock_id and value == "1" and old == "0":
                rising = True
    return names, samples


def signal_value(state, names, name):
    identifier = names.get(name)
    if identifier is None:
        return None
    bits = state.get(identifier, "x")
    if not bits or any(bit not in "01" for bit in bits):
        return None
    return int(bits, 2)


def stage_snapshot(state, names, stage_name):
    prefix = "uut." + stage_name
    valid = signal_value(state, names, prefix + "_valid") == 1
    pc = signal_value(state, names, prefix + "_pc")
    ir = signal_value(state, names, prefix + "_ir")
    if not valid or pc is None or ir is None:
        return {"valid": False, "pc": None, "ir": None, "text": "Bubble"}
    return {"valid": True, "pc": pc, "ir": ir, "text": decode_instruction(ir)}


def simulate(assembly, cycle_limit):
    iverilog_path = shutil.which("iverilog")
    vvp_path = shutil.which("vvp")
    iverilog = str(pathlib.Path(iverilog_path).resolve()) if iverilog_path else None
    vvp = str(pathlib.Path(vvp_path).resolve()) if vvp_path else None
    if not iverilog or not vvp:
        raise SimulationError("Icarus Verilog is required. Add iverilog and vvp to PATH.")

    with tempfile.TemporaryDirectory(prefix="dsd8-visualizer-") as temp_name:
        work = pathlib.Path(temp_name)
        sim_dir = work / "sim"
        sim_dir.mkdir()
        asm_path = work / "program.asm"
        image_path = work / "program.hex"
        binary_path = work / "dsd8.vvp"
        asm_path.write_text(assembly, encoding="utf-8")

        run_command(
            [sys.executable, str(ROOT / "tools" / "dsd8asm.py"),
             str(asm_path), "-o", str(image_path)],
            cwd=ROOT,
        )
        words = image_path.read_text(encoding="ascii").splitlines()
        if len(words) > 512:
            raise SimulationError("This program is longer than the 512-word instruction memory.")
        if not words:
            raise SimulationError("Enter at least one instruction.")

        sources = [str(ROOT / source) for source in RTL_SOURCES]
        run_command(
            [iverilog, "-g2005", f"-Ptb_dsd8.MAX_CYCLES={cycle_limit}",
             "-o", str(binary_path)] + sources,
            cwd=ROOT,
        )
        simulation = run_command([vvp, str(binary_path)], cwd=work, timeout=45)
        vcd_path = sim_dir / "dsd8_pipeline.vcd"
        if not vcd_path.is_file():
            raise SimulationError(
                "Simulation finished without a VCD file.\n" + simulation.stdout + simulation.stderr
            )
        names, samples = read_vcd_samples(vcd_path)

        first_active = next(
            (index for index, (_, state) in enumerate(samples)
             if any(signal_value(state, names, "uut." + stage + "_valid") == 1
                    for stage in ("s1", "s2", "s3"))),
            None,
        )
        if first_active is None:
            raise SimulationError("Simulation produced no valid pipeline cycles.")
        samples = samples[first_active:]

        registers = [0] * 8
        memory = [0] * 256
        flags = 0
        cycles = []
        for cycle_number, (time_ps, state) in enumerate(samples, start=1):
            retired = signal_value(state, names, "retire") == 1
            retire_flags = signal_value(state, names, "retire_flags")
            rf_write = None
            mem_write = None
            retire_pc = signal_value(state, names, "retire_pc")
            retire_ir = signal_value(state, names, "retire_ir")
            if retired:
                rf_we = signal_value(state, names, "retire_rf_we") == 1
                if rf_we:
                    address = signal_value(state, names, "retire_rf_addr")
                    data = signal_value(state, names, "retire_rf_data")
                    if address is not None and data is not None:
                        registers[address] = data
                        rf_write = {"address": address, "data": data}
                mem_we = signal_value(state, names, "retire_mem_we") == 1
                if mem_we:
                    address = signal_value(state, names, "retire_mem_addr")
                    data = signal_value(state, names, "retire_mem_data")
                    if address is not None and data is not None:
                        memory[address] = data
                        mem_write = {"address": address, "data": data}
                if retire_flags is not None:
                    flags = retire_flags

            s2_valid = signal_value(state, names, "uut.s2_valid") == 1
            s3_valid = signal_value(state, names, "uut.s3_valid") == 1
            s3_we = signal_value(state, names, "uut.s3_rf_we") == 1
            s3_addr = signal_value(state, names, "uut.s3_rf_addr")
            s2_rs1 = signal_value(state, names, "uut.s2_rs1")
            s2_ra2 = signal_value(state, names, "uut.s2_ra2")
            events = {
                "retire": retired,
                "branchTaken": signal_value(state, names, "uut.branch_taken") == 1,
                "loadUseStall": signal_value(state, names, "uut.load_use_stall") == 1,
                "ioStall": signal_value(state, names, "uut.io_stall") == 1,
                "pipelineStall": signal_value(state, names, "uut.pipeline_stall") == 1,
                "forwardA": bool(s2_valid and s3_valid and s3_we and s3_addr is not None
                                 and s3_addr == s2_rs1),
                "forwardB": bool(s2_valid and s3_valid and s3_we and s3_addr is not None
                                 and s3_addr == s2_ra2),
            }
            cycles.append({
                "cycle": cycle_number,
                "timeNs": time_ps // 1000,
                "fetch": stage_snapshot(state, names, "s1"),
                "execute": stage_snapshot(state, names, "s2"),
                "writeback": stage_snapshot(state, names, "s3"),
                "events": events,
                "commit": {
                    "pc": retire_pc if retired else None,
                    "ir": retire_ir if retired else None,
                    "rfWrite": rf_write,
                    "memWrite": mem_write,
                    "flags": flags,
                },
                "registers": list(registers),
                "memoryHead": memory[:16],
                "alu": {
                    "a": signal_value(state, names, "uut.a"),
                    "b": signal_value(state, names, "uut.b"),
                    "result": signal_value(state, names, "uut.alu_result"),
                    "flags": signal_value(state, names, "uut.alu_flags"),
                },
                "io": {
                    "port": signal_value(state, names, "io_port"),
                    "writeData": signal_value(state, names, "io_wdata"),
                    "readData": signal_value(state, names, "io_rdata"),
                    "read": signal_value(state, names, "io_rd"),
                    "write": signal_value(state, names, "io_wr"),
                    "ready": signal_value(state, names, "io_ready"),
                    "leds": signal_value(state, names, "leds"),
                },
                "halted": signal_value(state, names, "halted") == 1,
            })

        program = [
            {"pc": pc, "word": word.upper(), "text": decode_instruction(int(word, 16))}
            for pc, word in enumerate(words)
        ]
        hit_limit = "hit MAX_CYCLES" in simulation.stdout
        return {
            "program": program,
            "cycles": cycles,
            "cycleCount": len(cycles),
            "hitLimit": hit_limit,
            "halted": any(cycle["halted"] for cycle in cycles),
        }


class Handler(BaseHTTPRequestHandler):
    server_version = "DSD8Visualizer/1.0"

    def send_json(self, status, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/api/health":
            self.send_json(200, {"ok": True})
            return
        static_files = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/app.js": ("app.js", "text/javascript; charset=utf-8"),
            "/style.css": ("style.css", "text/css; charset=utf-8"),
        }
        asset = static_files.get(self.path)
        if asset is None:
            self.send_json(404, {"error": "Not found."})
            return
        path = WEB / asset[0]
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", asset[1])
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self';",
        )
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/simulate":
            self.send_json(404, {"error": "Not found."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(400, {"error": "Invalid Content-Length."})
            return
        if length <= 0 or length > MAX_BODY_BYTES:
            self.send_json(413, {"error": "Request must be between 1 byte and 64 KB."})
            return
        try:
            request = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_json(400, {"error": "Request body must be valid UTF-8 JSON."})
            return
        if not isinstance(request, dict) or not isinstance(request.get("assembly"), str):
            self.send_json(400, {"error": "Provide assembly text in the 'assembly' field."})
            return
        assembly = request["assembly"]
        if not assembly.strip():
            self.send_json(400, {"error": "Enter at least one instruction."})
            return
        if len(assembly.encode("utf-8")) > 48 * 1024:
            self.send_json(413, {"error": "Assembly text is too large."})
            return
        cycle_limit = request.get("cycleLimit", 250)
        if isinstance(cycle_limit, bool) or not isinstance(cycle_limit, int):
            self.send_json(400, {"error": "cycleLimit must be an integer."})
            return
        if not 1 <= cycle_limit <= MAX_CYCLES:
            self.send_json(400, {"error": f"cycleLimit must be from 1 to {MAX_CYCLES}."})
            return
        try:
            result = simulate(assembly, cycle_limit)
        except SimulationError as error:
            self.send_json(422, {"error": str(error)})
            return
        self.send_json(200, result)

    def log_message(self, format_string, *args):
        print("%s - %s" % (self.address_string(), format_string % args))


def main():
    parser = argparse.ArgumentParser(description="Open the local DSD-8 pipeline visualizer.")
    parser.add_argument("--host", default="127.0.0.1", help="bind address (default: localhost only)")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true", help="do not open a browser automatically")
    args = parser.parse_args()
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        parser.error("For safety, the visualizer only binds to localhost.")

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{server.server_port}/"
    print(f"DSD-8 visualizer ready at {url}")
    print("Press Ctrl+C to stop the local server.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping DSD-8 visualizer.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
