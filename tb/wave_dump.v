`timescale 1ns/1ps

module wave_dump;
    reg [31:0] s1_mnemonic;
    reg [31:0] s2_mnemonic;
    reg [31:0] s3_mnemonic;

    task decode_mnemonic;
        input [15:0] ir;
        input valid;
        output [31:0] mnemonic;
        reg [3:0] opcode;
        reg [2:0] cond;
        begin
            mnemonic = "----";
            if (valid) begin
                opcode = ir[15:12];
                cond = ir[11:9];
                case (opcode)
                    4'h0: mnemonic = "NOP ";
                    4'h1: mnemonic = "LDI ";
                    4'h2: mnemonic = "LD  ";
                    4'h3: mnemonic = "ST  ";
                    4'h4: mnemonic = "ADD ";
                    4'h5: mnemonic = "SUB ";
                    4'h6: mnemonic = "AND ";
                    4'h7: mnemonic = "OR  ";
                    4'h8: mnemonic = "XOR ";
                    4'h9: mnemonic = "SHL ";
                    4'hA: mnemonic = "SHR ";
                    4'hB: mnemonic = "CMP ";
                    4'hC: mnemonic = "JMP ";
                    4'hD: begin
                        case (cond)
                            3'b000: mnemonic = "BEQ ";
                            3'b001: mnemonic = "BNE ";
                            3'b010: mnemonic = "BCS ";
                            3'b011: mnemonic = "BCC ";
                            3'b100: mnemonic = "BMI ";
                            3'b101: mnemonic = "BPL ";
                            3'b110: mnemonic = "BVS ";
                            3'b111: mnemonic = "BVC ";
                        endcase
                    end
                    4'hE: mnemonic = ir[8] ? "OUT " : "IN  ";
                    4'hF: mnemonic = "HLT ";
                    default: mnemonic = "----";
                endcase
            end
        end
    endtask

    always @* begin
        decode_mnemonic(tb_dsd8.uut.s1_ir, tb_dsd8.uut.s1_valid, s1_mnemonic);
        decode_mnemonic(tb_dsd8.uut.s2_ir, tb_dsd8.uut.s2_valid, s2_mnemonic);
        decode_mnemonic(tb_dsd8.uut.s3_ir, tb_dsd8.uut.s3_valid, s3_mnemonic);
    end

    initial begin
        $dumpfile("sim/dsd8_pipeline.vcd");
        $dumpvars(0, tb_dsd8);
        $dumpvars(0, wave_dump);
    end
endmodule
