const editor = document.querySelector("#county-editor");
const statusBox = document.querySelector("#county-save-status");

function countyRow(county = {}) {
  const row = document.createElement("div");
  row.className = "county-edit-row";
  row.innerHTML = `
    <label>Name<input name="name" value="${county.name || ""}"></label>
    <label>Status<input name="status" value="${county.status || ""}" placeholder="ready"></label>
    <label>Badge<input name="badge" value="${county.badge || ""}" placeholder="NEW"></label>
    <label>Template
      <select name="template">
        <option value="">standard</option>
        <option value="mombasa">mombasa</option>
        <option value="kwale">kwale</option>
        <option value="kilifi">kilifi</option>
        <option value="lamu">lamu</option>
      </select>
    </label>
    <button class="duplicate-county" type="button">Copy</button>
    <button class="remove-county" type="button">Remove</button>
  `;
  row.querySelector("[name='template']").value = county.template || "";
  return row;
}

function collectCounties() {
  return [...document.querySelectorAll(".county-edit-row")].map((row) => ({
    name: row.querySelector("[name='name']").value.trim(),
    status: row.querySelector("[name='status']").value.trim(),
    badge: row.querySelector("[name='badge']").value.trim(),
    template: row.querySelector("[name='template']").value.trim(),
  })).filter((county) => county.name);
}

document.querySelector("#add-county").addEventListener("click", () => {
  editor.appendChild(countyRow({ name: "New county" }));
});

editor.addEventListener("click", (event) => {
  if (event.target.classList.contains("duplicate-county")) {
    const row = event.target.closest(".county-edit-row");
    const county = {
      name: `${row.querySelector("[name='name']").value.trim()} Copy`,
      status: row.querySelector("[name='status']").value.trim(),
      badge: row.querySelector("[name='badge']").value.trim(),
      template: row.querySelector("[name='template']").value.trim(),
    };
    row.after(countyRow(county));
  }
  if (event.target.classList.contains("remove-county")) {
    event.target.closest(".county-edit-row").remove();
  }
});

document.querySelector("#save-counties").addEventListener("click", async () => {
  statusBox.textContent = "Saving...";
  const response = await fetch("/api/counties", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ counties: collectCounties() }),
  });
  statusBox.textContent = response.ok ? "Saved" : "Save failed";
});
