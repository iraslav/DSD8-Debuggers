`timescale 1ns/1ps

module tb_instr_memory;
    reg clk;
    reg [8:0] addr;
    wire [15:0] data;
    integer checks, errors;

    instr_memory #(.IMAGE("tb/instr_memory_test.hex")) dut (
        .clk(clk), .addr(addr), .data(data)
    );

    task check;
        input [8*40-1:0] label;
        input [15:0] expected;
        begin
            #1;
            checks = checks + 1;
            if (data !== expected) begin
                errors = errors + 1;
                $display("CHECK FAIL %0s addr=%03h got=%04h expected=%04h",
                         label, addr, data, expected);
            end else $display("CHECK PASS %0s", label);
        end
    endtask

    initial begin
        clk = 0; addr = 0; checks = 0; errors = 0;
        addr = 0; check("first image word", 16'h16A5);
        addr = 1; check("second image word", 16'h4650);
        addr = 2; check("third image word", 16'hF000);
        addr = 9'h1FF; check("last image word", 16'hC012);
        $display("CHECK SUMMARY: %0d checks, %0d errors", checks, errors);
        if (errors == 0) $display("TESTBENCH: PASS");
        else begin
            $display("TESTBENCH: FAIL (%0d errors)", errors);
            $fatal(1, "tb_instr_memory failed");
        end
        $finish;
    end
endmodule
