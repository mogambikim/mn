const form = document.querySelector("#barcode-form");
const encodedText = document.querySelector("#encoded-text");
const structuredData = document.querySelector("#structured-data");
const xmlOutput = document.querySelector("#xml-output");
const parsedFieldsTable = document.querySelector("#parsed-fields-table");
const decodeFieldsTable = document.querySelector("#decoded-fields-table");
const preview = document.querySelector("#barcode-preview");
const pngLink = document.querySelector("#download-png");
const pdfLink = document.querySelector("#download-pdf");
const code128Preview = document.querySelector("#code128-preview");
const code128PngLink = document.querySelector("#download-code128-png");
const code128PdfLink = document.querySelector("#download-code128-pdf");
const code128Status = document.querySelector("#code128-status");
const infoPopover = document.querySelector("#info-popover");
const formDataPreview = document.querySelector("#form-data");
const qualityWarning = document.querySelector("#quality-warning");
const scanStatus = document.querySelector("#scan-status");
const SETTINGS_KEY = "pdf417BarcodeSettings";
const shell = document.querySelector(".shell");
const countyTemplate = shell?.dataset.template || "";
const savedInstructions = JSON.parse(document.querySelector("#instruction-data")?.textContent || "{}");
const savedTemplates = JSON.parse(document.querySelector("#template-data")?.textContent || "{}");
let calculationTimer;
let lastDecodedFields = null;
let scanPreviewUrl = null;

const countyConfigs = {
  mombasa: {
    visibleExtras: ["weight_range", "is_real_id"],
    hide: ["state", "suffix", "weight"],
    order: [
      "license_number", "last_name", "first_name", "middle_name",
      "address", "city", "zip_code", "license_class", "sex", "donor",
      "birth_date", "issue_date", "expiry_date", "document_discriminator", "audit_info",
      "restrictions", "endorsement", "height", "is_real_id",
      "weight_range", "eye_color", "hair_color",
    ],
    defaults: {
      license_number: "50764683",
      last_name: "Doe",
      first_name: "John",
      address: "3704 3RD PL NE",
      city: "Center Point",
      zip_code: "352151400",
      license_class: "D",
      birth_date: "01151970",
      issue_date: "08262023",
      expiry_date: "08262027",
      document_discriminator: "NONE",
      audit_info: "50764683783372324201",
      is_real_id: "Yes",
    },
    hints: {
      license_number: "7 random digits. You can click the calculator icon to calculate number automatically.",
      expiry_date: "Same month and day as in birth date. 5 years after the year of issue.",
      audit_info: "Document number + 5 random digits + 2 digits of issue year + 3 digits from the beginning of the year to document + 01. You can click the calculator icon to calculate ICN automatically.",
    },
  },
  kwale: {
    visibleExtras: ["address2"],
    hide: ["state", "suffix", "hair_color"],
    order: [
      "license_number", "first_name", "last_name", "middle_name",
      "address", "city", "zip_code", "license_class", "sex", "donor",
      "birth_date", "issue_date", "expiry_date", "audit_info", "document_discriminator",
      "restrictions", "endorsement", "height", "weight", "eye_color", "address2",
    ],
    defaults: {
      license_number: "T403223261033",
      first_name: "John",
      last_name: "Doe",
      address: "4102 Beaver Dam Rd",
      city: "Eagan",
      zip_code: "551222123",
      license_class: "D",
      birth_date: "01151970",
      issue_date: "08262020",
      expiry_date: "01152024",
      audit_info: "T4032232610330124301",
      document_discriminator: "00000006518117",
    },
    hints: {
      license_number: "One letter and 12 numbers. You can click the calculator icon to calculate number automatically.",
      expiry_date: "Same month and day as in birth date. 4 years after the year of issue.",
      audit_info: "Document number + '01' + number of days from the beginning of year to issue date + '01'. You can click the calculator icon to calculate ICN automatically.",
      document_discriminator: "7 zeros + 7 random digits. You can click the calculator icon to calculate DD automatically.",
    },
  },
  kilifi: {
    visibleExtras: ["race"],
    hide: ["state", "address2", "weight_range", "is_real_id"],
    showLoginWarning: true,
    order: [
      "license_number", "first_name", "last_name", "middle_name",
      "address", "city", "zip_code", "license_class", "sex", "donor",
      "birth_date", "issue_date", "expiry_date", "document_discriminator", "audit_info",
      "restrictions", "endorsement", "height", "weight",
      "eye_color", "hair_color", "race", "suffix",
    ],
    defaults: {
      license_number: "24253231",
      first_name: "John",
      last_name: "Doe",
      middle_name: "Daniel",
      address: "609 E Clare St",
      city: "Beeville",
      zip_code: "781024321",
      license_class: "C",
      birth_date: "01151970",
      issue_date: "08262021",
      expiry_date: "01152028",
      document_discriminator: "92334268049701405070",
      audit_info: "10001846127",
    },
    hints: {
      license_number: "8 random digits. You can click the calculator icon to calculate number automatically.",
      expiry_date: "Same month and day as in birth date. 6 years after the issue year.",
      document_discriminator: "20 digits with custom algorithm. Please click the calculator icon to calculate DD automatically.",
      audit_info: "'0000' + 7 random digits. You can click the calculator icon to calculate ICN automatically.",
    },
  },
  lamu: {
    visibleExtras: ["is_real_id"],
    hide: ["state", "suffix", "weight_range", "address2", "race"],
    order: [
      "license_number", "last_name", "first_name", "middle_name",
      "address", "city", "zip_code", "license_class", "sex", "donor",
      "birth_date", "issue_date", "expiry_date",
      "audit_info", "document_discriminator", "restrictions",
      "endorsement", "height", "weight",
      "eye_color", "hair_color", "is_real_id",
    ],
    defaults: {
      license_number: "7476172",
      last_name: "Doe",
      first_name: "John",
      address: "3201 Legacy Dr",
      city: "Anchorage",
      zip_code: "995162765",
      license_class: "D",
      birth_date: "01151970",
      issue_date: "08262020",
      expiry_date: "01152028",
      audit_info: "1000728920",
      document_discriminator: "8475992 460200826PNV-1",
      restrictions: "NONE",
      endorsement: "NONE",
      height: "69",
      weight: "169",
      is_real_id: "Yes",
    },
    hints: {},
  },
};

for (const [templateName, config] of Object.entries(savedTemplates)) {
  countyConfigs[templateName] = {
    ...(countyConfigs[templateName] || {}),
    ...config,
    defaults: {
      ...((countyConfigs[templateName] || {}).defaults || {}),
      ...(config.defaults || {}),
    },
  };
}

function collectPayload() {
  const data = new FormData(form);
  const fields = {};
  const profileConfig = countyConfigs[countyTemplate];
  const activeFields = profileConfig?.activeFields
    ? new Set(profileConfig.activeFields)
    : null;
  for (const [key, value] of data.entries()) {
    if (["module_size", "x", "y", "width", "height_px", "canvas_width", "canvas_height", "rotation"].includes(key)) {
      continue;
    }
    if (activeFields && !activeFields.has(key)) continue;
    fields[key] = value;
  }
  return {
    fields,
    profile: profileConfig?.jurisdictionProfile ? countyTemplate : "",
    xml_schema: (() => {
      try {
        return JSON.parse(document.querySelector("#xml-schema").value);
      } catch {
        throw new Error("XML schema must be valid JSON.");
      }
    })(),
    record_source: document.querySelector("#record-source").value,
    settings: {
      module_size: data.get("module_size"),
      x: data.get("x"),
      y: data.get("y"),
      width: data.get("width"),
      height: data.get("height_px"),
      canvas_width: data.get("canvas_width"),
      canvas_height: data.get("canvas_height"),
      rotation: data.get("rotation") || "none",
    },
  };
}

function collectFields() {
  return collectPayload().fields;
}

function setDownloads(pngUrl, pdfUrl) {
  pngLink.href = pngUrl;
  pdfLink.href = pdfUrl;
  pngLink.classList.remove("disabled");
  pdfLink.classList.remove("disabled");
}

function setCode128Downloads(body) {
  if (body.code128_error) {
    code128Status.textContent = body.code128_error;
    code128Status.className = "scan-status failed";
    code128Preview.removeAttribute("src");
    code128PngLink.classList.add("disabled");
    code128PdfLink.classList.add("disabled");
    return;
  }
  code128Status.textContent = `Encoded ICN: ${body.code128_text}`;
  code128Status.className = "scan-status passed";
  code128Preview.src = `${body.code128_png_url}?t=${Date.now()}`;
  code128PngLink.href = body.code128_png_url;
  code128PdfLink.href = body.code128_pdf_url;
  code128PngLink.classList.remove("disabled");
  code128PdfLink.classList.remove("disabled");
}

async function createBarcode() {
  await calculateDerivedFields(false);
  updateFormPreview();
  updateQualityWarning();
  encodedText.textContent = "Generating...";
  structuredData.textContent = "";
  xmlOutput.textContent = "";
  parsedFieldsTable.replaceChildren();
  scanStatus.textContent = "Scan test running...";
  scanStatus.className = "scan-status pending";
  let response;
  try {
    response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectPayload()),
    });
  } catch (error) {
    encodedText.textContent = `Generation failed: ${error.message}`;
    scanStatus.textContent = "Generation failed";
    scanStatus.className = "scan-status failed";
    return;
  }
  const body = await response.json();
  if (!response.ok) {
    encodedText.textContent = (body.errors || ["Generation failed."]).join("\n");
    scanStatus.textContent = "Scan test not run";
    scanStatus.className = "scan-status failed";
    return;
  }
  encodedText.textContent = body.encoded_text;
  structuredData.textContent = JSON.stringify(body.structured, null, 2);
  renderFieldsTable(parsedFieldsTable, body.structured);
  xmlOutput.textContent = body.xml;
  preview.src = `${body.png_url}?t=${Date.now()}`;
  setDownloads(body.png_url, body.pdf_url);
  setCode128Downloads(body);
  updateScanStatus(body);
}

async function randomField(fieldName) {
  if (countyTemplate && countyConfigs[countyTemplate]) {
    const countyValue = randomCountyField(fieldName);
    if (countyValue !== null) {
      form.elements[fieldName].value = countyValue;
      updateFormPreview();
      return;
    }
  }

  if (fieldName === "expiry_date") {
    const issueDate = form.elements.issue_date.value.trim();
    const expiry = expiryFromIssue(issueDate);
    if (expiry) {
      form.elements.expiry_date.value = expiry;
      syncDatePickers();
      scheduleDerivedCalculation();
      return;
    }
  }

  if (fieldName === "document_discriminator" || fieldName === "audit_info") {
    await calculateDerivedFields(false);
    return;
  }

  const profileQuery = countyConfigs[countyTemplate]?.jurisdictionProfile
    ? `?profile=${encodeURIComponent(countyTemplate)}`
    : "";
  const response = await fetch(`/api/random-field/${fieldName}${profileQuery}`);
  const body = await response.json();
  if (body.ok) {
    const input = form.elements[fieldName];
    if (input) input.value = body.value;
    if (["issue_date", "birth_date", "expiry_date"].includes(fieldName)) {
      syncDatePickers();
    }
    if (fieldName === "issue_date") {
      scheduleDerivedCalculation(true);
    }
    if (fieldName === "expiry_date" || fieldName === "license_number") {
      scheduleDerivedCalculation(false);
    }
    updateFormPreview();
  }
}

function randomDigits(length) {
  let value = "";
  for (let i = 0; i < length; i += 1) value += Math.floor(Math.random() * 10);
  return value;
}

function dayOfYear(mmddyyyy) {
  const digits = mmddyyyy.replace(/\D/g, "");
  if (digits.length !== 8) return "001";
  const date = new Date(Number(digits.slice(4)), Number(digits.slice(0, 2)) - 1, Number(digits.slice(2, 4)));
  const start = new Date(date.getFullYear(), 0, 0);
  return String(Math.floor((date - start) / 86400000)).padStart(3, "0");
}

function randomCountyField(fieldName) {
  const issue = form.elements.issue_date.value || "";
  const expiry = form.elements.expiry_date.value || "";
  const birth = form.elements.birth_date.value || "";
  const license = form.elements.license_number.value || "";

  if (countyTemplate === "mombasa") {
    if (fieldName === "license_number") return randomDigits(7);
    if (fieldName === "expiry_date") return expiryFromBirthAndIssue(birth, issue, 5);
    if (fieldName === "document_discriminator") return "NONE";
    if (fieldName === "audit_info") return `${license || randomDigits(7)}${randomDigits(5)}${issue.slice(6, 8)}${dayOfYear(issue)}01`;
  }
  if (countyTemplate === "kwale") {
    if (fieldName === "license_number") return `T${randomDigits(12)}`;
    if (fieldName === "expiry_date") return expiryFromBirthAndIssue(birth, issue, 4);
    if (fieldName === "audit_info") return `${license || `T${randomDigits(12)}`}01${dayOfYear(issue)}01`;
    if (fieldName === "document_discriminator") return `0000000${randomDigits(7)}`;
  }
  if (countyTemplate === "kilifi") {
    if (fieldName === "license_number") return randomDigits(8);
    if (fieldName === "expiry_date") return expiryFromBirthAndIssue(birth, issue, 6);
    if (fieldName === "document_discriminator") return randomDigits(20);
    if (fieldName === "audit_info") return `0000${randomDigits(7)}`;
  }
  if (countyTemplate === "lamu") {
    if (fieldName === "license_number") return randomDigits(7);
    if (fieldName === "expiry_date") return expiryFromBirthAndIssue(birth, issue, 8);
    if (fieldName === "document_discriminator") return `${randomDigits(7)} ${randomDigits(3)}${issue.slice(6, 8)}${issue.slice(0, 4)}${randomLetters(3)}-${Math.floor(Math.random() * 2)}`;
    if (fieldName === "audit_info") return randomDigits(10);
  }
  return null;
}

function randomLetters(length) {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  let value = "";
  for (let i = 0; i < length; i += 1) value += alphabet[Math.floor(Math.random() * alphabet.length)];
  return value;
}

function expiryFromBirthAndIssue(birthDate, issueDate, yearsAfterIssue) {
  const birthDigits = birthDate.replace(/\D/g, "");
  const issueDigits = issueDate.replace(/\D/g, "");
  if (birthDigits.length !== 8 || issueDigits.length !== 8) return "";
  const year = Number(issueDigits.slice(4, 8)) + yearsAfterIssue;
  return `${birthDigits.slice(0, 4)}${year}`;
}

function expiryFromIssue(issueDate) {
  const digits = issueDate.replace(/\D/g, "");
  if (digits.length !== 8) return "";
  const month = digits.slice(0, 2);
  const day = digits.slice(2, 4);
  const year = Number(digits.slice(4, 8)) + 5;
  return `${month}${day}${year}`;
}

function mmddyyyyToIso(value) {
  const digits = value.replace(/\D/g, "");
  if (digits.length !== 8) return "";
  return `${digits.slice(4, 8)}-${digits.slice(0, 2)}-${digits.slice(2, 4)}`;
}

function isoToMmddyyyy(value) {
  if (!value) return "";
  const [year, month, day] = value.split("-");
  if (!year || !month || !day) return "";
  return `${month}${day}${year}`;
}

function syncDatePickers() {
  document.querySelectorAll(".date-picker").forEach((picker) => {
    const target = form.elements[picker.dataset.dateTarget];
    if (target) picker.value = mmddyyyyToIso(target.value);
  });
}

async function calculateDerivedFields(overwriteExpiry = true) {
  const fields = collectFields();
  if (!fields.issue_date) return;
  if (overwriteExpiry || !fields.expiry_date) {
    const expiry = countyConfigs[countyTemplate] ? randomCountyField("expiry_date") : expiryFromIssue(fields.issue_date);
    if (expiry) {
      form.elements.expiry_date.value = expiry;
      fields.expiry_date = expiry;
    }
  }
  if (countyConfigs[countyTemplate]) {
    syncDatePickers();
    updateFormPreview();
    return;
  }

  const response = await fetch("/api/calculate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fields }),
  });
  const body = await response.json();
  if (!body.ok) return;
  for (const [key, value] of Object.entries(body.fields)) {
    if (value && form.elements[key]) form.elements[key].value = value;
  }
  syncDatePickers();
  updateFormPreview();
}

function scheduleDerivedCalculation(overwriteExpiry = true) {
  clearTimeout(calculationTimer);
  calculationTimer = setTimeout(() => calculateDerivedFields(overwriteExpiry), 180);
}

function updateFormPreview() {
  formDataPreview.textContent = JSON.stringify(collectFields(), null, 2);
}

function applyCountyTemplate() {
  const config = countyConfigs[countyTemplate];
  if (!config) return;
  document.querySelector("#login-warning").hidden = !config.showLoginWarning;
  document.querySelector("#synthetic-profile-warning").hidden = !config.jurisdictionProfile;

  document.querySelectorAll("[data-field]").forEach((field) => {
    const name = field.dataset.field;
    field.hidden = config.hide?.includes(name) || false;
    if (config.visibleExtras?.includes(name)) field.hidden = false;
    const order = config.order.indexOf(name);
    if (order >= 0) field.style.order = order;
  });

  for (const [fieldName, value] of Object.entries(config.defaults || {})) {
    if (form.elements[fieldName]) form.elements[fieldName].value = value;
  }
  const instructions = {
    ...(savedInstructions.standard || {}),
    ...(config.hints || {}),
    ...(savedInstructions[countyTemplate] || {}),
  };
  for (const [fieldName, message] of Object.entries(instructions)) {
    const wrapper = document.querySelector(`[data-field="${fieldName}"]`);
    const hint = wrapper?.querySelector(".hint");
    if (hint) hint.dataset.info = message;
  }
  for (const [fieldName, labelText] of Object.entries(config.labels || {})) {
    const label = document.querySelector(`label[for="${fieldName}"]`);
    if (label?.firstChild) label.firstChild.textContent = `${labelText} `;
  }
  syncDatePickers();
  updateFormPreview();
  if (config.jurisdictionProfile) randomRecord();
}

function updateScanStatus(body) {
  const decoded = body.decoded_preview || "";
  if (decoded.startsWith("Decode preview unavailable")) {
    scanStatus.textContent = decoded;
    scanStatus.className = "scan-status pending";
    return;
  }
  if (body.round_trip?.payload_preserved) {
    scanStatus.textContent = "Scan test passed";
    scanStatus.className = "scan-status passed";
    return;
  }
  scanStatus.textContent = "Scan test needs review";
  scanStatus.className = "scan-status failed";
}

function updateQualityWarning() {
  const data = new FormData(form);
  const width = Number(data.get("width"));
  const height = Number(data.get("height_px"));
  const moduleSize = Number(data.get("module_size"));
  const warnings = [];
  if (width && width < 900) warnings.push("Barcode width is low for dense PDF417 data.");
  if (height && height < 240) warnings.push("Barcode height is low and may reduce scan reliability.");
  if (moduleSize && moduleSize < 2) warnings.push("Module size below 2 can reduce sharpness.");
  if (width && height) {
    const ratio = width / height;
    if (ratio < 3 || ratio > 6) warnings.push("Width/height ratio is outside the usual PDF417 range.");
  }
  qualityWarning.textContent = warnings.join(" ");
  qualityWarning.hidden = warnings.length === 0;
}

function saveSettings() {
  const data = new FormData(form);
  const settings = {};
  ["module_size", "x", "y", "width", "height_px", "canvas_width", "canvas_height", "rotation"].forEach((key) => {
    settings[key] = data.get(key);
  });
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
}

function loadSettings() {
  const raw = localStorage.getItem(SETTINGS_KEY);
  if (!raw) return;
  const settings = JSON.parse(raw);
  for (const [key, value] of Object.entries(settings)) {
    if (form.elements[key]) form.elements[key].value = value;
  }
  updateQualityWarning();
}

function showInfo(button) {
  const message = button.dataset.info;
  if (!message) return;
  const rect = button.getBoundingClientRect();
  infoPopover.textContent = message;
  infoPopover.hidden = false;

  const popoverWidth = infoPopover.offsetWidth;
  const left = Math.min(
    window.innerWidth - popoverWidth - 12,
    Math.max(12, rect.left + rect.width / 2 - popoverWidth / 2)
  );
  infoPopover.style.left = `${left}px`;
  infoPopover.style.top = `${rect.bottom + window.scrollY + 8}px`;
}

function hideInfo(event) {
  if (event.target.closest(".hint") || event.target.closest("#info-popover")) return;
  infoPopover.hidden = true;
}

async function randomRecord() {
  const profileQuery = countyConfigs[countyTemplate]?.jurisdictionProfile
    ? `?profile=${encodeURIComponent(countyTemplate)}`
    : "";
  const response = await fetch(`/api/random-record${profileQuery}`);
  const body = await response.json();
  if (!body.ok) return;
  document.querySelector("#record-source").value = "test";
  for (const [key, value] of Object.entries(body.fields)) {
    const input = form.elements[key];
    if (input) input.value = value;
  }
  const profileConfig = countyConfigs[countyTemplate];
  for (const [key, value] of Object.entries(profileConfig?.defaults || {})) {
    if (form.elements[key]) form.elements[key].value = value;
  }
  syncDatePickers();
  updateFormPreview();
  updateQualityWarning();
}

document.querySelector("#create").addEventListener("click", createBarcode);
document.querySelector("#fill-random").addEventListener("click", randomRecord);
document.querySelector("#profile-picker").addEventListener("change", (event) => {
  const selected = event.target.value;
  if (selected === "/studio") {
    window.location.href = selected;
    return;
  }
  window.location.href = `/studio?county=${selected}`;
});
document.querySelector("#copy-xml").addEventListener("click", async () => {
  const value = xmlOutput.textContent;
  if (!value) return;
  await navigator.clipboard.writeText(value);
});
document.querySelector("#save-settings").addEventListener("click", saveSettings);
document.querySelector("#load-settings").addEventListener("click", loadSettings);
document.querySelectorAll("[data-random]").forEach((button) => {
  button.addEventListener("click", () => randomField(button.dataset.random));
});
document.querySelectorAll(".date-picker").forEach((picker) => {
  picker.addEventListener("change", () => {
    const target = form.elements[picker.dataset.dateTarget];
    if (target) target.value = isoToMmddyyyy(picker.value);
    if (picker.dataset.dateTarget === "issue_date") scheduleDerivedCalculation(true);
    if (picker.dataset.dateTarget === "expiry_date") scheduleDerivedCalculation(false);
    updateFormPreview();
  });
});
form.elements.license_number.addEventListener("input", () => {
  scheduleDerivedCalculation(false);
});
form.elements.issue_date.addEventListener("input", () => {
  syncDatePickers();
  scheduleDerivedCalculation(true);
});
form.elements.expiry_date.addEventListener("input", () => {
  syncDatePickers();
  scheduleDerivedCalculation(false);
});
["module_size", "width", "height_px"].forEach((name) => {
  form.elements[name].addEventListener("input", updateQualityWarning);
});
form.addEventListener("input", updateFormPreview);
document.querySelectorAll(".hint").forEach((button) => {
  button.addEventListener("click", (event) => {
    event.stopPropagation();
    showInfo(button);
  });
});
document.addEventListener("click", hideInfo);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") infoPopover.hidden = true;
});

function renderFieldsTable(container, fields) {
  container.replaceChildren();
  if (!fields || typeof fields !== "object") return;
  const table = document.createElement("table");
  const body = document.createElement("tbody");
  for (const [field, value] of Object.entries(fields)) {
    const row = document.createElement("tr");
    const name = document.createElement("th");
    const content = document.createElement("td");
    name.textContent = field;
    content.textContent = value;
    row.append(name, content);
    body.append(row);
  }
  table.append(body);
  container.append(table);
}

function loadDecodedRecord() {
  if (!lastDecodedFields) return;
  document.querySelectorAll("#barcode-form option[data-scanned-value='true']").forEach((option) => option.remove());
  const fieldNames = [
    "license_number", "first_name", "middle_name", "last_name", "address", "city",
    "state", "zip_code", "license_class", "sex", "donor", "birth_date", "issue_date",
    "expiry_date", "document_discriminator", "inventory_control_number", "compliance_type",
    "card_revision_date", "audit_info", "restrictions", "endorsement", "height", "weight",
    "suffix", "eye_color", "hair_color", "country",
  ];
  const unavailableFields = [];
  const preservedSelectValues = [];
  const activeFields = countyConfigs[countyTemplate]?.activeFields;
  for (const key of fieldNames) {
    if (form.elements[key]) form.elements[key].value = "";
  }
  for (const [key, value] of Object.entries(lastDecodedFields)) {
    const formKey = key === "organ_donor" ? "donor" : key;
    const input = form.elements[formKey];
    if (!input || value === "") continue;
    if (activeFields && !activeFields.includes(formKey)) {
      unavailableFields.push(formKey);
      continue;
    }
    if (input instanceof HTMLSelectElement && !Array.from(input.options).some((option) => option.value === value)) {
      const option = new Option(`${value} (from scan)`, value);
      option.dataset.scannedValue = "true";
      input.add(option);
      preservedSelectValues.push(formKey);
    }
    input.value = ["birth_date", "issue_date", "expiry_date", "card_revision_date"].includes(formKey)
      ? value.replace(/^(\d{4})-(\d{2})-(\d{2})$/, "$2$3$1")
      : value;
  }
  document.querySelector("#record-source").value = "external";
  const status = document.querySelector("#decode-status");
  const notes = [];
  if (preservedSelectValues.length) {
    notes.push(`Non-standard scanned values were preserved in their fields: ${preservedSelectValues.join(", ")}.`);
  }
  if (unavailableFields.length) {
    notes.push(`Not shown by the selected profile: ${unavailableFields.join(", ")}. Original values remain in the decoded field table.`);
  }
  if (notes.length) status.textContent += ` ${notes.join(" ")}`;
  syncDatePickers();
  updateFormPreview();
}

function clearRecordFields() {
  document.querySelectorAll("#barcode-form option[data-scanned-value='true']").forEach((option) => option.remove());
  document.querySelectorAll("#barcode-form .field input, #barcode-form .field select").forEach((input) => {
    input.value = "";
  });
  document.querySelector("#record-source").value = "external";
  lastDecodedFields = null;
  document.querySelector("#load-decoded-record").disabled = true;
  syncDatePickers();
  updateFormPreview();
}

function setInputMode(mode) {
  const scanning = mode === "scan";
  document.querySelector("#scan-panel").hidden = !scanning;
  document.querySelector("#manual-entry-mode").classList.toggle("selected", !scanning);
  document.querySelector("#scan-existing-mode").classList.toggle("selected", scanning);
  if (scanning) document.querySelector("#decode-upload").focus();
}

function xmlSchema() {
  try {
    return JSON.parse(document.querySelector("#xml-schema").value);
  } catch {
    throw new Error("XML schema must be valid JSON.");
  }
}

async function showDecodedPayload(text, label) {
  const status = document.querySelector("#decode-status");
  const output = document.querySelector("#decode-result");
  lastDecodedFields = null;
  document.querySelector("#load-decoded-record").disabled = true;
  output.textContent = `${label}\n${text}`;
  document.querySelector("#scanner-input").value = text;
  document.querySelector("#record-source").value = "external";
  status.textContent = "Barcode/payload decoded; validating AAMVA format...";
  status.className = "scan-status pending";
  try {
    const response = await fetch("/api/parse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ payload: text, xml_schema: xmlSchema() }),
    });
    const body = await response.json();
    if (!response.ok) {
      status.textContent = `Generic payload only: ${(body.errors || ["AAMVA validation failed."]).join(" ")}`;
      status.className = "scan-status failed";
      decodeFieldsTable.replaceChildren();
      xmlOutput.textContent = "";
      return;
    }
    const report = body.aamva_record;
    lastDecodedFields = report.fields;
    document.querySelector("#load-decoded-record").disabled = false;
    const selectedProfile = countyConfigs[countyTemplate]?.profileName;
    status.textContent = report.aamva_valid
      ? `AAMVA v${report.version} structure and required fields validated. Issuer is not verified.`
      : `AAMVA v${report.version} structure decoded; ${report.validation_errors.join(" ")}`;
    status.textContent += selectedProfile
      ? ` Selected UI profile: ${selectedProfile}; this does not verify the issuer.`
      : " No jurisdiction profile was inferred; select one above if needed.";
    if (Object.keys(report.unsupported_fields || {}).length) {
      status.textContent += ` Unmapped field IDs preserved: ${Object.keys(report.unsupported_fields).join(", ")}.`;
    }
    status.className = report.aamva_valid ? "scan-status passed" : "scan-status failed";
    renderFieldsTable(decodeFieldsTable, report.raw_fields);
    xmlOutput.textContent = body.xml;
  } catch (error) {
    status.textContent = error.message;
    status.className = "scan-status failed";
  }
}

document.querySelector("#load-decoded-record").addEventListener("click", loadDecodedRecord);
document.querySelector("#clear-fields").addEventListener("click", clearRecordFields);
document.querySelector("#manual-entry-mode").addEventListener("click", () => setInputMode("manual"));
document.querySelector("#scan-existing-mode").addEventListener("click", () => setInputMode("scan"));
document.querySelector("#scanner-input").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
    event.preventDefault();
    document.querySelector("#parse-payload").click();
  }
});

document.querySelector("#decode-upload").addEventListener("change", (event) => {
  const file = event.target.files[0];
  const image = document.querySelector("#scan-image-preview");
  const empty = document.querySelector("#scan-preview-empty");
  const status = document.querySelector("#decode-status");
  const scanButton = document.querySelector("#scan-barcode");
  scanButton.disabled = !file;
  if (!file) return;
  if (scanPreviewUrl) URL.revokeObjectURL(scanPreviewUrl);
  scanPreviewUrl = URL.createObjectURL(file);
  image.src = scanPreviewUrl;
  image.hidden = false;
  empty.hidden = true;
  status.textContent = `${file.name} ready to scan. Check the preview, then select Scan Barcode.`;
  status.className = "scan-status pending";
});

document.querySelector("#scan-barcode").addEventListener("click", async () => {
  const file = document.querySelector("#decode-upload").files[0];
  if (!file) return;
  const output = document.querySelector("#decode-result");
  const status = document.querySelector("#decode-status");
  output.textContent = "Scanning image...";
  status.textContent = `Decoding PDF417 from ${file.name}...`;
  status.className = "scan-status pending";
  const data = new FormData();
  data.append("image", file);
  try {
    const response = await fetch("/api/decode", { method: "POST", body: data });
    const body = await response.json();
    if (!response.ok) {
      status.textContent = (body.errors || ["Decode failed."]).join("\n");
      status.className = "scan-status failed";
      output.textContent = "";
      decodeFieldsTable.replaceChildren();
      xmlOutput.textContent = "";
      lastDecodedFields = null;
      document.querySelector("#load-decoded-record").disabled = true;
      return;
    }
    await showDecodedPayload(body.decoded_text, "Decoded image payload");
  } catch (error) {
    status.textContent = `Decode failed: ${error.message}`;
    status.className = "scan-status failed";
  }
});

document.querySelector("#parse-payload").addEventListener("click", () => {
  const text = document.querySelector("#scanner-input").value;
  if (text) showDecodedPayload(text, "Scanner / pasted input");
  else {
    const status = document.querySelector("#decode-status");
    status.textContent = "Enter or scan a raw payload first.";
    status.className = "scan-status failed";
  }
});

loadSettings();
if (countyTemplate && countyConfigs[countyTemplate]) {
  applyCountyTemplate();
} else {
  const instructions = savedInstructions.standard || {};
  for (const [fieldName, message] of Object.entries(instructions)) {
    const wrapper = document.querySelector(`[data-field="${fieldName}"]`);
    const hint = wrapper?.querySelector(".hint");
    if (hint) hint.dataset.info = message;
  }
  randomRecord();
}
