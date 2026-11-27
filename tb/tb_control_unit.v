`timescale 1ns/1ps

module tb_control_unit;
    reg clk, rst_n;
    reg [3:0] opcode, flags;
    reg [2:0] cond;
    reg io_ready;
    wire pc_en, pc_load, rf_we, mem_we, io_rd, io_wr, flags_we;
    wire [1:0] wb_sel;
    wire halted, retire;
    integer checks, errors;

    control_unit dut (
        .clk(clk), .rst_n(rst_n), .opcode(opcode), .cond(cond), .flags(flags),
        .io_ready(io_ready), .pc_en(pc_en), .pc_load(pc_load), .rf_we(rf_we),
        .mem_we(mem_we), .io_rd(io_rd), .io_wr(io_wr), .flags_we(flags_we),
        .wb_sel(wb_sel), .halted(halted), .retire(retire)
    );

    task check_controls;
        input [8*40-1:0] label;
        input [10:0] expected;
        begin
            #1;
            checks = checks + 1;
            if ({pc_en,pc_load,rf_we,mem_we,io_rd,io_wr,flags_we,wb_sel,halted,retire} !== expected) begin
                errors = errors + 1;
                $display("CHECK FAIL %0s got=%b expected=%b", label,
                         {pc_en,pc_load,rf_we,mem_we,io_rd,io_wr,flags_we,wb_sel,halted,retire},
                         expected);
            end else $display("CHECK PASS %0s", label);
        end
    endtask

    initial begin
        clk = 0; rst_n = 1; opcode = 0; cond = 0; flags = 0; io_ready = 1;
        checks = 0; errors = 0;
        opcode=4'h0; check_controls("NOP defaults", 11'b10000000000);
        opcode=4'h1; check_controls("LDI selects immediate", 11'b10100001000);
        opcode=4'h2; check_controls("LD selects memory", 11'b10100000100);
        opcode=4'h3; check_controls("ST writes memory", 11'b10010000000);
        opcode=4'h4; check_controls("ALU writes RF and flags", 11'b10100010000);
        opcode=4'hB; check_controls("CMP writes flags only", 11'b10000010000);
        opcode=4'hC; check_controls("JMP loads PC", 11'b11000000000);

        opcode = 4'hD;
        cond=3'b000; flags=4'b1000; check_controls("BEQ taken", 11'b11000000000);
        cond=3'b000; flags=4'b0000; check_controls("BEQ not taken", 11'b10000000000);
        cond=3'b001; flags=4'b0000; check_controls("BNE taken", 11'b11000000000);
        cond=3'b001; flags=4'b1000; check_controls("BNE not taken", 11'b10000000000);
        cond=3'b010; flags=4'b0010; check_controls("BCS taken", 11'b11000000000);
        cond=3'b010; flags=4'b0000; check_controls("BCS not taken", 11'b10000000000);
        cond=3'b011; flags=4'b0000; check_controls("BCC taken", 11'b11000000000);
        cond=3'b011; flags=4'b0010; check_controls("BCC not taken", 11'b10000000000);
        cond=3'b100; flags=4'b0100; check_controls("BMI taken", 11'b11000000000);
        cond=3'b100; flags=4'b0000; check_controls("BMI not taken", 11'b10000000000);
        cond=3'b101; flags=4'b0000; check_controls("BPL taken", 11'b11000000000);
        cond=3'b101; flags=4'b0100; check_controls("BPL not taken", 11'b10000000000);
        cond=3'b110; flags=4'b0001; check_controls("BVS taken", 11'b11000000000);
        cond=3'b110; flags=4'b0000; check_controls("BVS not taken", 11'b10000000000);
        cond=3'b111; flags=4'b0000; check_controls("BVC taken", 11'b11000000000);
        cond=3'b111; flags=4'b0001; check_controls("BVC not taken", 11'b10000000000);

        opcode=4'hE; io_ready=1; check_controls("I/O ready requests", 11'b10001100000);
        io_ready=0; check_controls("I/O wait deasserts request", 11'b10000000000);
        opcode=4'hF; check_controls("HLT disables PC", 11'b00000000010);

        $display("CHECK SUMMARY: %0d checks, %0d errors", checks, errors);
        if (errors == 0) $display("TESTBENCH: PASS");
        else begin
            $display("TESTBENCH: FAIL (%0d errors)", errors);
            $fatal(1, "tb_control_unit failed");
        end
        $finish;
    end
endmodule
