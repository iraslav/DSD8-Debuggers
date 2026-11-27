# DSD-8 Verification Report

**Run date:** 2026-11-21  
**Environment:** Windows PowerShell, GNU make, Icarus Verilog (`iverilog` /
`vvp`), Python supplied with the repository. No WSL or new packages used.

## 1. Objective and scope

This report records the local verification performed for the DSD-8 RTL and
the additional directed test programs. The test strategy combines
module-level self-checking tests, a constrained-random ALU run, and
instruction-level trace comparison against the supplied reference simulator.
The supplied harness `tb/tb_dsd8.v` remains unchanged. Unit tests compile one
selected testbench top at a time; the CPU conformance runner assembles an
image, generates a golden trace with `tools/dsd8sim.py`, runs the RTL, and
reports the first trace mismatch.

The named official conformance cases T01-T40 are not present in the local
checkout. Only the two Appendix B examples were originally available. Five
additional local programs were added to exercise the requested difficult
behaviors; they are useful stress cases, but they are not represented as the
instructor's official T-numbered tests.

The project specification PDF was not found in the repository at verification
time. Consequently, this report uses the requested behaviors, RTL interface
comments, local assembler/reference model, and the project's existing test
conventions as its audit basis. A final course-specification review remains
necessary when the frozen PDF is available.

## 2. Test plan

| layer | command / asset | purpose | pass criterion |
|---|---|---|---|
| Unit RTL | `make test` | Isolate each listed RTL module; exercise directed cases and reset/hold/edge behavior. | Every bench prints `TESTBENCH: PASS`, reports checks, exits successfully. |
| ALU random | `tb/tb_alu_random.v`, included in `make test` | Run 10,000 operand pairs for each of the eight flag-setting opcodes against a separate behavioral model. | At least 80,000 comparisons; zero mismatches; all corner operands present for every opcode and port. |
| CPU integration | `make conformance` | Compare complete retirement traces to the software reference. | Golden and RTL traces match exactly for each local `.asm`. |
| Directed stress | `tests/conformance/extra_*.asm` | Target arithmetic flags, branches, LD flag preservation, SLOW_ECHO, and a 256-iteration loop. | Exact retire trace equality and successful HLT completion. |

### Unit-test inventory

| bench | checks performed |
|---|---|
| `tb_alu.v` | ADD carry/overflow, SUB borrow/overflow, logical flags, shift carry, CMP equality. |
| `tb_alu_example.v` | Worked directed vectors for all operations plus corner operands. |
| `tb_alu_random.v` | Independent reference-model comparison for 80,000 operation/operand pairs, with coverage counts. |
| `tb_register_file.v` | Synchronous active-low reset of all eight registers, old value before a simultaneous write edge, write visibility after edge, and both read ports. |
| `tb_instr_decoder.v` | Worked encodings for NOP, LDI, LD, ST, ADD, CMP, BEQ, JMP, IN, and OUT; checks all overlapping field slices. |
| `tb_flags_reg.v` | Reset precedence, write enable, and disabled hold. |
| `tb_data_memory.v` | All 256 initial bytes are zero, writes to first/last address, independent byte retention. |
| `tb_prog_counter.v` | Reset, increment, branch load, disabled hold, and 9-bit wrap. |
| `tb_instr_memory.v` | `$readmemh` image mapping, asynchronous reads at low and high addresses. |
| `tb_io_bus.v` | Switch/button reads, unmapped read, peripheral readiness/data/request forwarding, and board output writes. |
| `tb_control_unit.v` | Implemented combinational decode for load/store/ALU/CMP/JMP/HLT, all eight branch conditions both ways, and I/O-ready gating. |

The control-unit test is intentionally scoped to the current standalone
module's combinational outputs. `dsd8_cpu` does not instantiate this module;
the module has no valid or I/O-direction input, so it cannot independently
model the integrated pipeline retirement/IN-vs-OUT behavior. The CPU's
retirement and I/O behavior is instead exercised by trace comparison.

## 3. ALU randomized coverage evidence

The constrained-random bench executes 10,000 operand pairs for each opcode
`4` through `B` (80,000 comparisons total). For each opcode the first 25
vectors cover the full 5-by-5 pairing of `00`, `01`, `7F`, `80`, and `FF`;
remaining operands come from a deterministic seeded `$random` stream.
The reference computes arithmetic and flags independently in the testbench.
All result bits and Z/N/C/V are compared.

| op | pairs | C=1 | V=1 | `a` corner hits `[00 01 7F 80 FF]` | `b` corner hits `[00 01 7F 80 FF]` |
|---:|---:|---:|---:|---|---|
| ADD (`4`) | 10,000 | 4,948 | 2,529 | 38, 42, 36, 39, 39 | 44, 49, 41, 39, 46 |
| SUB (`5`) | 10,000 | 4,953 | 2,465 | 44, 52, 42, 46, 43 | 41, 53, 44, 50, 40 |
| AND (`6`) | 10,000 | 0 | 0 | 50, 46, 44, 45, 50 | 32, 45, 35, 46, 57 |
| OR (`7`) | 10,000 | 0 | 0 | 53, 51, 40, 44, 42 | 45, 53, 45, 36, 45 |
| XOR (`8`) | 10,000 | 0 | 0 | 38, 41, 42, 46, 44 | 54, 39, 48, 27, 44 |
| SHL (`9`) | 10,000 | 5,018 | 0 | 46, 39, 51, 46, 37 | 36, 49, 47, 40, 38 |
| SHR (`A`) | 10,000 | 5,015 | 0 | 42, 43, 44, 36, 48 | 48, 47, 36, 38, 39 |
| CMP (`B`) | 10,000 | 5,086 | 2,484 | 41, 52, 39, 42, 41 | 50, 45, 37, 39, 46 |

Observed final line: `CHECK SUMMARY: 80000 comparisons, 0 errors`; the bench
printed `TESTBENCH: PASS`. Corner hit counts exceed the deliberate directed
minimum because random values can also equal a corner. Coverage counts are
evidence only; they are not used as assertions beyond ensuring the total
comparison count.

## 4. Integration stress programs

The five programs below were assembled by `tools/dsd8asm.py`; expected traces
were generated by `tools/dsd8sim.py`; and the DUT traces were compared by the
same runner as the original samples.

| local case | exercised behavior | result |
|---|---|---|
| `extra_t15_t17_arithmetic_flags.asm` | ADD carry/overflow, SUB borrow/overflow, CMP flags | PASS |
| `extra_t24_t25_branch_conditions.asm` | All eight Bcc conditions, with both taken and not-taken cases | PASS |
| `extra_t14_ld_preserves_flags.asm` | LD retains flags so a following BNE observes the earlier CMP | PASS |
| `extra_t34_slow_echo.asm` | OUT then IN at SLOW_ECHO port `0x40`, including peripheral wait | PASS |
| `extra_t30_256_iteration_loop.asm` | Counter wraparound executes a 256-iteration loop | PASS |

The local T30-style loop retires 773 instructions including setup, loop body,
OUT, and HLT. The local T34-style program retires four instructions and
observes the written `0xA6` byte on IN. In addition, `sample01_multiply`
matches its 51-instruction expected trace (R3=91, LEDs=`0x5B`), and
`sample02_popcount` matches its 44-instruction expected trace (R2=6).
Final conformance output was **7 / 7 passed**.

## 5. Results and known limits

Final local results:

- `make test`: **11 / 11 passed**.
- `make conformance`: **7 / 7 passed** (two samples plus five local stress cases).
- ALU constrained-random comparisons: **80,000 / 80,000 passed**.

The following remain outside the evidence collected here:

1. The official T01-T40 suite is unavailable locally. Five similarly targeted
   programs do not substitute for the unavailable official test vectors.
2. The exact instructor T13 and T30 long-program workloads were not run. The
   authored 256-iteration loop only checks the specific local loop described
   above.
3. The T34 reference simulator models I/O functionally and completes requests
   immediately; it does not model peripheral wall-clock latency. The RTL
   SLOW_ECHO peripheral does delay `io_ready`, but trace equality proves
   architectural completion/data, not an exact stall-cycle count. Dedicated
   cycle-level assertions for all possible 0-7 cycle delays are not included.
4. The CPU load-use detector compares multiple raw fields without decoding the
   following instruction's true source fields. Tests exercise representative
   loads but do not prove absence of all unnecessary stalls or all pipeline
   interlock cases.
5. Standalone `control_unit` behavior is not used by the CPU. Its interface
   lacks a validity bit and a direction bit, so the standalone output cannot
   establish integrated retirement or distinguish IN from OUT.
6. This is simulation evidence with Icarus, not formal verification, FPGA
   timing closure, synthesis-to-board validation, or a full random CPU
   instruction stream.
7. The specification PDF is absent in this checkout; final requirement IDs,
   encoding examples, and all report wording must be reconciled with the
   frozen course document before submission.

## 6. Closure argument

The submitted local changes close the verifiable defects and requirements
within this checkout: all named module benches pass; the ALU has 10,000
seeded pairs per flag-setting operation with explicit corner coverage; and
both reference samples plus the five focused programs match the golden
retirement traces exactly. The strongest evidence is the agreement of three
independent layers: directed unit checks, randomized ALU checks against a
separate behavioral model, and end-to-end RTL/reference trace comparisons.

This is a defensible local closure, not a claim that the confidential official
suite, cycle-accurate T34 latency requirements, or unavailable PDF audit have
been completed. Those gaps are explicit and should be closed when the
instructor suite and specification are available.
