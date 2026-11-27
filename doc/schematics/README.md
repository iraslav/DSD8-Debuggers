# DSD-8 schematics

- `alu_schematic.png` — ALU gate-level logic; appendix (complex).
- `register_file_schematic.png` — Register-file gate-level logic; appendix (complex).
- `flags_reg_schematic.png` — Flags-register gate-level logic; appendix (complex).
- `instr_decoder_schematic.png` — Instruction-decoder gate-level logic; appendix (complex).
- `control_unit_schematic.png` — Control-unit gate-level logic; appendix (complex).
- `prog_counter_schematic.png` — Program-counter gate-level logic; appendix (complex).
- `cpu_blocks.png` — Hierarchical dsd8_cpu with its actual instances; appendix (complex).
- `cpu_blocks.svg` — Zoomable hierarchical dsd8_cpu drawing; appendix (complex).
- `alu_simple.png` — ALU input and output port names in one box; present this (simple).
- `register_file_simple.png` — Register-file input and output port names in one box; present this (simple).
- `flags_reg_simple.png` — Flags-register input and output port names in one box; present this (simple).
- `instr_decoder_simple.png` — Decoder input and output port names in one box; present this (simple).
- `control_unit_simple.png` — Control-unit input and output port names in one box; present this (simple).
- `prog_counter_simple.png` — Program-counter input and output port names in one box; present this (simple).
- `cpu_simple.png` — Five high-level CPU boxes with stage colors; present this (simple).

The `cpu_blocks` hierarchy contains `instr_decoder`, `register_file`, `alu`, `flags_reg`, and `data_memory` instances.
`dsd8_cpu` does not instantiate `prog_counter` or `control_unit`; its PC and opcode control are implemented inside the CPU module.
