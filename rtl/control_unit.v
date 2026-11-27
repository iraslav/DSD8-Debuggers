// control_unit.v -- the FSM that sequences every instruction
// Owner: member C -- this is YOUR module; you are individually examined
// on it at the oral defence, and it is the heart of your microarchitecture
// choice (Section 4.3).
// Spec: Section 6. Port list is FROZEN.
//
// This is deliberately the least finished file in this repository: the
// control unit is the one part of the design the spec leaves entirely
// up to you (single-cycle, multi-cycle, or pipelined -- Section 4.3),
// and it is what the recommended state machine and control-signal
// table in Section 6 describe. Copying a working FSM from anywhere
// would defeat the point of the assignment and of the oral defence.
//
// What every implementation must guarantee, regardless of style
// (Section 8.2, R22): instructions retire in program order, and
// `retire` pulses exactly once per retired instruction -- never zero,
// never twice.

module control_unit (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [3:0] opcode,
    input  wire [2:0] cond,
    input  wire [3:0] flags,      // {Z,N,C,V}
    input  wire       io_ready,
    output reg        pc_en,
    output reg        pc_load,
    output reg        rf_we,
    output reg        mem_we,
    output reg        io_rd,
    output reg        io_wr,
    output reg        flags_we,
    output reg  [1:0] wb_sel,     // 0=ALU 1=DMEM 2=imm8 3=io_rdata
    output reg        halted,
    output reg        retire
);

    reg taken;

    always @* begin
        pc_en = 1'b1;
        pc_load = 1'b0;
        rf_we = 1'b0;
        mem_we = 1'b0;
        io_rd = 1'b0;
        io_wr = 1'b0;
        flags_we = 1'b0;
        wb_sel = 2'b00;
        halted = 1'b0;
        retire = 1'b0;
        taken = 1'b0;

        case (opcode)
            4'h1: begin rf_we = 1'b1; wb_sel = 2'b10; end
            4'h2: begin rf_we = 1'b1; wb_sel = 2'b01; end
            4'h3: mem_we = 1'b1;
            4'h4, 4'h5, 4'h6, 4'h7, 4'h8, 4'h9, 4'hA: begin
                rf_we = 1'b1;
                flags_we = 1'b1;
                wb_sel = 2'b00;
            end
            4'hB: begin
                flags_we = 1'b1;
                wb_sel = 2'b00;
            end
            4'hC: pc_load = 1'b1;
            4'hD: begin
                case (cond)
                    3'b000: taken = flags[3];
                    3'b001: taken = ~flags[3];
                    3'b010: taken = flags[1];
                    3'b011: taken = ~flags[1];
                    3'b100: taken = flags[2];
                    3'b101: taken = ~flags[2];
                    3'b110: taken = flags[0];
                    3'b111: taken = ~flags[0];
                endcase
                pc_load = taken;
            end
            4'hE: begin
                io_rd = io_ready;
                io_wr = io_ready;
            end
            4'hF: begin
                pc_en = 1'b0;
                halted = 1'b1;
            end
        endcase
    end

endmodule
