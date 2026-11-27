# Simple presentation pack — file list and demo waves

## Files created

- `block_diagram.svg` and `block_diagram.png` — six-box overview.
- `pipeline_timing.svg` — first eight active cycles from a real simulation.
- `hazards.md` — four short hazard notes. It calls out the repeated load-use stall.
- `instruction_cheatsheet.md` — the 16 opcode families in one table.
- `presentation_script.md` — three speaking parts and five viva answers.
- `pipeline_example.vcd` — the simulated eight-instruction example.
- `load_use_repro.vcd` — the repeated load-use stall.
- `slow_io_example.vcd` — the slow I/O wait.
- `scripts/make_simple_diagram.py` and `scripts/make_pipeline_timing.py` — generators.

## Three demo waves

Run these commands from the repository root in PowerShell.

```powershell
gtkwave sim/demo_alu_pipeline.vcd
```

Zoom to **75 ns** for the ADD in Execute and its ALU result. Also see the taken branch at **225 ns**.

```powershell
gtkwave sim/b1_multiply_pipeline.vcd
```

Zoom to **715 ns** for the final OUT in Writeback and the multiply result.

```powershell
gtkwave doc/simple/pipeline_example.vcd
```

Zoom to **85 ns** for ADD-to-SUB forwarding. Zoom to **115 ns** for the taken branch and flush.

## Other hazard screenshots

```powershell
gtkwave doc/simple/load_use_repro.vcd
```

Zoom to **85–115 ns**. `load_use_stall` repeats, and `retire_pc` repeats.

```powershell
gtkwave doc/simple/slow_io_example.vcd
```

Zoom to **65–125 ns**. The OUT wait is 65–95 ns. The IN wait is at 115 ns.

The load-use trace is an observed current-RTL bug. It is not a one-cycle bubble.
