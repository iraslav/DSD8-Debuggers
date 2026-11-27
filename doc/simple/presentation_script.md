# Five-minute presentation script

## Part A — Member A: project and stages

Assalam-o-alaikum. Hamara project DSD-8 processor hai. Yeh 8-bit values par kaam karta hai. Is mein teen pipeline stages hain. Har instruction in stages se guzarti hai.

Stage 1 fetch hai. Yeh program memory se instruction leti hai. Stage 2 execute hai. Yeh instruction decode karti hai, registers read karti hai, ALU chalati hai, aur memory ya I/O ka kaam karti hai. Stage 3 writeback hai. Yeh result register mein likhti hai, flags update karti hai, aur instruction retire karti hai.

Assembly ki simple misaal dekhein. Pehle `LDI R1,10` aur `LDI R2,10` registers mein numbers rakhte hain. Phir `ADD R3,R1,R2` ka matlab hai `R3 = R1+R2`. Pipeline ki wajah se alag instructions alag stages mein ek hi waqt par chal sakti hain.

Diagram mein blue Fetch, yellow Execute, aur green Writeback hai. Register File operands deti hai. Data Memory `LD` aur `ST` ke liye hai. `retire` ka matlab hai ke instruction ka result final ho gaya. Hum wave mein `retire_pc` se instruction ka address dekh sakte hain.

## Part B — Member B: timing and hazards

Yeh timing picture real Icarus simulation se bani hai. Clock 10 ns ka hai. Cycle 1 pehla valid fetch hai. Pehli instruction cycle 3, 65 ns par retire hoti hai. Cycle 4 aur 5 mein forwarding bhi dikhti hai. Cycle 8 par `branch_taken` hota hai. HLT fetch hui thi, lekin branch usay flush karti hai.

Data forwarding ke liye `doc/simple/pipeline_example.vcd` kholen. 85 ns par dekhein. Execute mein `SUB R4,R3,R3` hai. Writeback mein pichla `ADD R3,R1,R2` hai. `s3_rf_data` operands `a` aur `b` tak jata hai.

Load-use ke liye `doc/simple/load_use_repro.vcd` ko 85 se 115 ns tak zoom karein. `load_use_stall` bar bar high rehta hai. `s1` aur `s2` nahi badalte. `retire_pc` bhi dobara 3 hota hai. Yeh one-cycle bubble nahi hai. Is checkout mein yeh bug hai, is liye hum isay chhupa nahi rahe.

Branch ke liye `doc/simple/pipeline_example.vcd` ko 115 ns par dekhein. `branch_taken` high hai aur `s1_valid` clear hota hai. Slow I/O ke liye `doc/simple/slow_io_example.vcd` kholen. OUT wait 65 se 95 ns tak hai. IN wait 115 ns par hai. `io_stall` aur `io_ready` dikhayen.

## Part C — Member C: checks and takeaway

Verification ke liye hum `make test` chalate hain. Is mein 11 unit benches pass hue. ALU random test ne 80,000 comparisons kiye aur zero errors diye. `make conformance` mein local suite ke 7 programs pass hue. Is checkout mein official T01 se T40 files maujood nahi hain.

Bug log mein kuch misaalein hain. Ek unused `retire_r` assignment compile ko rok sakti thi. Branch pehle purane flags par nirbhar ho sakti thi. Slow I/O ke dauran retire signal instruction ko do martaba dikha sakta tha. Yeh masail log mein likhe hain.

Hamara takeaway yeh hai: DSD-8 teen stages mein instructions chalata hai, aur waveforms batate hain ke har instruction asal mein kya kar rahi hai. Load-use stall ka masla abhi bhi saamne hai. Hum sirf wahi claim karte hain jo simulation ne dikhaya.

## Likely viva questions

**1. Pipeline kya hoti hai?**  
Alag instructions alag stages mein ek saath hoti hain. Is se har clock mein zyada kaam ho sakta hai.

**2. `retire` ka kya matlab hai?**  
Instruction ka result final ho chuka hai. `retire_pc` us instruction ka address dikhata hai.

**3. Forwarding kyun chahiye?**  
Naya result register file mein aane se pehle aglay instruction ko chahiye ho sakta hai. `s3_rf_data` usay seedha `a` ya `b` tak deta hai.

**4. Z, N, C, V flags kya batate hain?**  
Z zero result, N negative sign, C carry, aur V signed overflow batate hain. Branch in flags ko check kar sakti hai.

**5. `prog_counter` aur `control_unit` `dsd8_cpu` ke andar kyun instantiate nahi hote?**  
`dsd8_cpu` apna `pc` register aur next-address logic khud rakhta hai. Opcode control bhi `always @*` ke `case` mein hai; standalone modules yahan use nahi hote.

