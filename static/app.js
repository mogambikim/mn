const form = document.querySelector("#barcode-form");
const encodedText = document.querySelector("#encoded-text");
const structuredData = document.querySelector("#structured-data");
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
  for (const [key, value] of data.entries()) {
    if (["module_size", "x", "y", "width", "height_px", "canvas_width", "canvas_height", "rotation"].includes(key)) {
      continue;
    }
    fields[key] = value;
  }
  return {
    template: countyTemplate || "standard",
    fields,
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
  scanStatus.textContent = "Scan test running...";
  scanStatus.className = "scan-status pending";
  const response = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(collectPayload()),
  });
  const body = await response.json();
  if (!response.ok) {
    encodedText.textContent = (body.errors || ["Generation failed."]).join("\n");
    scanStatus.textContent = "Scan test not run";
    scanStatus.className = "scan-status failed";
    return;
  }
  encodedText.textContent = body.encoded_text;
  structuredData.textContent = JSON.stringify(body.structured, null, 2);
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
    const birthDate = form.elements.birth_date.value.trim();
    const expiry = expiryFromInstruction(birthDate, issueDate) || expiryFromIssue(issueDate);
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

  const response = await fetch(`/api/random-field/${fieldName}`);
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
  const instructedExpiry = fieldName === "expiry_date" ? expiryFromInstruction(birth, issue) : "";

  if (countyTemplate === "mombasa") {
    if (fieldName === "license_number") return randomDigits(7);
    if (fieldName === "expiry_date") return instructedExpiry || expiryFromBirthAndIssue(birth, issue, 5);
    if (fieldName === "document_discriminator") return "NONE";
    if (fieldName === "audit_info") return `${license || randomDigits(7)}${randomDigits(5)}${issue.slice(6, 8)}${dayOfYear(issue)}01`;
  }
  if (countyTemplate === "kwale") {
    if (fieldName === "license_number") return `T${randomDigits(12)}`;
    if (fieldName === "expiry_date") return instructedExpiry || expiryFromBirthAndIssue(birth, issue, 4);
    if (fieldName === "audit_info") return `${license || `T${randomDigits(12)}`}01${dayOfYear(issue)}01`;
    if (fieldName === "document_discriminator") return `0000000${randomDigits(7)}`;
  }
  if (countyTemplate === "kilifi") {
    if (fieldName === "license_number") return randomDigits(8);
    if (fieldName === "expiry_date") return instructedExpiry || expiryFromBirthAndIssue(birth, issue, 6);
    if (fieldName === "document_discriminator") return randomDigits(20);
    if (fieldName === "audit_info") return `0000${randomDigits(7)}`;
  }
  if (countyTemplate === "lamu") {
    if (fieldName === "license_number") return randomDigits(7);
    if (fieldName === "expiry_date") return instructedExpiry || expiryFromBirthAndIssue(birth, issue, 8);
    if (fieldName === "document_discriminator") return `${randomDigits(7)} ${randomDigits(3)}${issue.slice(6, 8)}${issue.slice(0, 4)}${randomLetters(3)}-${Math.floor(Math.random() * 2)}`;
    if (fieldName === "audit_info") return randomDigits(10);
  }
  if (countyTemplate === "fl") {
    if (fieldName === "license_number") return `${randomLetters(1)}${randomDigits(12)}`;
    if (fieldName === "expiry_date") return instructedExpiry || expiryFromBirthAndIssue(birth, issue, 5);
    if (fieldName === "document_discriminator") return `N${randomDigits(12)}`;
    if (fieldName === "audit_info") return `0100${randomDigits(12)}`;
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

function expiryInstruction() {
  const template = countyTemplate || "standard";
  return savedInstructions[template]?.expiry_date || savedInstructions.standard?.expiry_date || "";
}

function instructionYears(message) {
  const numberWords = {
    one: 1,
    two: 2,
    three: 3,
    four: 4,
    five: 5,
    six: 6,
    seven: 7,
    eight: 8,
    nine: 9,
    ten: 10,
  };
  const lower = message.toLowerCase();
  const numericMatch = lower.match(/(\d+)\s+years?/);
  if (numericMatch) return Number(numericMatch[1]);
  const wordMatch = lower.match(/\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+years?\b/);
  return wordMatch ? numberWords[wordMatch[1]] : null;
}

function expiryFromInstruction(birthDate, issueDate) {
  const instruction = expiryInstruction().toLowerCase();
  const years = instructionYears(instruction);
  if (!instruction || years === null) return "";

  const birthDigits = birthDate.replace(/\D/g, "");
  const issueDigits = issueDate.replace(/\D/g, "");
  const mentionsBirth = /\bbirth\s*date\b|\bbirthdate\b|\bbirthday\b/.test(instruction);
  const mentionsIssue = /\bissue(d)?\b/.test(instruction);
  const monthDaySource = mentionsBirth && birthDigits.length === 8 ? birthDigits : issueDigits;
  const yearSource = mentionsIssue && issueDigits.length === 8 ? issueDigits : monthDaySource;

  if (monthDaySource.length !== 8 || yearSource.length !== 8) return "";
  const year = Number(yearSource.slice(4, 8)) + years;
  return `${monthDaySource.slice(0, 4)}${year}`;
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
    const expiry = countyConfigs[countyTemplate] ? randomCountyField("expiry_date") : expiryFromInstruction(fields.birth_date, fields.issue_date) || expiryFromIssue(fields.issue_date);
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
    body: JSON.stringify({ fields, template: countyTemplate || "standard" }),
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
  syncDatePickers();
  updateFormPreview();
}

function updateScanStatus(body) {
  const decoded = body.decoded_preview || "";
  if (decoded.startsWith("Decode preview unavailable")) {
    scanStatus.textContent = decoded;
    scanStatus.className = "scan-status pending";
    return;
  }
  if (decoded === body.encoded_text) {
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
  const response = await fetch("/api/random-record");
  const body = await response.json();
  if (!body.ok) return;
  for (const [key, value] of Object.entries(body.fields)) {
    const input = form.elements[key];
    if (input) input.value = value;
  }
  syncDatePickers();
  updateFormPreview();
  updateQualityWarning();
}

document.querySelector("#create").addEventListener("click", createBarcode);
document.querySelector("#fill-random").addEventListener("click", randomRecord);
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

document.querySelector("#decode-upload").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  const output = document.querySelector("#decode-result");
  output.textContent = "Decoding...";
  const data = new FormData();
  data.append("image", file);
  const response = await fetch("/api/decode", { method: "POST", body: data });
  const body = await response.json();
  if (!response.ok) {
    output.textContent = (body.errors || ["Decode failed."]).join("\n");
    return;
  }
  output.textContent = `${body.decoded_text}\n\n${JSON.stringify(body.structured, null, 2)}`;
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
