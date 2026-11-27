`timescale 1ns/1ps

module tb_register_file;
    reg clk, rst_n, we;
    reg [2:0] ra1, ra2, wa;
    reg [7:0] wd;
    wire [7:0] rd1, rd2;
    integer checks, errors, i;

    register_file dut (
        .clk(clk), .rst_n(rst_n), .ra1(ra1), .ra2(ra2),
        .rd1(rd1), .rd2(rd2), .we(we), .wa(wa), .wd(wd)
    );
    always #5 clk = ~clk;

    task check;
        input [8*40-1:0] label;
        input [7:0] expected1, expected2;
        begin
            #1;
            checks = checks + 1;
            if ({rd1,rd2} !== {expected1,expected2}) begin
                errors = errors + 1;
                $display("CHECK FAIL %0s got=%02h/%02h expected=%02h/%02h",
                         label, rd1, rd2, expected1, expected2);
            end else $display("CHECK PASS %0s", label);
        end
    endtask

    initial begin
        clk = 0; rst_n = 0; we = 0; ra1 = 0; ra2 = 0; wa = 0; wd = 0;
        checks = 0; errors = 0;
        @(posedge clk); #1; rst_n = 1;
        for (i = 0; i < 8; i = i + 1) begin
            ra1 = i; ra2 = i;
            check("reset register zero", 0, 0);
        end
        @(negedge clk);
        we = 1; wa = 3; wd = 8'hA6; ra1 = 3; ra2 = 2;
        check("read before same-edge write", 0, 0);
        @(posedge clk); #1; we = 0;
        check("write visible after edge", 8'hA6, 0);
        ra1 = 3; ra2 = 3;
        check("two combinational read ports", 8'hA6, 8'hA6);

        $display("CHECK SUMMARY: %0d checks, %0d errors", checks, errors);
        if (errors == 0) $display("TESTBENCH: PASS");
        else begin
            $display("TESTBENCH: FAIL (%0d errors)", errors);
            $fatal(1, "tb_register_file failed");
        end
        $finish;
    end
endmodule
