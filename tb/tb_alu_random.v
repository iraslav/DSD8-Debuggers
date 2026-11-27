`timescale 1ns/1ps

module tb_alu_random;
    reg [7:0] a, b;
    reg [3:0] op;
    wire [7:0] result;
    wire flag_z, flag_n, flag_c, flag_v;

    reg [3:0] operations [0:7];
    reg [7:0] corners [0:4];
    integer op_count [0:7];
    integer corner_a [0:7][0:4];
    integer corner_b [0:7][0:4];
    integer v_count [0:7];
    integer c_count [0:7];
    integer errors, pairs_checked, random_seed;
    integer oi, i, ci;

    alu dut (
        .a(a), .b(b), .op(op), .result(result),
        .flag_z(flag_z), .flag_n(flag_n), .flag_c(flag_c), .flag_v(flag_v)
    );

    task reference_model;
        input [7:0] ra, rb;
        input [3:0] rop;
        output [7:0] rr;
        output [3:0] rf;
        reg [8:0] add_ext;
        reg [8:0] sub_ext;
        reg overflow;
        begin
            rr = 8'h00;
            rf = 4'b0000;
            add_ext = {1'b0,ra} + {1'b0,rb};
            sub_ext = {1'b0,ra} + {1'b0,~rb} + 9'd1;
            overflow = 1'b0;

            case (rop)
                4'h4: begin
                    rr = add_ext[7:0];
                    rf[1] = add_ext[8];
                    overflow = (ra[7] == rb[7]) && (rr[7] != ra[7]);
                end
                4'h5, 4'hB: begin
                    rr = sub_ext[7:0];
                    rf[1] = sub_ext[8];
                    overflow = (ra[7] != rb[7]) && (rr[7] != ra[7]);
                end
                4'h6: rr = ra & rb;
                4'h7: rr = ra | rb;
                4'h8: rr = ra ^ rb;
                4'h9: begin rr = {ra[6:0],1'b0}; rf[1] = ra[7]; end
                4'hA: begin rr = {1'b0,ra[7:1]}; rf[1] = ra[0]; end
                default: rr = 8'h00;
            endcase

            rf[3] = (rr == 8'h00);
            rf[2] = rr[7];
            rf[0] = overflow;
        end
    endtask

    task run_vector;
        input integer op_index;
        input [7:0] av, bv;
        reg [7:0] expected_result;
        reg [3:0] expected_flags;
        begin
            a = av; b = bv; op = operations[op_index];
            reference_model(av, bv, op, expected_result, expected_flags);
            #1;
            pairs_checked = pairs_checked + 1;
            op_count[op_index] = op_count[op_index] + 1;
            for (ci = 0; ci < 5; ci = ci + 1) begin
                if (av == corners[ci]) corner_a[op_index][ci] = corner_a[op_index][ci] + 1;
                if (bv == corners[ci]) corner_b[op_index][ci] = corner_b[op_index][ci] + 1;
            end
            if (flag_v) v_count[op_index] = v_count[op_index] + 1;
            if (flag_c) c_count[op_index] = c_count[op_index] + 1;
            if ({result,flag_z,flag_n,flag_c,flag_v} !==
                {expected_result,expected_flags}) begin
                errors = errors + 1;
                if (errors <= 20)
                    $display("MISMATCH op=%h a=%02h b=%02h got=%02h/%b expected=%02h/%b",
                             op, av, bv, result, {flag_z,flag_n,flag_c,flag_v},
                             expected_result, expected_flags);
            end
        end
    endtask

    initial begin
        operations[0]=4'h4; operations[1]=4'h5; operations[2]=4'h6;
        operations[3]=4'h7; operations[4]=4'h8; operations[5]=4'h9;
        operations[6]=4'hA; operations[7]=4'hB;
        corners[0]=8'h00; corners[1]=8'h01; corners[2]=8'h7F;
        corners[3]=8'h80; corners[4]=8'hFF;
        errors=0; pairs_checked=0; random_seed=32'h4D534431;
        for (oi=0; oi<8; oi=oi+1) begin
            op_count[oi]=0; v_count[oi]=0; c_count[oi]=0;
            for (ci=0; ci<5; ci=ci+1) begin
                corner_a[oi][ci]=0; corner_b[oi][ci]=0;
            end
        end

        for (oi=0; oi<8; oi=oi+1) begin
            for (i=0; i<10000; i=i+1) begin
                if (i < 25) begin
                    a = corners[i / 5];
                    b = corners[i % 5];
                end else begin
                    a = $random(random_seed);
                    b = $random(random_seed);
                end
                run_vector(oi, a, b);
            end
        end

        $display("ALU COVERAGE: pairs=%0d (target >= 80000)", pairs_checked);
        $display("op   count   C=1   V=1   operand-a corners [00 01 7F 80 FF] / operand-b corners");
        for (oi=0; oi<8; oi=oi+1) begin
            $display("%h    %0d    %0d    %0d    A[%0d %0d %0d %0d %0d] B[%0d %0d %0d %0d %0d]",
                operations[oi], op_count[oi], c_count[oi], v_count[oi],
                corner_a[oi][0], corner_a[oi][1], corner_a[oi][2], corner_a[oi][3], corner_a[oi][4],
                corner_b[oi][0], corner_b[oi][1], corner_b[oi][2], corner_b[oi][3], corner_b[oi][4]);
        end
        $display("CHECK SUMMARY: %0d comparisons, %0d errors", pairs_checked, errors);
        if (errors == 0 && pairs_checked >= 80000) $display("TESTBENCH: PASS");
        else begin
            $display("TESTBENCH: FAIL (%0d errors)", errors);
            $fatal(1, "tb_alu_random failed");
        end
        $finish;
    end
endmodule
