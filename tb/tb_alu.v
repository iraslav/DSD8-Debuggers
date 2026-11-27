`timescale 1ns/1ps

module tb_alu;
    reg [7:0] a, b;
    reg [3:0] op;
    wire [7:0] result;
    wire flag_z, flag_n, flag_c, flag_v;
    integer checks, errors;

    alu dut (
        .a(a), .b(b), .op(op), .result(result),
        .flag_z(flag_z), .flag_n(flag_n), .flag_c(flag_c), .flag_v(flag_v)
    );

    task check;
        input [8*40-1:0] label;
        input [7:0] expected_result;
        input [3:0] expected_flags;
        begin
            #1;
            checks = checks + 1;
            if ({result, flag_z, flag_n, flag_c, flag_v} !==
                {expected_result, expected_flags}) begin
                errors = errors + 1;
                $display("CHECK FAIL %0s got=%02h %b expected=%02h %b",
                         label, result, {flag_z,flag_n,flag_c,flag_v},
                         expected_result, expected_flags);
            end else
                $display("CHECK PASS %0s", label);
        end
    endtask

    initial begin
        checks = 0;
        errors = 0;

        a = 8'hFF; b = 8'h01; op = 4'h4;
        check("ADD carry", 8'h00, 4'b1010);
        a = 8'h7F; b = 8'h01; op = 4'h4;
        check("ADD overflow", 8'h80, 4'b0101);
        a = 8'h00; b = 8'h01; op = 4'h5;
        check("SUB borrow", 8'hFF, 4'b0100);
        a = 8'h80; b = 8'h01; op = 4'h5;
        check("SUB overflow", 8'h7F, 4'b0011);
        a = 8'hF0; b = 8'h0F; op = 4'h6;
        check("AND flags", 8'h00, 4'b1000);
        a = 8'hF0; b = 8'h0F; op = 4'h7;
        check("OR flags", 8'hFF, 4'b0100);
        a = 8'hAA; b = 8'hFF; op = 4'h8;
        check("XOR flags", 8'h55, 4'b0000);
        a = 8'h81; b = 8'h00; op = 4'h9;
        check("SHL carry", 8'h02, 4'b0010);
        a = 8'h03; b = 8'h00; op = 4'hA;
        check("SHR carry", 8'h01, 4'b0010);
        a = 8'h05; b = 8'h05; op = 4'hB;
        check("CMP equality", 8'h00, 4'b1010);

        $display("CHECK SUMMARY: %0d checks, %0d errors", checks, errors);
        if (errors == 0) $display("TESTBENCH: PASS");
        else begin
            $display("TESTBENCH: FAIL (%0d errors)", errors);
            $fatal(1, "tb_alu failed");
        end
        $finish;
    end
endmodule
