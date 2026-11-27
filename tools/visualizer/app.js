const byId = (id) => document.getElementById(id);
const assemblyInput = byId("assembly");
const cycleLimitInput = byId("cycleLimit");
const runButton = byId("runButton");
const statusLine = byId("status");
const slider = byId("cycleSlider");
const speed = byId("speed");

let trace = null;
let cycleIndex = 0;
let playbackTimer = null;
let registerNodes = [];
let memoryNodes = [];

function hex(value, width = 2) {
  return value === null || value === undefined
    ? "--"
    : `0x${Number(value).toString(16).toUpperCase().padStart(width, "0")}`;
}

function setStatus(message, kind = "") {
  statusLine.textContent = message;
  statusLine.className = `status ${kind}`.trim();
}

function createCells() {
  const registers = byId("registerGrid");
  registers.replaceChildren();
  registerNodes = [];
  for (let index = 0; index < 8; index += 1) {
    const cell = document.createElement("div");
    cell.className = "register-cell";
    const label = document.createElement("span");
    label.textContent = `R${index}`;
    const value = document.createElement("b");
    value.textContent = "0x00";
    cell.append(label, value);
    registers.append(cell);
    registerNodes.push({ cell, value });
  }

  const memory = byId("memoryGrid");
  memory.replaceChildren();
  memoryNodes = [];
  for (let address = 0; address < 16; address += 1) {
    const cell = document.createElement("div");
    cell.className = "memory-cell";
    const label = document.createElement("small");
    label.textContent = hex(address);
    const value = document.createElement("span");
    value.textContent = "00";
    cell.append(label, value);
    memory.append(cell);
    memoryNodes.push({ cell, value });
  }
}

function buildProgramListing(program) {
  const listing = byId("programListing");
  listing.replaceChildren();
  for (const instruction of program) {
    const row = document.createElement("div");
    row.className = "code-row";
    row.dataset.pc = instruction.pc;
    const address = document.createElement("span");
    address.className = "address";
    address.textContent = hex(instruction.pc, 3);
    const word = document.createElement("span");
    word.className = "word";
    word.textContent = instruction.word;
    const text = document.createElement("span");
    text.textContent = instruction.text;
    row.append(address, word, text);
    listing.append(row);
  }
  byId("programCount").textContent = `${program.length} instructions`;
}

function setStage(prefix, key, stage) {
  const card = document.querySelector(`.${prefix}-card`);
  card.classList.toggle("active", stage.valid);
  byId(`${key}Pc`).textContent = stage.valid ? `PC ${hex(stage.pc, 3)}` : "Bubble";
  byId(`${key}Instruction`).textContent = stage.text;
}

function renderProgramHighlights(cycle) {
  for (const row of byId("programListing").querySelectorAll(".code-row")) {
    row.classList.remove("fetching", "executing", "writing");
  }
  const pairs = [
    ["fetch", "fetching"],
    ["execute", "executing"],
    ["writeback", "writing"],
  ];
  for (const [stageName, className] of pairs) {
    const stage = cycle[stageName];
    if (stage.valid) {
      const row = byId("programListing").querySelector(`[data-pc="${stage.pc}"]`);
      if (row) row.classList.add(className);
    }
  }
}

function renderEvents(cycle) {
  const events = [];
  if (cycle.events.retire) events.push(["Retired", "good"]);
  if (cycle.events.forwardA || cycle.events.forwardB) {
    const operands = [cycle.events.forwardA ? "a" : "", cycle.events.forwardB ? "b" : ""]
      .filter(Boolean)
      .join(" and ");
    events.push([`Forwarding to ${operands}`, "good"]);
  }
  if (cycle.events.loadUseStall) events.push(["Load-use stall", "alert"]);
  if (cycle.events.ioStall) events.push(["I/O wait", "warn"]);
  if (cycle.events.branchTaken) events.push(["Branch taken · younger stages flushed", "warn"]);
  if (!events.length) events.push(["Pipeline advancing", ""]);
  const strip = byId("eventStrip");
  strip.replaceChildren();
  for (const [label, kind] of events) {
    const badge = document.createElement("span");
    badge.className = `event-badge ${kind}`.trim();
    badge.textContent = label;
    strip.append(badge);
  }
}

function renderRegisters(cycle) {
  for (let index = 0; index < registerNodes.length; index += 1) {
    registerNodes[index].value.textContent = hex(cycle.registers[index]);
    registerNodes[index].cell.classList.toggle(
      "changed",
      Boolean(cycle.commit.rfWrite && cycle.commit.rfWrite.address === index),
    );
  }
  const flags = cycle.commit.flags ?? 0;
  const flagNames = [["Z", 3], ["N", 2], ["C", 1], ["V", 0]];
  byId("flagSummary").textContent = flagNames
    .map(([name, bit]) => `${name} ${(flags >> bit) & 1}`)
    .join(" · ");
  const flagsRow = byId("flagsRow");
  flagsRow.replaceChildren();
  for (const [name, bit] of flagNames) {
    const badge = document.createElement("span");
    badge.className = `flag ${(flags >> bit) & 1 ? "on" : ""}`.trim();
    badge.textContent = `${name} ${(flags >> bit) & 1}`;
    flagsRow.append(badge);
  }

  for (let address = 0; address < 16; address += 1) {
    memoryNodes[address].value.textContent = Number(cycle.memoryHead[address])
      .toString(16).toUpperCase().padStart(2, "0");
    memoryNodes[address].cell.classList.toggle(
      "changed",
      Boolean(cycle.commit.memWrite && cycle.commit.memWrite.address === address),
    );
  }
  const write = cycle.commit.memWrite;
  byId("memoryEvent").textContent = write
    ? `Store ${hex(write.data)} → [${hex(write.address)}]`
    : "No store this cycle";
}

function renderAluAndIo(cycle) {
  byId("aluA").textContent = hex(cycle.alu.a);
  byId("aluB").textContent = hex(cycle.alu.b);
  byId("aluResult").textContent = hex(cycle.alu.result);
  const aluFlags = cycle.alu.flags;
  byId("aluFlags").textContent = `ALU flags Z/N/C/V: ${
    aluFlags === null ? "----" : Number(aluFlags).toString(2).padStart(4, "0")
  }`;

  const io = cycle.io;
  if (io.read || io.write || cycle.events.ioStall) {
    const operation = io.read ? "IN" : io.write ? "OUT" : "WAIT";
    byId("ioReadout").textContent =
      `${operation} · port ${hex(io.port)} · data ${hex(io.write ? io.writeData : io.readData)} · ` +
      `ready ${io.ready ? "yes" : "no"}`;
  } else {
    byId("ioReadout").textContent = "No active I/O request";
  }
  byId("ledReadout").textContent = `LED output: ${hex(io.leds)}`;
}

function renderRetireHistory() {
  const list = byId("retireList");
  const completed = trace.cycles.slice(0, cycleIndex + 1)
    .filter((cycle) => cycle.commit.pc !== null)
    .slice(-10)
    .reverse();
  list.replaceChildren();
  if (!completed.length) {
    const empty = document.createElement("p");
    empty.className = "empty-message";
    empty.textContent = "No instructions retired yet.";
    list.append(empty);
    return;
  }
  const textByPc = new Map(trace.program.map((instruction) => [instruction.pc, instruction.text]));
  for (const cycle of completed) {
    const row = document.createElement("div");
    row.className = "retire-row";
    const seq = document.createElement("span");
    seq.className = "seq";
    seq.textContent = `C${cycle.cycle}`;
    const pc = document.createElement("span");
    pc.className = "pc";
    pc.textContent = hex(cycle.commit.pc, 3);
    const instruction = document.createElement("span");
    instruction.textContent = textByPc.get(cycle.commit.pc) || "Instruction";
    const change = document.createElement("span");
    change.className = "write";
    if (cycle.commit.rfWrite) {
      change.textContent = `R${cycle.commit.rfWrite.address} ← ${hex(cycle.commit.rfWrite.data)}`;
    } else if (cycle.commit.memWrite) {
      change.textContent = `[${hex(cycle.commit.memWrite.address)}] ← ${hex(cycle.commit.memWrite.data)}`;
    }
    row.append(seq, pc, instruction, change);
    list.append(row);
  }
}

function render() {
  if (!trace || !trace.cycles.length) return;
  const cycle = trace.cycles[cycleIndex];
  byId("cycleTitle").textContent = `Cycle ${cycle.cycle} · ${cycle.timeNs} ns`;
  byId("seekStart").textContent = "Cycle 1";
  byId("seekEnd").textContent = `Cycle ${trace.cycleCount}`;
  slider.max = String(trace.cycleCount - 1);
  slider.value = String(cycleIndex);
  setStage("fetch", "fetch", cycle.fetch);
  setStage("execute", "execute", cycle.execute);
  setStage("writeback", "writeback", cycle.writeback);
  renderProgramHighlights(cycle);
  renderEvents(cycle);
  renderRegisters(cycle);
  renderAluAndIo(cycle);
  renderRetireHistory();
}

function setPlaybackButtons(enabled) {
  for (const id of ["firstButton", "backButton", "playButton", "pauseButton", "nextButton"]) {
    byId(id).disabled = !enabled;
  }
  slider.disabled = !enabled;
}

function stopPlayback() {
  if (playbackTimer !== null) {
    window.clearInterval(playbackTimer);
    playbackTimer = null;
  }
}

function moveTo(index) {
  if (!trace) return;
  cycleIndex = Math.max(0, Math.min(trace.cycleCount - 1, index));
  render();
}

function startPlayback() {
  if (!trace || playbackTimer !== null) return;
  if (cycleIndex >= trace.cycleCount - 1) moveTo(0);
  playbackTimer = window.setInterval(() => {
    if (cycleIndex >= trace.cycleCount - 1) {
      stopPlayback();
      return;
    }
    moveTo(cycleIndex + 1);
  }, Number(speed.value));
}

runButton.addEventListener("click", async () => {
  stopPlayback();
  runButton.disabled = true;
  setStatus("Assembling and running the RTL simulation…");
  try {
    const response = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        assembly: assemblyInput.value,
        cycleLimit: Number(cycleLimitInput.value),
      }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || `Simulation failed (${response.status}).`);
    trace = result;
    cycleIndex = 0;
    buildProgramListing(trace.program);
    setPlaybackButtons(trace.cycleCount > 0);
    render();
    const endMessage = trace.hitLimit
      ? `Cycle limit reached at ${trace.cycleCount} displayed cycles.`
      : `RTL simulation finished after ${trace.cycleCount} displayed cycles.`;
    setStatus(`${endMessage} Use Play or step through the trace.`, trace.hitLimit ? "" : "success");
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    runButton.disabled = false;
  }
});

byId("firstButton").addEventListener("click", () => { stopPlayback(); moveTo(0); });
byId("backButton").addEventListener("click", () => { stopPlayback(); moveTo(cycleIndex - 1); });
byId("nextButton").addEventListener("click", () => { stopPlayback(); moveTo(cycleIndex + 1); });
byId("playButton").addEventListener("click", startPlayback);
byId("pauseButton").addEventListener("click", stopPlayback);
slider.addEventListener("input", () => { stopPlayback(); moveTo(Number(slider.value)); });
speed.addEventListener("input", () => { byId("speedValue").textContent = `${speed.value} ms`; });

createCells();
