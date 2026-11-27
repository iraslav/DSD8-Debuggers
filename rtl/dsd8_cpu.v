// dsd8_cpu.v -- 3-stage pipelined DSD-8 core

module dsd8_cpu (
    input  wire        clk,
    input  wire        rst_n,

    output wire [8:0]  imem_addr,
    input  wire [15:0] imem_data,

    output wire [7:0]  io_port,
    output wire [7:0]  io_wdata,
    input  wire [7:0]  io_rdata,
    output wire        io_rd,
    output wire        io_wr,
    input  wire        io_ready,

    output wire        halted,
    output wire        retire,
    output wire [8:0]  retire_pc,
    output wire [15:0] retire_ir,
    output wire        retire_rf_we,
    output wire [2:0]  retire_rf_addr,
    output wire [7:0]  retire_rf_data,
    output wire        retire_mem_we,
    output wire [7:0]  retire_mem_addr,
    output wire [7:0]  retire_mem_data,
    output wire [3:0]  retire_flags
);

    reg [8:0] pc;
    reg [8:0] s1_pc;
    reg [15:0] s1_ir;
    reg s1_valid;

    reg [8:0] s2_pc;
    reg [15:0] s2_ir;
    reg s2_valid;

    reg [8:0] s3_pc;
    reg [15:0] s3_ir;
    reg s3_valid;
    reg s3_rf_we;
    reg [2:0] s3_rf_addr;
    reg [7:0] s3_rf_data;
    reg s3_mem_we;
    reg [7:0] s3_mem_addr;
    reg [7:0] s3_mem_data;
    reg s3_flags_we;
    reg [3:0] s3_flags;

    reg halted_r;
    wire [3:0] s2_opcode;
    wire [2:0] s2_rd;
    wire [2:0] s2_rs1;
    wire [2:0] s2_rs2;
    wire [7:0] s2_imm8;
    wire [8:0] s2_addr9;
    wire [2:0] s2_cond;
    wire [7:0] s2_port;
    wire s2_io_dir;

    instr_decoder s2_decoder (
        .instr(s2_ir),
        .opcode(s2_opcode),
        .rd(s2_rd),
        .rs1(s2_rs1),
        .rs2(s2_rs2),
        .imm8(s2_imm8),
        .addr9(s2_addr9),
        .cond(s2_cond),
        .port(s2_port),
        .io_dir(s2_io_dir)
    );

    wire [2:0] s2_ra2 =
        (s2_opcode == 4'h3 || s2_opcode == 4'hE) ? s2_rd : s2_rs2;

    wire [7:0] rf_rd1;
    wire [7:0] rf_rd2;
    reg [7:0] a;
    reg [7:0] b;

    register_file rf (
        .clk(clk),
        .rst_n(rst_n),
        .ra1(s2_rs1),
        .ra2(s2_ra2),
        .rd1(rf_rd1),
        .rd2(rf_rd2),
        .we(s3_valid && s3_rf_we),
        .wa(s3_rf_addr),
        .wd(s3_rf_data)
    );

    always @* begin
        a = rf_rd1;
        b = rf_rd2;
        if (s3_valid && s3_rf_we && s3_rf_addr == s2_rs1)
            a = s3_rf_data;
        if (s3_valid && s3_rf_we && s3_rf_addr == s2_ra2)
            b = s3_rf_data;
    end

    wire [7:0] alu_result;
    wire alu_z;
    wire alu_n;
    wire alu_c;
    wire alu_v;

    alu alu_inst (
        .a(a),
        .b(b),
        .op(s2_opcode),
        .result(alu_result),
        .flag_z(alu_z),
        .flag_n(alu_n),
        .flag_c(alu_c),
        .flag_v(alu_v)
    );

    wire [3:0] alu_flags = {alu_z, alu_n, alu_c, alu_v};
    wire [3:0] flags_out;
    wire [3:0] branch_flags =
        (s3_valid && s3_flags_we) ? s3_flags : flags_out;

    flags_reg flags_inst (
        .clk(clk),
        .rst_n(rst_n),
        .flags_we(s3_valid && s3_flags_we),
        .flags_in(s3_flags),
        .flags_out(flags_out)
    );

    wire [7:0] dmem_rdata;
    data_memory dmem (
        .clk(clk),
        .addr(s3_valid ? s3_mem_addr : 8'h00),
        .we(s3_valid && s3_mem_we),
        .wdata(s3_valid ? s3_mem_data : 8'h00),
        .rdata(dmem_rdata)
    );

    reg cu_rf_we;
    reg cu_mem_we;
    reg cu_flags_we;
    reg [1:0] cu_wb_sel;
    reg branch_taken;
    reg cu_halted;

    always @* begin
        cu_rf_we = 1'b0;
        cu_mem_we = 1'b0;
        cu_flags_we = 1'b0;
        cu_wb_sel = 2'b00;
        branch_taken = 1'b0;
        cu_halted = 1'b0;

        case (s2_opcode)
            4'h1: begin cu_rf_we = 1'b1; cu_wb_sel = 2'b10; end
            4'h2: begin cu_rf_we = 1'b1; cu_wb_sel = 2'b01; end
            4'h3: cu_mem_we = 1'b1;
            4'h4, 4'h5, 4'h6, 4'h7, 4'h8,
            4'h9, 4'hA: begin cu_rf_we = 1'b1; cu_flags_we = 1'b1; cu_wb_sel = 2'b00; end
            4'hB: cu_flags_we = 1'b1;
            4'hC: branch_taken = 1'b1;
            4'hD: begin
                case (s2_cond)
                    3'b000: branch_taken = branch_flags[3];
                    3'b001: branch_taken = !branch_flags[3];
                    3'b010: branch_taken = branch_flags[1];
                    3'b011: branch_taken = !branch_flags[1];
                    3'b100: branch_taken = branch_flags[2];
                    3'b101: branch_taken = !branch_flags[2];
                    3'b110: branch_taken = branch_flags[0];
                    3'b111: branch_taken = !branch_flags[0];
                endcase
            end
            4'hE: begin
                if (s2_io_dir)
                    cu_mem_we = 1'b0;
                else begin
                    cu_rf_we = 1'b1;
                    cu_wb_sel = 2'b11;
                end
            end
            4'hF: cu_halted = 1'b1;
            default: begin end
        endcase
    end

    reg [7:0] s2_rf_data;
    reg [7:0] s2_mem_addr;
    reg [7:0] s2_mem_data;
    always @* begin
        s2_rf_data = alu_result;
        s2_mem_addr = a;
        s2_mem_data = b;

        case (cu_wb_sel)
            2'b01: s2_rf_data = dmem_rdata;
            2'b10: s2_rf_data = s2_imm8;
            2'b11: s2_rf_data = io_rdata;
            default: s2_rf_data = alu_result;
        endcase
    end

    wire io_request = s2_valid && s2_opcode == 4'hE;
    wire io_stall = io_request && !io_ready;
    wire load_use_stall =
        s1_valid && s2_valid && s2_opcode == 4'h2 &&
        ((imem_data[8:6] == s2_rd) ||
         (imem_data[5:3] == s2_rd) ||
         (imem_data[11:9] == s2_rd));

    wire pipeline_stall = io_stall || load_use_stall;
    assign imem_addr = pc;
    assign io_port = s2_valid ? s2_imm8 : 8'h00;
    assign io_wdata = s2_valid ? b : 8'h00;
    assign io_rd = s2_valid && s2_opcode == 4'hE && !s2_io_dir;
    assign io_wr = s2_valid && s2_opcode == 4'hE && s2_io_dir;
    assign halted = halted_r && !s3_valid;

    assign retire = rst_n && s3_valid && !io_stall;
    assign retire_pc = s3_valid ? s3_pc : 9'h000;
    assign retire_ir = s3_valid ? s3_ir : 16'h0000;
    assign retire_rf_we = s3_valid ? s3_rf_we : 1'b0;
    assign retire_rf_addr = (s3_valid && s3_rf_we) ? s3_rf_addr : 3'b000;
    assign retire_rf_data = (s3_valid && s3_rf_we) ? s3_rf_data : 8'h00;
    assign retire_mem_we = s3_valid ? s3_mem_we : 1'b0;
    assign retire_mem_addr = (s3_valid && s3_mem_we) ? s3_mem_addr : 8'h00;
    assign retire_mem_data = (s3_valid && s3_mem_we) ? s3_mem_data : 8'h00;
    assign retire_flags = s3_valid && s3_flags_we ? s3_flags : flags_out;

    always @(posedge clk) begin
        if (!rst_n) begin
            pc <= 9'h000;
            s1_valid <= 1'b0;
            s1_pc <= 9'h000;
            s1_ir <= 16'h0000;
            s2_valid <= 1'b0;
            s2_pc <= 9'h000;
            s2_ir <= 16'h0000;
            s3_valid <= 1'b0;
            s3_pc <= 9'h000;
            s3_ir <= 16'h0000;
            s3_rf_we <= 1'b0;
            s3_rf_addr <= 3'b000;
            s3_rf_data <= 8'h00;
            s3_mem_we <= 1'b0;
            s3_mem_addr <= 8'h00;
            s3_mem_data <= 8'h00;
            s3_flags_we <= 1'b0;
            s3_flags <= 4'b0000;
            halted_r <= 1'b0;
        end else begin
            if (halted_r) begin
                s3_valid <= 1'b0;
                s3_rf_we <= 1'b0;
                s3_mem_we <= 1'b0;
                s3_flags_we <= 1'b0;
            end else if (io_stall) begin
                pc <= pc;
                s1_valid <= s1_valid;
                s1_pc <= s1_pc;
                s1_ir <= s1_ir;
                s2_valid <= s2_valid;
                s2_pc <= s2_pc;
                s2_ir <= s2_ir;
                s3_valid <= s3_valid;
            end else begin
                s3_valid <= s2_valid;
                s3_pc <= s2_pc;
                s3_ir <= s2_ir;
                s3_rf_we <= s2_valid ? cu_rf_we : 1'b0;
                s3_rf_addr <= s2_rd;
                s3_rf_data <= s2_rf_data;
                s3_mem_we <= s2_valid ? cu_mem_we : 1'b0;
                s3_mem_addr <= s2_mem_addr;
                s3_mem_data <= s2_mem_data;
                s3_flags_we <= s2_valid ? cu_flags_we : 1'b0;
                s3_flags <= alu_flags;

                if (load_use_stall) begin
                    s1_valid <= s1_valid;
                    s1_pc <= s1_pc;
                    s1_ir <= s1_ir;
                    s2_valid <= s2_valid;
                    s2_pc <= s2_pc;
                    s2_ir <= s2_ir;
                end else begin
                    s1_valid <= 1'b1;
                    s1_pc <= pc;
                    s1_ir <= imem_data;
                    s2_valid <= s1_valid;
                    s2_pc <= s1_pc;
                    s2_ir <= s1_ir;

                    if (branch_taken) begin
                        s1_valid <= 1'b0;
                        s2_valid <= 1'b0;
                        pc <= s2_addr9;
                    end else begin
                        pc <= pc + 9'h001;
                    end
                end

                if (s2_valid && s2_opcode == 4'hF)
                    halted_r <= 1'b1;
            end
        end
    end

endmodule
