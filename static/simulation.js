const form = document.querySelector("[data-bench-run]");
const analysis = document.querySelector("#analysis-mode");
const sine = document.querySelector("#sine-source");
const unitSelect = document.querySelector("[data-resistor-select]");
const unitLabels = document.querySelectorAll("[data-resistor-unit]");
const unitBehavior = document.querySelector("#unit-behavior");
const lastRunNote = document.querySelector("#previous-run");
const runButton = form?.querySelector("button[type=submit]");
const runningMessage = document.querySelector("#running-message");
const runStatus = document.querySelector("[data-run-status]");
const runStatusText = runStatus?.textContent;

function updateUnits(event) {
  if (unitSelect) {
    const unit = { ohm: "Ω", kohm: "kΩ" }[unitSelect.value] ?? "—";
    for (const label of unitLabels) label.textContent = unit;
    if (event && unitBehavior && unit !== "—") {
      unitBehavior.textContent = `Numbers unchanged. Resistors will be interpreted in ${unit}.`;
    }
  }
}

function updateSource() {
  if (analysis && sine) {
    const transient = analysis.value === "tran";
    sine.hidden = !transient;
    for (const control of sine.querySelectorAll("input")) {
      control.required = transient;
    }
  }
}

function markEdited() {
  if (lastRunNote) {
    lastRunNote.hidden = false;
    if (runStatus?.hasAttribute("data-current-result")) {
      runStatus.textContent = "Previous run";
      runStatus.classList.add("badge-previous");
    }
  }
}

unitSelect?.addEventListener("change", updateUnits);
analysis?.addEventListener("change", updateSource);
form?.addEventListener("input", markEdited);
form?.addEventListener("change", markEdited);
form?.addEventListener("submit", () => {
  runButton.disabled = true;
  if (runningMessage) runningMessage.textContent = "Running ngspice…";
  if (runStatus) {
    runStatus.textContent = "Running";
    runStatus.classList.remove("badge-previous");
    runStatus.classList.add("badge-running");
  }
  if (lastRunNote) lastRunNote.hidden = false;
});

window.addEventListener("pageshow", (event) => {
  updateSource();
  updateUnits();
  if (runButton) runButton.disabled = false;
  if (runningMessage) runningMessage.textContent = "";
  if (runStatus) {
    runStatus.textContent = runStatusText;
    runStatus.classList.remove("badge-running", "badge-previous");
  }
  if (event.persisted && lastRunNote && !lastRunNote.hidden) markEdited();
  if (!event.persisted) {
    const target = form?.querySelector("[aria-invalid=true]") ?? document.querySelector("[data-run-landing]");
    if (target) {
      target.focus({ preventScroll: true });
      const rect = target.getBoundingClientRect();
      if (rect.top < 0 || rect.bottom > window.innerHeight - 32) {
        target.scrollIntoView({ block: "start" });
      }
    }
  }
});

updateSource();
updateUnits();
