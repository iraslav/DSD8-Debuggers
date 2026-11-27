        LDI R1, 5
        LDI R2, 3
        ADD R3, R1, R2
        SUB R4, R1, R2
        AND R5, R1, R2
        OR  R6, R1, R2
        XOR R7, R1, R2
        SHL R7, R7
        SHR R7, R7
        CMP R1, R2
        LDI R4, 16
        ST [R4], R3
        LD R5, [R4]
        ADD R6, R5, R2
        ADD R6, R6, R1
        CMP R1, R2
        BEQ NOT_TAKEN
        BNE TAKEN
NOT_TAKEN:
        LDI R7, 0
TAKEN:
        OUT 0x02, R6
        HLT
