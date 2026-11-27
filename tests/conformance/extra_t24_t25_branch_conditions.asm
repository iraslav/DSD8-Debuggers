        LDI R0, 0
        LDI R1, 1
        LDI R2, 0x7F
        LDI R3, 0x80

        CMP R0, R0
        BEQ beq_taken
        NOP
beq_taken:
        CMP R0, R1
        BEQ beq_done
        NOP
beq_done:
        CMP R0, R1
        BNE bne_taken
        NOP
bne_taken:
        CMP R0, R0
        BNE bne_done
        NOP
bne_done:
        CMP R1, R0
        BCS bcs_taken
        NOP
bcs_taken:
        CMP R1, R0
        BCC bcc_not_taken_done
        NOP
bcc_not_taken_done:
        CMP R0, R1
        BCC bcc_taken
        NOP
bcc_taken:
        CMP R0, R1
        BCS bcs_not_taken_done
        NOP
bcs_not_taken_done:
        SUB R4, R0, R1
        BMI bmi_taken
        NOP
bmi_taken:
        ADD R4, R1, R1
        BMI bmi_not_taken_done
        NOP
bmi_not_taken_done:
        ADD R4, R1, R1
        BPL bpl_taken
        NOP
bpl_taken:
        SUB R4, R0, R1
        BPL bpl_not_taken_done
        NOP
bpl_not_taken_done:
        ADD R4, R2, R1
        BVS bvs_taken
        NOP
bvs_taken:
        ADD R4, R1, R1
        BVS bvs_not_taken_done
        NOP
bvs_not_taken_done:
        ADD R4, R1, R1
        BVC bvc_taken
        NOP
bvc_taken:
        ADD R4, R2, R1
        BVC bvc_not_taken_done
        NOP
bvc_not_taken_done:
        HLT
