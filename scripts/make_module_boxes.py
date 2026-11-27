#!/usr/bin/env python3
"""Render readable RTL port boxes with Graphviz."""

import argparse
import html
import os
import pathlib
import re
import subprocess


ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "doc" / "schematics"
MODULES = {
    "alu": "rtl/alu.v",
    "register_file": "rtl/register_file.v",
    "flags_reg": "rtl/flags_reg.v",
    "instr_decoder": "rtl/instr_decoder.v",
    "control_unit": "rtl/control_unit.v",
    "prog_counter": "rtl/prog_counter.v",
}


def find_dot_exe():
    candidates = (
        pathlib.Path(r"C:\Program Files\Graphviz\bin\dot.exe"),
        pathlib.Path(r"C:\Program Files (x86)\Graphviz\bin\dot.exe"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate

    for current, directories, files in os.walk("C:\\", onerror=lambda _: None):
        directories[:] = [name for name in directories if name not in ("$Recycle.Bin", "System Volume Information")]
        if "dot.exe" in files:
            return pathlib.Path(current) / "dot.exe"
    raise FileNotFoundError("Could not find dot.exe under C:\\.")


def module_ports(module, source):
    text = source.read_text(encoding="utf-8")
    match = re.search(
        r"\bmodule\s+" + re.escape(module) + r"\s*\((.*?)\)\s*;",
        text,
        re.DOTALL,
    )
    if not match:
        raise ValueError(f"Could not find the {module} port list in {source}.")

    ports = {"input": [], "output": [], "inout": []}
    for raw_line in match.group(1).splitlines():
        line = raw_line.split("//", 1)[0].strip().rstrip(",").strip()
        if not line:
            continue
        declaration = re.match(r"^(input|output|inout)\b(.*)$", line)
        if not declaration:
            raise ValueError(f"Could not parse port declaration {line!r} in {source}.")
        identifiers = re.findall(r"[A-Za-z_]\w*", declaration.group(2))
        if not identifiers:
            raise ValueError(f"Could not parse port name in {line!r} in {source}.")
        ports[declaration.group(1)].append(identifiers[-1])

    if not ports["input"] or not ports["output"]:
        raise ValueError(f"Expected inputs and outputs for module {module}.")
    return ports


def table_cell(title, ports):
    rows = [f"<B>{html.escape(title)}</B>"]
    rows.extend(html.escape(port) for port in ports)
    return "<BR/>".join(rows)


def simple_module_dot(module, ports):
    inputs = ports["input"] + ports["inout"]
    outputs = ports["output"] + ports["inout"]
    return f"""digraph module_box {{
  graph [bgcolor="white", pad="0.3", dpi="180", fontname="Arial"];
  node [shape=plain, fontname="Arial"];
  module [label=<
    <TABLE BORDER="2" CELLBORDER="1" CELLSPACING="0" CELLPADDING="18" COLOR="#475569">
      <TR><TD COLSPAN="2" BGCOLOR="#dbeafe"><FONT FACE="Arial" POINT-SIZE="23"><B>{html.escape(module)}</B></FONT></TD></TR>
      <TR>
        <TD ALIGN="LEFT" VALIGN="TOP" BGCOLOR="#f8fafc"><FONT FACE="Arial" POINT-SIZE="18">{table_cell("Inputs", inputs)}</FONT></TD>
        <TD ALIGN="LEFT" VALIGN="TOP" BGCOLOR="#f8fafc"><FONT FACE="Arial" POINT-SIZE="18">{table_cell("Outputs", outputs)}</FONT></TD>
      </TR>
    </TABLE>
  >];
}}
"""


def cpu_box_dot():
    return """digraph cpu_simple {
  graph [rankdir=LR, bgcolor="white", pad="0.35", nodesep="0.6", ranksep="0.9", splines=polyline, dpi="180", fontname="Arial"];
  node [shape=plain, fontname="Arial"];
  edge [fontname="Arial", fontsize=15, color="#475569", arrowsize=0.8];
  fetch [label=<
    <TABLE BORDER="3" CELLBORDER="0" CELLSPACING="0" CELLPADDING="16" COLOR="#2563eb" BGCOLOR="#dbeafe">
      <TR><TD><FONT FACE="Arial" POINT-SIZE="23"><B>Fetch</B></FONT></TD></TR>
      <TR><TD ALIGN="LEFT"><FONT FACE="Arial" POINT-SIZE="17">pc<BR/>s1_pc, s1_ir, s1_valid<BR/>imem_addr, imem_data<BR/>branch_taken, s2_addr9</FONT></TD></TR>
    </TABLE>
  >];
  execute [label=<
    <TABLE BORDER="3" CELLBORDER="0" CELLSPACING="0" CELLPADDING="16" COLOR="#d97706" BGCOLOR="#fef3c7">
      <TR><TD><FONT FACE="Arial" POINT-SIZE="23"><B>Execute</B></FONT></TD></TR>
      <TR><TD ALIGN="LEFT"><FONT FACE="Arial" POINT-SIZE="17">s2_pc, s2_ir, s2_valid<BR/>s2_decoder · rf · alu_inst<BR/>a, b, alu_result</FONT></TD></TR>
    </TABLE>
  >];
  writeback [label=<
    <TABLE BORDER="3" CELLBORDER="0" CELLSPACING="0" CELLPADDING="16" COLOR="#16a34a" BGCOLOR="#dcfce7">
      <TR><TD><FONT FACE="Arial" POINT-SIZE="23"><B>Writeback</B></FONT></TD></TR>
      <TR><TD ALIGN="LEFT"><FONT FACE="Arial" POINT-SIZE="17">s3_pc, s3_ir, s3_valid<BR/>flags_inst<BR/>retire, retire_pc, retire_ir</FONT></TD></TR>
    </TABLE>
  >];
  dmem [label=<
    <TABLE BORDER="2" CELLBORDER="0" CELLSPACING="0" CELLPADDING="14" COLOR="#0e7490" BGCOLOR="#cffafe">
      <TR><TD><FONT FACE="Arial" POINT-SIZE="20"><B>Data Memory</B></FONT></TD></TR>
      <TR><TD ALIGN="LEFT"><FONT FACE="Arial" POINT-SIZE="16">dmem<BR/>s3_mem_we, s3_mem_addr,<BR/>s3_mem_data, dmem_rdata</FONT></TD></TR>
    </TABLE>
  >];
  io [label=<
    <TABLE BORDER="2" CELLBORDER="0" CELLSPACING="0" CELLPADDING="14" COLOR="#64748b" BGCOLOR="#f1f5f9">
      <TR><TD><FONT FACE="Arial" POINT-SIZE="20"><B>I/O</B></FONT></TD></TR>
      <TR><TD ALIGN="LEFT"><FONT FACE="Arial" POINT-SIZE="16">io_port, io_wdata,<BR/>io_rdata, io_rd, io_wr,<BR/>io_ready</FONT></TD></TR>
    </TABLE>
  >];

  fetch -> execute [color="#2563eb"];
  execute -> writeback [color="#d97706"];
  writeback -> fetch [constraint=false, color="#16a34a"];
  writeback -> dmem [color="#0e7490"];
  dmem -> execute [constraint=false, color="#0e7490"];
  execute -> io [color="#64748b"];
  io -> execute [constraint=false, color="#64748b"];
}
"""


def render(dot_exe, dot_text, output):
    subprocess.run(
        [str(dot_exe), "-Tpng", "-o", str(output)],
        input=dot_text,
        text=True,
        check=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dot-exe", type=pathlib.Path)
    args = parser.parse_args()
    dot_exe = args.dot_exe or find_dot_exe()
    if not dot_exe.is_file():
        raise FileNotFoundError(f"Graphviz executable not found: {dot_exe}")

    OUT.mkdir(parents=True, exist_ok=True)
    for module, relative_source in MODULES.items():
        ports = module_ports(module, ROOT / relative_source)
        output = OUT / f"{module}_simple.png"
        render(dot_exe, simple_module_dot(module, ports), output)
        print(f"Wrote {output}")

    cpu_output = OUT / "cpu_simple.png"
    render(dot_exe, cpu_box_dot(), cpu_output)
    print(f"Wrote {cpu_output}")


if __name__ == "__main__":
    main()
