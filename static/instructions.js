const editor = document.querySelector("#instruction-editor");
const statusBox = document.querySelector("#instruction-save-status");

function instructionRow(data = {}) {
  const row = document.createElement("div");
  row.className = "instruction-row";
  row.innerHTML = `
    <label>Template<input name="template" value="${data.template || "standard"}"></label>
    <label>Field<input name="field" value="${data.field || "license_number"}"></label>
    <label>Instruction<textarea name="message">${data.message || ""}</textarea></label>
    <button class="remove-instruction" type="button">Remove</button>
  `;
  return row;
}

function collectInstructions() {
  const instructions = {};
  document.querySelectorAll(".instruction-row").forEach((row) => {
    const template = row.querySelector("[name='template']").value.trim();
    const field = row.querySelector("[name='field']").value.trim();
    const message = row.querySelector("[name='message']").value.trim();
    if (!template || !field) return;
    instructions[template] ||= {};
    instructions[template][field] = message;
  });
  return instructions;
}

document.querySelector("#add-instruction").addEventListener("click", () => {
  editor.appendChild(instructionRow());
});

editor.addEventListener("click", (event) => {
  if (event.target.classList.contains("remove-instruction")) {
    event.target.closest(".instruction-row").remove();
  }
});

document.querySelector("#save-instructions").addEventListener("click", async () => {
  statusBox.textContent = "Saving...";
  const response = await fetch("/api/instructions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ instructions: collectInstructions() }),
  });
  statusBox.textContent = response.ok ? "Saved" : "Save failed";
});
