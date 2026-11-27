// io_bus.v -- port address decode and the io_ready handshake
// Owner: member C -- this is YOUR module; you are individually examined
// on it at the oral defence.
// Spec: Section 7. The CPU-facing side of this module (the six signals
// wired to dsd8_cpu) is frozen by Section 7.1's signal table. The
// board/peripheral-facing side below is NOT dictated verbatim by the
// spec excerpts this template was built from -- treat those ports as a
// starting design, confirm them against your own course's Section 5.11
// if one exists, and adjust freely; unlike dsd8_cpu, no external
// testbench binds to io_bus's peripheral-facing ports by name.
//
// What is required (Section 7.1, R19-R21): decode io_port into the
// right peripheral, forward io_rd/io_wr and stall the CPU (by holding
// io_ready low) until the addressed peripheral is ready. Ports 0x00 to
// 0x3F are reserved and behave exactly per Section 7.2's table; reads
// of an unmapped port return 0x00, writes to one are discarded, and no
// port may ever hold io_ready low indefinitely.

module io_bus (
    input  wire        clk,
    input  wire        rst_n,

    // ---- CPU-facing side: matches dsd8_cpu's io_* ports exactly ----
    input  wire [7:0]  io_port,
    input  wire [7:0]  io_wdata,
    output reg  [7:0]  io_rdata,
    input  wire        io_rd,
    input  wire        io_wr,
    output reg         io_ready,

    // ---- board-facing side (Section 7.2 standard port map) ----
    input  wire [7:0]  switches,     // port 0x00
    input  wire [4:0]  buttons,      // port 0x01
    output reg  [7:0]  leds,         // port 0x02
    output reg  [7:0]  seg_value,    // port 0x10
    output reg  [7:0]  seg_enable,   // port 0x11

    // ---- forwarded to sim/peripherals.v for UART / timer / SLOW_ECHO ----
    output wire [7:0]  periph_port,
    output wire [7:0]  periph_wdata,
    input  wire [7:0]  periph_rdata,
    output wire        periph_rd,
    output wire        periph_wr,
    input  wire        periph_ready
);

    always @* begin
        io_rdata = 8'h00;
        io_ready = 1'b1;

        if (io_port == 8'h00)
            io_rdata = switches;
        else if (io_port == 8'h01)
            io_rdata = {3'b000, buttons};
        else if (io_port >= 8'h20)
            io_rdata = periph_rdata;
        else
            io_rdata = 8'h00;

        if (io_port >= 8'h20)
            io_ready = periph_ready;
        else
            io_ready = 1'b1;
    end

    assign periph_port  = io_port;
    assign periph_wdata = io_wdata;
    assign periph_rd    = (io_port >= 8'h20) ? io_rd : 1'b0;
    assign periph_wr    = (io_port >= 8'h20) ? io_wr : 1'b0;

    always @(posedge clk) begin
        if (!rst_n) begin
            leds       <= 8'h00;
            seg_value  <= 8'h00;
            seg_enable <= 8'h00;
        end else if (io_wr) begin
            case (io_port)
                8'h02: leds      <= io_wdata;
                8'h10: seg_value <= io_wdata;
                8'h11: seg_enable <= io_wdata;
                default: begin end
            endcase
        end
    end

endmodule
