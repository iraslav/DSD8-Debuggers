# DSD-8 Bug Log

“Time to find” is intentionally left blank for the project team to complete.
This checkout has one baseline commit; the entries below are verified against
that baseline and the current RTL/testbench diffs, rather than a multi-commit
fix history.

| id | description | found by (unit test / conformance diff / review / inspection) | time to find | fix |
|---|---|---|---|---|
| B-01 | A stale `if (s3_valid) retire_r <= 1'b1;` referenced undeclared/unneeded `retire_r` state. | RTL inspection / compile review | __________ | Removed the dead two-line assignment; architectural retirement remains the public `retire`/`retire_*` outputs. |
| B-02 | `expected_result(fa, fb, fop)[7]` selected a bit directly from a function call, which Icarus rejected as malformed Verilog. | Unit-test compile (`make test`) | __________ | Store the function's 8-bit return in a temporary `reg [7:0]`, then select bit 7. |
| B-03 | A conditional branch could consume stale architectural flags when the immediately preceding flag-setting operation was in writeback. | Conformance trace diff | __________ | Select the pending `s3_flags` when `s3_valid && s3_flags_we`; otherwise use `flags_out`. |
| B-04 | `halted` asserted while HLT was still in decode/execute, before HLT retired, truncating the final retirement event. | Conformance trace diff | __________ | Latch `halted_r` when HLT reaches the sequential control point and assert public `halted` after `s3_valid` drains. |
| B-05 | A prior I/O wait held the retirement-stage instruction while `retire` stayed asserted, which could count that instruction repeatedly during a multi-cycle wait. | RTL inspection / I/O-stall review | __________ | Gate `retire` with `!io_stall`; the held retirement entry is emitted once when the wait completes. |

