const editor = document.querySelector("#template-editor");
const statusBox = document.querySelector("#template-save-status");

function templateRow(name = "new_template", config = {}) {
  const row = document.createElement("div");
  row.className = "template-row";
  row.innerHTML = `
    <label>Template name<input name="name" value="${name}"></label>
    <label>Config JSON<textarea name="config">${JSON.stringify(config, null, 2)}</textarea></label>
    <button class="duplicate-template" type="button">Copy</button>
    <button class="remove-template" type="button">Remove</button>
  `;
  return row;
}

function collectTemplates() {
  const templates = {};
  document.querySelectorAll(".template-row").forEach((row) => {
    const name = row.querySelector("[name='name']").value.trim();
    const raw = row.querySelector("[name='config']").value;
    if (!name) return;
    templates[name] = JSON.parse(raw);
  });
  return templates;
}

document.querySelector("#add-template").addEventListener("click", () => {
  editor.appendChild(templateRow());
});

editor.addEventListener("click", (event) => {
  if (event.target.classList.contains("duplicate-template")) {
    const row = event.target.closest(".template-row");
    const name = `${row.querySelector("[name='name']").value.trim()}_copy`;
    const config = JSON.parse(row.querySelector("[name='config']").value);
    row.after(templateRow(name, config));
  }
  if (event.target.classList.contains("remove-template")) {
    event.target.closest(".template-row").remove();
  }
});

document.querySelector("#save-templates").addEventListener("click", async () => {
  statusBox.textContent = "Saving...";
  try {
    const response = await fetch("/api/templates", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ templates: collectTemplates() }),
    });
    statusBox.textContent = response.ok ? "Saved" : "Save failed";
  } catch (error) {
    statusBox.textContent = `Invalid JSON: ${error.message}`;
  }
});
