# Interactive DSD-8 visualizer

Run it from the repository root in PowerShell:

```powershell
python scripts/run_visualizer.py
```

The local page opens in your browser. Paste assembly into the editor and select **Run RTL**. The app assembles the program, runs the existing RTL test harness, and animates the recorded clock cycles. It does not approximate the processor with the Python reference simulator.

Use **Play**, **Pause**, **Step back**, **Step forward**, or the cycle slider. The display shows Fetch, Execute, and Writeback; register values; flags; the first 16 data-memory bytes; ALU inputs and result; I/O; and retired instructions. A cycle limit prevents an infinite loop from running forever.

The server listens on `127.0.0.1:8765` only. Stop it with **Ctrl+C** in PowerShell. It needs Python, Icarus Verilog (`iverilog` and `vvp`), and the existing DSD-8 assembler. It adds no packages and does not modify RTL or tests.

