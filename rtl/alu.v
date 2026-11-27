// alu.v -- arithmetic, logic, shifts, and the four flag outputs
// Owner: member B -- this is YOUR module; you are individually examined
// on it at the oral defence, and it is the one Section 8.5 (R24-R25)
// requires a constrained-random self-checking testbench for.
// Spec: Section 5.7 and Section 2.3. Purely combinational. Port list
// is FROZEN. `op` is the instruction opcode directly (R15) -- no
// separate ALU-control encoding needed.
//
// This file intentionally does NOT implement the truth table for you
// -- Section 2.3 already gives you the exact carry, overflow and flag
// definitions; writing the RTL from that table (and then proving it
// correct with your own random test) is the actual exercise. See
// tools/dsd8sim.py if you want a second, independent statement of the
// same semantics in Python to cross-check your own reading of the spec
// against -- but write this module yourself.

module alu (
    input  wire [7:0] a,
    input  wire [7:0] b,
    input  wire [3:0] op,     // instruction opcode: 0x4 ADD .. 0xB CMP
    output wire [7:0] result,
    output wire       flag_z,
    output wire       flag_n,
    output wire       flag_c,
    output wire       flag_v
);

    reg [7:0] r;
    reg z;
    reg n;
    reg c;
    reg v;
    reg [8:0] add9;
    reg [8:0] sub9;

    always @* begin
        r = 8'h00;
        z = 1'b0;
        n = 1'b0;
        c = 1'b0;
        v = 1'b0;
        add9 = {1'b0, a} + {1'b0, b};
        sub9 = {1'b0, a} + {1'b0, ~b} + 9'h001;

        case (op)
            4'h4: begin
                r = add9[7:0];
                c = add9[8];
                v = (a[7] == b[7]) && (r[7] != a[7]);
            end
            4'h5, 4'hB: begin
                r = sub9[7:0];
                c = sub9[8];
                v = (a[7] != b[7]) && (r[7] != a[7]);
            end
            4'h6: r = a & b;
            4'h7: r = a | b;
            4'h8: r = a ^ b;
            4'h9: begin
                r = {a[6:0], 1'b0};
                c = a[7];
            end
            4'hA: begin
                r = {1'b0, a[7:1]};
                c = a[0];
            end
            default: r = 8'h00;
        endcase

        z = (r == 8'h00);
        n = r[7];
    end

    assign result = r;
    assign flag_z = z;
    assign flag_n = n;
    assign flag_c = c;
    assign flag_v = v;

endmodule
