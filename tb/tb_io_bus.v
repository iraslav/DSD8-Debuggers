`timescale 1ns/1ps

module tb_io_bus;
    reg clk, rst_n;
    reg [7:0] io_port, io_wdata, switches, periph_rdata;
    reg [4:0] buttons;
    reg io_rd, io_wr, periph_ready;
    wire [7:0] io_rdata, leds, seg_value, seg_enable;
    wire io_ready;
    wire [7:0] periph_port, periph_wdata;
    wire periph_rd, periph_wr;
    integer checks, errors;

    io_bus dut (
        .clk(clk), .rst_n(rst_n), .io_port(io_port), .io_wdata(io_wdata),
        .io_rdata(io_rdata), .io_rd(io_rd), .io_wr(io_wr), .io_ready(io_ready),
        .switches(switches), .buttons(buttons), .leds(leds),
        .seg_value(seg_value), .seg_enable(seg_enable),
        .periph_port(periph_port), .periph_wdata(periph_wdata),
        .periph_rdata(periph_rdata), .periph_rd(periph_rd),
        .periph_wr(periph_wr), .periph_ready(periph_ready)
    );
    always #5 clk = ~clk;

    task check1;
        input [8*40-1:0] label;
        input got, expected;
        begin
            checks = checks + 1;
            if (got !== expected) begin
                errors = errors + 1;
                $display("CHECK FAIL %0s got=%b expected=%b", label, got, expected);
            end else $display("CHECK PASS %0s", label);
        end
    endtask

    task check8;
        input [8*40-1:0] label;
        input [7:0] got, expected;
        begin
            checks = checks + 1;
            if (got !== expected) begin
                errors = errors + 1;
                $display("CHECK FAIL %0s got=%02h expected=%02h", label, got, expected);
            end else $display("CHECK PASS %0s", label);
        end
    endtask

    initial begin
        clk = 0; rst_n = 0; io_port = 0; io_wdata = 0;
        switches = 0; buttons = 0; periph_rdata = 0; io_rd = 0; io_wr = 0;
        periph_ready = 0; checks = 0; errors = 0;
        @(posedge clk); #1;
        check8("reset LEDs", leds, 0);
        check8("reset seven-seg value", seg_value, 0);
        check8("reset seven-seg enable", seg_enable, 0);
        rst_n = 1;

        io_port = 0; switches = 8'hA5;
        #1; check8("switch read", io_rdata, 8'hA5);
        check1("reserved switch port ready", io_ready, 1);
        io_port = 1; buttons = 5'h15;
        #1; check8("button read zero extends", io_rdata, 8'h15);
        io_port = 8'h03; #1;
        check8("unmapped port reads zero", io_rdata, 0);

        io_port = 8'h40; io_rd = 1; io_wr = 0; periph_ready = 0;
        periph_rdata = 8'h6C; #1;
        check1("peripheral wait propagated", io_ready, 0);
        check1("peripheral read forwarded", periph_rd, 1);
        check1("peripheral write inactive", periph_wr, 0);
        check8("peripheral data forwarded", io_rdata, 8'h6C);
        check8("peripheral address forwarded", periph_port, 8'h40);
        periph_ready = 1; io_rd = 0; io_wr = 1; io_wdata = 8'hC3; #1;
        check1("peripheral ready propagated", io_ready, 1);
        check1("peripheral write forwarded", periph_wr, 1);
        check8("peripheral write data forwarded", periph_wdata, 8'hC3);

        io_port = 8'h02; io_wr = 1; io_wdata = 8'h5A;
        @(posedge clk); #1; check8("LED write", leds, 8'h5A);
        io_port = 8'h10; io_wdata = 8'hA1;
        @(posedge clk); #1; check8("seven-seg value write", seg_value, 8'hA1);
        io_port = 8'h11; io_wdata = 8'h0F;
        @(posedge clk); #1; check8("seven-seg enable write", seg_enable, 8'h0F);

        $display("CHECK SUMMARY: %0d checks, %0d errors", checks, errors);
        if (errors == 0) $display("TESTBENCH: PASS");
        else begin
            $display("TESTBENCH: FAIL (%0d errors)", errors);
            $fatal(1, "tb_io_bus failed");
        end
        $finish;
    end
endmodule
