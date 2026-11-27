        LDI R0, 0xFF
        LDI R1, 1
        ADD R2, R0, R1
        LDI R0, 0x7F
        ADD R2, R0, R1
        LDI R0, 0
        SUB R2, R0, R1
        LDI R0, 0x80
        SUB R2, R0, R1
        CMP R0, R1
        HLT
