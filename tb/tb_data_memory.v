`timescale 1ns/1ps

module tb_data_memory;
    reg clk, we;
    reg [7:0] addr, wdata;
    wire [7:0] rdata;
    integer checks, errors, i;

    data_memory dut (.clk(clk), .addr(addr), .we(we), .wdata(wdata), .rdata(rdata));
    always #5 clk = ~clk;

    task check;
        input [8*40-1:0] label;
        input [7:0] expected;
        begin
            #1;
            checks = checks + 1;
            if (rdata !== expected) begin
                errors = errors + 1;
                $display("CHECK FAIL %0s addr=%02h got=%02h expected=%02h",
                         label, addr, rdata, expected);
            end else $display("CHECK PASS %0s addr=%02h", label, addr);
        end
    endtask

    initial begin
        clk = 0; we = 0; addr = 0; wdata = 0; checks = 0; errors = 0;
        for (i = 0; i < 256; i = i + 1) begin
            addr = i;
            check("zero initialized DMEM byte", 0);
        end
        @(negedge clk); addr = 8'h00; wdata = 8'hA5; we = 1;
        @(posedge clk); #1; we = 0; check("write first byte", 8'hA5);
        @(negedge clk); addr = 8'hFF; wdata = 8'h5A; we = 1;
        @(posedge clk); #1; we = 0; check("write last byte", 8'h5A);
        addr = 8'h00; check("independent byte retained", 8'hA5);
        addr = 8'hFF; check("last byte retained", 8'h5A);

        $display("CHECK SUMMARY: %0d checks, %0d errors", checks, errors);
        if (errors == 0) $display("TESTBENCH: PASS");
        else begin
            $display("TESTBENCH: FAIL (%0d errors)", errors);
            $fatal(1, "tb_data_memory failed");
        end
        $finish;
    end
endmodule
