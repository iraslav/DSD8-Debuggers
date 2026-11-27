        LDI R1, 0
        LDI R2, 0
        LDI R3, 1
loop:
        ADD R2, R2, R3
        SUB R1, R1, R3
        BNE loop
        OUT 0x02, R2
        HLT
