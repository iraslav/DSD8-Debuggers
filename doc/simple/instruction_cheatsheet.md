# DSD-8 instruction cheatsheet

| Name | What it does | Example |
|---|---|---|
| NOP | Does nothing. | `NOP` leaves registers unchanged. |
| LDI | Puts a small number in a register. | `LDI R1,5` means `R1 = 5`. |
| LD | Reads one byte from memory. | `LD R3,[R1]` means `R3 = memory[R1]`. |
| ST | Writes one byte to memory. | `ST [R1],R2` means `memory[R1] = R2`. |
| ADD | Adds two registers. | `ADD R3,R1,R2` means `R3 = R1+R2`. |
| SUB | Subtracts the second register from the first. | `SUB R3,R1,R2` means `R3 = R1-R2`. |
| AND | Keeps bits set in both inputs. | `AND R3,R1,R2` means `R3 = R1 AND R2`. |
| OR | Keeps bits set in either input. | `OR R3,R1,R2` means `R3 = R1 OR R2`. |
| XOR | Keeps bits that differ. | `XOR R3,R1,R2` means `R3 = R1 XOR R2`. |
| SHL | Shifts a register left by one bit. | `SHL R3,R1` means `R3 = R1 shifted left`. |
| SHR | Shifts a register right by one bit. | `SHR R3,R1` means `R3 = R1 shifted right`. |
| CMP | Compares two registers and sets flags. | `CMP R1,R2` means compare `R1` with `R2`. |
| JMP | Always jumps to an address. | `JMP 0x010` means go to address `0x010`. |
| BEQ family | Jumps when its condition is true. Other names are BNE, BCS, BCC, BMI, BPL, BVS, and BVC. | `BEQ 0x010` means go there when the zero flag is 1. |
| IN / OUT | Reads from or writes to an I/O port. | `IN R1,0x40` reads port `0x40`; `OUT 0x40,R1` writes it. |
| HLT | Stops the processor. | `HLT` ends the program. |

There is no `MUL` instruction. Multiply is a loop of `ADD` and `SUB`.

