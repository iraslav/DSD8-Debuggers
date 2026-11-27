# Pipeline hazards

| Problem | Our fix | Wave signal to point at |
|---|---|---|
| A later instruction can need a register before its new value is written. | The `a` and `b` inputs can use the newest `s3_rf_data` value when the register addresses match. | `tb_dsd8.uut.s3_rf_we`, `tb_dsd8.uut.s3_rf_addr`, `tb_dsd8.uut.s3_rf_data`, `tb_dsd8.uut.a`, `tb_dsd8.uut.b` |
| An instruction can need a value that is still being loaded. | This RTL raises `load_use_stall`, but the stall repeats; it is not yet a one-cycle fix. | `tb_dsd8.uut.load_use_stall`, `tb_dsd8.uut.s1_valid`, `tb_dsd8.uut.s2_valid`, `tb_dsd8.uut.s3_valid`, `tb_dsd8.retire_pc` |
| A taken branch makes the next fetched instruction the wrong one. | `branch_taken` loads the target into `pc` and clears `s1_valid` and `s2_valid`. | `tb_dsd8.uut.branch_taken`, `tb_dsd8.uut.pc`, `tb_dsd8.uut.s1_valid`, `tb_dsd8.uut.s2_valid` |
| A slow device may need more clocks before it is ready. | `io_stall` holds the pipeline until `io_ready` returns. | `tb_dsd8.uut.io_stall`, `tb_dsd8.io_ready`, `tb_dsd8.io_rd`, `tb_dsd8.io_wr`, `tb_dsd8.retire` |

