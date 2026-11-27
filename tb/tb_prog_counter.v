`timescale 1ns/1ps

module tb_prog_counter;
    reg clk, rst_n, pc_en, pc_load;
    reg [8:0] branch_addr;
    wire [8:0] pc;
    integer checks, errors;

    prog_counter dut (
        .clk(clk), .rst_n(rst_n), .pc_en(pc_en), .pc_load(pc_load),
        .branch_addr(branch_addr), .pc(pc)
    );
    always #5 clk = ~clk;

    task check;
        input [8*40-1:0] label;
        input [8:0] expected;
        begin
            #1;
            checks = checks + 1;
            if (pc !== expected) begin
                errors = errors + 1;
                $display("CHECK FAIL %0s got=%03h expected=%03h", label, pc, expected);
            end else $display("CHECK PASS %0s", label);
        end
    endtask

    initial begin
        clk = 0; rst_n = 0; pc_en = 0; pc_load = 0; branch_addr = 0;
        checks = 0; errors = 0;
        @(posedge clk); #1; check("synchronous reset", 0);
        rst_n = 1; pc_en = 1;
        @(posedge clk); #1; check("increment", 1);
        pc_load = 1; branch_addr = 9'h1A5;
        @(posedge clk); #1; check("branch load", 9'h1A5);
        pc_en = 0; branch_addr = 9'h010;
        @(posedge clk); #1; check("disabled PC hold", 9'h1A5);
        pc_en = 1; pc_load = 0;
        @(posedge clk); #1; check("increment after hold", 9'h1A6);
        pc_load = 1; branch_addr = 9'h1FF;
        @(posedge clk); #1;
        pc_load = 0;
        @(posedge clk); #1; check("nine-bit wraparound", 0);

        $display("CHECK SUMMARY: %0d checks, %0d errors", checks, errors);
        if (errors == 0) $display("TESTBENCH: PASS");
        else begin
            $display("TESTBENCH: FAIL (%0d errors)", errors);
            $fatal(1, "tb_prog_counter failed");
        end
        $finish;
    end
endmodule
