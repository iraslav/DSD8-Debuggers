`timescale 1ns/1ps

module tb_instr_decoder;
    reg [15:0] instr;
    wire [3:0] opcode;
    wire [2:0] rd, rs1, rs2, cond;
    wire [7:0] imm8, port;
    wire [8:0] addr9;
    wire io_dir;
    integer checks, errors;

    instr_decoder dut (
        .instr(instr), .opcode(opcode), .rd(rd), .rs1(rs1), .rs2(rs2),
        .imm8(imm8), .addr9(addr9), .cond(cond), .port(port), .io_dir(io_dir)
    );

    task check_fields;
        input [8*40-1:0] label;
        input [3:0] eop;
        input [2:0] erd, ers1, ers2, econd;
        input [7:0] eimm, eport;
        input [8:0] eaddr;
        input edir;
        begin
            #1;
            checks = checks + 1;
            if ({opcode,rd,rs1,rs2,cond,imm8,port,addr9,io_dir} !==
                {eop,erd,ers1,ers2,econd,eimm,eport,eaddr,edir}) begin
                errors = errors + 1;
                $display("CHECK FAIL %0s instr=%04h", label, instr);
            end else $display("CHECK PASS %0s", label);
        end
    endtask

    initial begin
        checks = 0; errors = 0;

        instr = 16'h0000;
        check_fields("worked NOP encoding", 0,0,0,0,0,0,0,0,0);
        instr = 16'h16A5;
        check_fields("worked LDI R3, A5", 1,3,2,4,3,8'hA5,8'hA5,9'h0A5,0);
        instr = 16'h2540;
        check_fields("worked LD R2, [R5]", 2,2,5,0,2,8'h40,8'h40,9'h140,1);
        instr = 16'h3840;
        check_fields("worked ST [R1], R4", 3,4,1,0,4,8'h40,8'h40,9'h040,0);
        instr = 16'h4650;
        check_fields("worked ADD R3, R1, R2", 4,3,1,2,3,8'h50,8'h50,9'h050,0);
        instr = 16'hB050;
        check_fields("worked CMP R1, R2", 11,0,1,2,0,8'h50,8'h50,9'h050,0);
        instr = 16'hD012;
        check_fields("worked BEQ target", 13,0,0,2,0,8'h12,8'h12,9'h012,0);
        instr = 16'hC012;
        check_fields("worked JMP target", 12,0,0,2,0,8'h12,8'h12,9'h012,0);
        instr = 16'hE421;
        check_fields("worked IN R2, 21", 14,2,0,4,2,8'h21,8'h21,9'h021,0);
        instr = 16'hE702;
        check_fields("worked OUT 02, R3", 14,3,4,0,3,8'h02,8'h02,9'h102,1);

        $display("CHECK SUMMARY: %0d checks, %0d errors", checks, errors);
        if (errors == 0) $display("TESTBENCH: PASS");
        else begin
            $display("TESTBENCH: FAIL (%0d errors)", errors);
            $fatal(1, "tb_instr_decoder failed");
        end
        $finish;
    end
endmodule
