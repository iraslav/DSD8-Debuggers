        LDI R0, 0
        LDI R1, 1
        CMP R0, R1
        LDI R2, 0x20
        LD R3, [R2]
        BNE flags_preserved
        HLT
flags_preserved:
        LDI R4, 0x5A
        HLT
