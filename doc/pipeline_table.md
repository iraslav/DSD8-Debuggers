# DSD-8 Pipeline Tables

## Demo ALU program

| cycle | time (ns) | IF | ID/EX | EX-WB | marker | retire pc |
|---:|---:|---|---|---|---|---|
| 1 | 35 | - | - | - | - | - |
| 2 | 45 | 000 LDI R1,0x05 | - | - | - | - |
| 3 | 55 | 001 LDI R2,0x03 | 000 LDI R1,0x05 | - | - | - |
| 4 | 65 | 002 ADD R3,R1,R2 | 001 LDI R2,0x03 | 000 LDI R1,0x05 | - | 000 |
| 5 | 75 | 003 SUB R4,R1,R2 | 002 ADD R3,R1,R2 | 001 LDI R2,0x03 | - | 001 |
| 6 | 85 | 004 AND R5,R1,R2 | 003 SUB R4,R1,R2 | 002 ADD R3,R1,R2 | - | 002 |
| 7 | 95 | 005 OR R6,R1,R2 | 004 AND R5,R1,R2 | 003 SUB R4,R1,R2 | - | 003 |
| 8 | 105 | 006 XOR R7,R1,R2 | 005 OR R6,R1,R2 | 004 AND R5,R1,R2 | - | 004 |
| 9 | 115 | 007 SHL R7,R7 | 006 XOR R7,R1,R2 | 005 OR R6,R1,R2 | - | 005 |
| 10 | 125 | 008 SHR R7,R7 | 007 SHL R7,R7 | 006 XOR R7,R1,R2 | - | 006 |
| 11 | 135 | 009 CMP R1,R2 | 008 SHR R7,R7 | 007 SHL R7,R7 | - | 007 |
| 12 | 145 | 00A LDI R4,0x10 | 009 CMP R1,R2 | 008 SHR R7,R7 | - | 008 |
| 13 | 155 | 00B ST [R4],R3 | 00A LDI R4,0x10 | 009 CMP R1,R2 | - | 009 |
| 14 | 165 | 00C LD R5,[R4] | 00B ST [R4],R3 | 00A LDI R4,0x10 | - | 00A |
| 15 | 175 | 00D ADD R6,R5,R2 | 00C LD R5,[R4] | 00B ST [R4],R3 | - | 00B |
| 16 | 185 | 00E ADD R6,R6,R1 | 00D ADD R6,R5,R2 | 00C LD R5,[R4] | - | 00C |
| 17 | 195 | 00F CMP R1,R2 | 00E ADD R6,R6,R1 | 00D ADD R6,R5,R2 | - | 00D |
| 18 | 205 | 010 BEQ 0x012 | 00F CMP R1,R2 | 00E ADD R6,R6,R1 | - | 00E |
| 19 | 215 | 011 BNE 0x013 | 010 BEQ 0x012 | 00F CMP R1,R2 | - | 00F |
| 20 | 225 | 012 LDI R7,0x00 | 011 BNE 0x013 | 010 BEQ 0x012 | flush taken | 010 |
| 21 | 235 | - | - | 011 BNE 0x013 | - | 011 |
| 22 | 245 | 013 OUT 0x02,R6 | - | - | - | - |
| 23 | 255 | 014 HLT | 013 OUT 0x02,R6 | - | - | - |
| 24 | 265 | - | 014 HLT | 013 OUT 0x02,R6 | - | 013 |
| 25 | 275 | - | - | 014 HLT | - | 014 |
| 26 | 285 | - | - | - | - | - |

## B.1 Multiply

| cycle | time (ns) | IF | ID/EX | EX-WB | marker | retire pc |
|---:|---:|---|---|---|---|---|
| 1 | 35 | - | - | - | - | - |
| 2 | 45 | 000 LDI R1,0x0D | - | - | - | - |
| 3 | 55 | 001 LDI R2,0x07 | 000 LDI R1,0x0D | - | - | - |
| 4 | 65 | 002 LDI R3,0x00 | 001 LDI R2,0x07 | 000 LDI R1,0x0D | - | 000 |
| 5 | 75 | 003 LDI R4,0x01 | 002 LDI R3,0x00 | 001 LDI R2,0x07 | - | 001 |
| 6 | 85 | 004 LDI R5,0x00 | 003 LDI R4,0x01 | 002 LDI R3,0x00 | - | 002 |
| 7 | 95 | 005 CMP R2,R5 | 004 LDI R5,0x00 | 003 LDI R4,0x01 | - | 003 |
| 8 | 105 | 006 BEQ 0x00A | 005 CMP R2,R5 | 004 LDI R5,0x00 | - | 004 |
| 9 | 115 | 007 ADD R3,R3,R1 | 006 BEQ 0x00A | 005 CMP R2,R5 | - | 005 |
| 10 | 125 | 008 SUB R2,R2,R4 | 007 ADD R3,R3,R1 | 006 BEQ 0x00A | - | 006 |
| 11 | 135 | 009 JMP 0x004 | 008 SUB R2,R2,R4 | 007 ADD R3,R3,R1 | - | 007 |
| 12 | 145 | 00A OUT 0x02,R3 | 009 JMP 0x004 | 008 SUB R2,R2,R4 | flush taken | 008 |
| 13 | 155 | - | - | 009 JMP 0x004 | - | 009 |
| 14 | 165 | 004 LDI R5,0x00 | - | - | - | - |
| 15 | 175 | 005 CMP R2,R5 | 004 LDI R5,0x00 | - | - | - |
| 16 | 185 | 006 BEQ 0x00A | 005 CMP R2,R5 | 004 LDI R5,0x00 | - | 004 |
| 17 | 195 | 007 ADD R3,R3,R1 | 006 BEQ 0x00A | 005 CMP R2,R5 | - | 005 |
| 18 | 205 | 008 SUB R2,R2,R4 | 007 ADD R3,R3,R1 | 006 BEQ 0x00A | - | 006 |
| 19 | 215 | 009 JMP 0x004 | 008 SUB R2,R2,R4 | 007 ADD R3,R3,R1 | - | 007 |
| 20 | 225 | 00A OUT 0x02,R3 | 009 JMP 0x004 | 008 SUB R2,R2,R4 | flush taken | 008 |
| 21 | 235 | - | - | 009 JMP 0x004 | - | 009 |
| 22 | 245 | 004 LDI R5,0x00 | - | - | - | - |
| 23 | 255 | 005 CMP R2,R5 | 004 LDI R5,0x00 | - | - | - |
| 24 | 265 | 006 BEQ 0x00A | 005 CMP R2,R5 | 004 LDI R5,0x00 | - | 004 |
| 25 | 275 | 007 ADD R3,R3,R1 | 006 BEQ 0x00A | 005 CMP R2,R5 | - | 005 |
| 26 | 285 | 008 SUB R2,R2,R4 | 007 ADD R3,R3,R1 | 006 BEQ 0x00A | - | 006 |
| 27 | 295 | 009 JMP 0x004 | 008 SUB R2,R2,R4 | 007 ADD R3,R3,R1 | - | 007 |
| 28 | 305 | 00A OUT 0x02,R3 | 009 JMP 0x004 | 008 SUB R2,R2,R4 | flush taken | 008 |
| 29 | 315 | - | - | 009 JMP 0x004 | - | 009 |
| 30 | 325 | 004 LDI R5,0x00 | - | - | - | - |
| 31 | 335 | 005 CMP R2,R5 | 004 LDI R5,0x00 | - | - | - |
| 32 | 345 | 006 BEQ 0x00A | 005 CMP R2,R5 | 004 LDI R5,0x00 | - | 004 |
| 33 | 355 | 007 ADD R3,R3,R1 | 006 BEQ 0x00A | 005 CMP R2,R5 | - | 005 |
| 34 | 365 | 008 SUB R2,R2,R4 | 007 ADD R3,R3,R1 | 006 BEQ 0x00A | - | 006 |
| 35 | 375 | 009 JMP 0x004 | 008 SUB R2,R2,R4 | 007 ADD R3,R3,R1 | - | 007 |
| 36 | 385 | 00A OUT 0x02,R3 | 009 JMP 0x004 | 008 SUB R2,R2,R4 | flush taken | 008 |
| 37 | 395 | - | - | 009 JMP 0x004 | - | 009 |
| 38 | 405 | 004 LDI R5,0x00 | - | - | - | - |
| 39 | 415 | 005 CMP R2,R5 | 004 LDI R5,0x00 | - | - | - |
| 40 | 425 | 006 BEQ 0x00A | 005 CMP R2,R5 | 004 LDI R5,0x00 | - | 004 |
| 41 | 435 | 007 ADD R3,R3,R1 | 006 BEQ 0x00A | 005 CMP R2,R5 | - | 005 |
| 42 | 445 | 008 SUB R2,R2,R4 | 007 ADD R3,R3,R1 | 006 BEQ 0x00A | - | 006 |
| 43 | 455 | 009 JMP 0x004 | 008 SUB R2,R2,R4 | 007 ADD R3,R3,R1 | - | 007 |
| 44 | 465 | 00A OUT 0x02,R3 | 009 JMP 0x004 | 008 SUB R2,R2,R4 | flush taken | 008 |
| 45 | 475 | - | - | 009 JMP 0x004 | - | 009 |
| 46 | 485 | 004 LDI R5,0x00 | - | - | - | - |
| 47 | 495 | 005 CMP R2,R5 | 004 LDI R5,0x00 | - | - | - |
| 48 | 505 | 006 BEQ 0x00A | 005 CMP R2,R5 | 004 LDI R5,0x00 | - | 004 |
| 49 | 515 | 007 ADD R3,R3,R1 | 006 BEQ 0x00A | 005 CMP R2,R5 | - | 005 |
| 50 | 525 | 008 SUB R2,R2,R4 | 007 ADD R3,R3,R1 | 006 BEQ 0x00A | - | 006 |
| 51 | 535 | 009 JMP 0x004 | 008 SUB R2,R2,R4 | 007 ADD R3,R3,R1 | - | 007 |
| 52 | 545 | 00A OUT 0x02,R3 | 009 JMP 0x004 | 008 SUB R2,R2,R4 | flush taken | 008 |
| 53 | 555 | - | - | 009 JMP 0x004 | - | 009 |
| 54 | 565 | 004 LDI R5,0x00 | - | - | - | - |
| 55 | 575 | 005 CMP R2,R5 | 004 LDI R5,0x00 | - | - | - |
| 56 | 585 | 006 BEQ 0x00A | 005 CMP R2,R5 | 004 LDI R5,0x00 | - | 004 |
| 57 | 595 | 007 ADD R3,R3,R1 | 006 BEQ 0x00A | 005 CMP R2,R5 | - | 005 |
| 58 | 605 | 008 SUB R2,R2,R4 | 007 ADD R3,R3,R1 | 006 BEQ 0x00A | - | 006 |
| 59 | 615 | 009 JMP 0x004 | 008 SUB R2,R2,R4 | 007 ADD R3,R3,R1 | - | 007 |
| 60 | 625 | 00A OUT 0x02,R3 | 009 JMP 0x004 | 008 SUB R2,R2,R4 | flush taken | 008 |
| 61 | 635 | - | - | 009 JMP 0x004 | - | 009 |
| 62 | 645 | 004 LDI R5,0x00 | - | - | - | - |
| 63 | 655 | 005 CMP R2,R5 | 004 LDI R5,0x00 | - | - | - |
| 64 | 665 | 006 BEQ 0x00A | 005 CMP R2,R5 | 004 LDI R5,0x00 | - | 004 |
| 65 | 675 | 007 ADD R3,R3,R1 | 006 BEQ 0x00A | 005 CMP R2,R5 | flush taken | 005 |
| 66 | 685 | - | - | 006 BEQ 0x00A | - | 006 |
| 67 | 695 | 00A OUT 0x02,R3 | - | - | - | - |
| 68 | 705 | 00B HLT | 00A OUT 0x02,R3 | - | - | - |
| 69 | 715 | - | 00B HLT | 00A OUT 0x02,R3 | - | 00A |
| 70 | 725 | - | - | 00B HLT | - | 00B |
| 71 | 735 | - | - | - | - | - |

## Operation timestamps

The values below are rising-edge execution times in ns in the ID/EX stage.

### demo_alu

- ADD: 75 ns
- SUB: 85 ns
- AND: 95 ns
- OR: 105 ns
- XOR: 115 ns
- SHL: 125 ns
- SHR: 135 ns
- CMP: 145 ns
- LD: 175 ns
- ST: 165 ns
- BEQ: 215 ns
- BNE: 225 ns
- OUT: 255 ns
- HLT: 265 ns

### B.1 multiply

- ADD: 125 ns
- SUB: 135 ns
- CMP: 105 ns
- BEQ: 115 ns
- OUT: 705 ns
- HLT: 715 ns

- Demo RAW hazard: back-to-back `ADD R6,R5,R2` / `ADD R6,R6,R1`; first ADD reaches ID/EX at the timestamp of the matching ADD.
- Demo load-use: `LD R5,[R4]` followed by `ADD R6,R5,R2`; load-use stall begins at the ADD following the LD.
- Demo branches: `BEQ` and `BNE` execute in ID/EX; marker `flush taken` applies when a taken branch redirects PC.
