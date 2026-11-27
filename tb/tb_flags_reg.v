`timescale 1ns/1ps

module tb_flags_reg;
    reg clk, rst_n, flags_we;
    reg [3:0] flags_in;
    wire [3:0] flags_out;
    integer checks, errors;

    flags_reg dut (
        .clk(clk), .rst_n(rst_n), .flags_we(flags_we),
        .flags_in(flags_in), .flags_out(flags_out)
    );
    always #5 clk = ~clk;

    task check;
        input [8*40-1:0] label;
        input [3:0] expected;
        begin
            #1;
            checks = checks + 1;
            if (flags_out !== expected) begin
                errors = errors + 1;
                $display("CHECK FAIL %0s got=%b expected=%b", label, flags_out, expected);
            end else $display("CHECK PASS %0s", label);
        end
    endtask

    initial begin
        clk = 0; rst_n = 0; flags_we = 0; flags_in = 0;
        checks = 0; errors = 0;
        @(posedge clk); #1; check("synchronous active-low reset", 0);
        rst_n = 1; flags_we = 1; flags_in = 4'b1011;
        @(posedge clk); #1; check("enabled flags update", 4'b1011);
        flags_we = 0; flags_in = 4'b0100;
        @(posedge clk); #1; check("disabled flags hold", 4'b1011);
        rst_n = 0; flags_we = 1; flags_in = 4'b1111;
        @(posedge clk); #1; check("reset overrides write", 0);

        $display("CHECK SUMMARY: %0d checks, %0d errors", checks, errors);
        if (errors == 0) $display("TESTBENCH: PASS");
        else begin
            $display("TESTBENCH: FAIL (%0d errors)", errors);
            $fatal(1, "tb_flags_reg failed");
        end
        $finish;
    end
endmodule
