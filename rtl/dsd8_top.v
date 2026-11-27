// dsd8_top.v -- system top level
// Owner: shared (whole team integrates this together)
// Spec: Section 5.1. Port list is FROZEN -- do not rename or resize.

module dsd8_top (
    input  wire       clk,
    input  wire       rst_n,       // synchronous, active low
    input  wire [7:0] switches,    // board slide switches  -> port 0x00
    input  wire [4:0] buttons,     // {btnU,btnD,btnL,btnR,btnC} -> port 0x01
    output wire [7:0] leds,        // board LEDs             <- port 0x02
    output wire [6:0] seg,         // seven-segment segments <- port 0x10
    output wire [3:0] an,          // seven-segment digit enables
    output wire       halted       // asserted after HLT retires
);

    wire [8:0] imem_addr;
    wire [15:0] imem_data;
    wire [7:0] io_port;
    wire [7:0] io_wdata;
    wire [7:0] io_rdata;
    wire io_rd;
    wire io_wr;
    wire io_ready;
    wire [7:0] periph_rdata;
    wire [7:0] periph_port;
    wire [7:0] periph_wdata;
    wire periph_rd;
    wire periph_wr;
    wire periph_ready;
    wire [7:0] leds_internal;
    wire [7:0] seg_internal;
    wire [7:0] an_internal;

    dsd8_cpu cpu (
        .clk(clk), .rst_n(rst_n),
        .imem_addr(imem_addr), .imem_data(imem_data),
        .io_port(io_port), .io_wdata(io_wdata), .io_rdata(io_rdata),
        .io_rd(io_rd), .io_wr(io_wr), .io_ready(io_ready),
        .halted(halted),
        .retire(), .retire_pc(), .retire_ir(),
        .retire_rf_we(), .retire_rf_addr(), .retire_rf_data(),
        .retire_mem_we(), .retire_mem_addr(), .retire_mem_data(),
        .retire_flags()
    );

    instr_memory imem (
        .clk(clk), .addr(imem_addr), .data(imem_data)
    );

    io_bus io_inst (
        .clk(clk), .rst_n(rst_n),
        .io_port(io_port), .io_wdata(io_wdata), .io_rdata(io_rdata),
        .io_rd(io_rd), .io_wr(io_wr), .io_ready(io_ready),
        .switches(switches), .buttons(buttons),
        .leds(leds_internal), .seg_value(seg_internal), .seg_enable(an_internal),
        .periph_port(periph_port), .periph_wdata(periph_wdata),
        .periph_rdata(periph_rdata), .periph_rd(periph_rd),
        .periph_wr(periph_wr), .periph_ready(periph_ready)
    );

    dsd8_ref_peripherals peripherals (
        .clk(clk), .rst_n(rst_n),
        .periph_port(periph_port), .periph_wdata(periph_wdata),
        .periph_rdata(periph_rdata), .periph_rd(periph_rd),
        .periph_wr(periph_wr), .periph_ready(periph_ready)
    );

    assign leds = leds_internal;
    assign seg = seg_internal[6:0];
    assign an = an_internal[3:0];

endmodule
