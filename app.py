from __future__ import annotations

import io
import json
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

from barcode_studio.aamva import fill_template, parse_aamva, validate_fields
from barcode_studio.barcode import BarcodeSettings, decode_pdf417, render_code128, render_pdf417
from barcode_studio.calculations import (
    calculate_dd,
    calculate_icn,
    document_number_from_license,
    expiry_from_instruction,
    expiry_from_issue,
)
from barcode_studio.random_data import random_field, random_record


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "/tmp/barcode_outputs" if os.environ.get("VERCEL") else BASE_DIR / "outputs"))
COUNTIES_PATH = BASE_DIR / "counties.json"
INSTRUCTIONS_PATH = BASE_DIR / "instructions.json"
TEMPLATES_PATH = BASE_DIR / "templates.json"
OUTPUT_DIR.mkdir(exist_ok=True)

app = Flask(__name__)

DEFAULT_COUNTIES = [
    {"name": "Mombasa", "status": "ready", "template": "mombasa"},
    {"name": "Kwale", "template": "kwale"},
    {"name": "Kilifi", "status": "ready", "template": "kilifi"},
    {"name": "Florida", "status": "ready", "badge": "NEW", "template": "fl"},
    {"name": "Tana River"},
    {"name": "Lamu", "badge": "NEW", "template": "lamu"},
    {"name": "Taita Taveta"},
    {"name": "Garissa", "status": "ready"},
    {"name": "Wajir"},
    {"name": "Mandera"},
    {"name": "Marsabit", "status": "ready"},
    {"name": "Isiolo"},
    {"name": "Meru"},
    {"name": "Tharaka Nithi", "status": "ready"},
    {"name": "Embu"},
    {"name": "Kitui"},
    {"name": "Machakos", "status": "ready"},
    {"name": "Makueni"},
    {"name": "Nyandarua"},
    {"name": "Nyeri", "status": "ready"},
    {"name": "Kirinyaga"},
    {"name": "Muranga", "status": "ready"},
    {"name": "Kiambu"},
    {"name": "Turkana"},
    {"name": "West Pokot"},
    {"name": "Samburu", "status": "ready"},
    {"name": "Trans Nzoia"},
    {"name": "Uasin Gishu", "badge": "NEW"},
    {"name": "Elgeyo Marakwet"},
    {"name": "Nandi", "status": "ready"},
    {"name": "Baringo"},
    {"name": "Laikipia"},
    {"name": "Nakuru", "status": "ready"},
    {"name": "Narok"},
    {"name": "Kajiado"},
    {"name": "Kericho", "status": "ready"},
    {"name": "Bomet"},
    {"name": "Kakamega"},
    {"name": "Vihiga", "status": "ready"},
    {"name": "Bungoma"},
    {"name": "Busia"},
    {"name": "Siaya", "status": "ready"},
    {"name": "Kisumu"},
    {"name": "Homa Bay"},
    {"name": "Migori", "status": "ready"},
    {"name": "Kisii"},
    {"name": "Nyamira"},
    {"name": "Nairobi", "status": "ready", "badge": "NEW"},
]

DEFAULT_INSTRUCTIONS = {
    "standard": {
        "license_number": "Random letter + 7 random digits. You can click the calculator icon to calculate the number automatically.",
        "middle_name": "Middle name is optional. You can leave it blank, or click the calculator to generate a random middle name.",
        "birth_date": "Enter the date in month, day, year format: MMDDYYYY. Example: 01151970.",
        "issue_date": "Public issue period is from October 20, 2025 until today. Click the calculator to generate a valid issue date in MMDDYYYY format.",
        "expiry_date": "Enter expiry date in month, day, year format: MMDDYYYY. The calculator uses the birth date and adds five years.",
        "document_discriminator": "First 8 digits are the issue date in DD/MM/YYYY format. The last 2 digits are the expiry year. You can click the calculator icon to calculate DD automatically.",
        "audit_info": "First 2 digits are issue year. Next 3 digits are the day number in that year. Next numbers are document number plus 0401. Click the calculator icon to calculate ICN automatically.",
        "suffix": "Name suffix is optional. Use NONE when there is no suffix.",
        "is_real_id": "Select whether this record is marked as REAL ID.",
    },
    "mombasa": {
        "license_number": "7 random digits. You can click the calculator icon to calculate number automatically.",
        "expiry_date": "Same month and day as in birth date. 5 years after the year of issue.",
        "audit_info": "Document number + 5 random digits + 2 digits of issue year + 3 digits from the beginning of the year to document + 01. You can click the calculator icon to calculate ICN automatically.",
    },
    "kwale": {
        "license_number": "One letter and 12 numbers. You can click the calculator icon to calculate number automatically.",
        "expiry_date": "Same month and day as in birth date. 4 years after the year of issue.",
        "audit_info": "Document number + '01' + number of days from the beginning of year to issue date + '01'. You can click the calculator icon to calculate ICN automatically.",
        "document_discriminator": "7 zeros + 7 random digits. You can click the calculator icon to calculate DD automatically.",
    },
    "kilifi": {
        "license_number": "8 random digits. You can click the calculator icon to calculate number automatically.",
        "expiry_date": "Same month and day as in birth date. 6 years after the issue year.",
        "document_discriminator": "20 digits with custom algorithm. Please click the calculator icon to calculate DD automatically.",
        "audit_info": "'0000' + 7 random digits. You can click the calculator icon to calculate ICN automatically.",
    },
    "lamu": {
        "license_number": "You can click on the calculator icon to calculate number automatically.",
        "document_discriminator": "7 digits + whitespace + 3 digits + issue date (YYMMDD) + 3 letters + -1 or -0. You can click on the calculator icon to calculate DD automatically.",
        "audit_info": "10 digits. You can click on the calculator icon to calculate ICN automatically.",
        "expiry_date": "As of January 2019, 8 years, expires on birthday in 7th or 8th year; previously issued cards, 5 years.",
        "is_real_id": "Select whether this record is marked as REAL ID.",
    },
    "fl": {
        "license_number": "Random letter + 12 random digits. You can click on the calculator icon to calculate number automatically.",
        "expiry_date": "Same month and day as in birth date. 5 years after the year of issue.",
        "document_discriminator": "You can click on the calculator icon to calculate DD automatically.",
        "audit_info": "0100 + 12 random digits. You can click on the calculator icon to calculate ICN automatically.",
        "safe_driver": "Select whether this record is marked as Safe Driver.",
    },
}

DEFAULT_TEMPLATES = {
    "mombasa": {
        "visibleExtras": ["weight_range", "is_real_id"],
        "hide": ["state", "suffix", "weight"],
        "order": [
            "license_number", "last_name", "first_name", "middle_name",
            "address", "city", "zip_code", "license_class", "sex", "donor",
            "birth_date", "issue_date", "expiry_date", "document_discriminator", "audit_info",
            "restrictions", "endorsement", "height", "is_real_id",
            "weight_range", "eye_color", "hair_color",
        ],
        "defaults": {
            "license_number": "50764683",
            "last_name": "Doe",
            "first_name": "John",
            "address": "3704 3RD PL NE",
            "city": "Center Point",
            "zip_code": "352151400",
            "license_class": "D",
            "birth_date": "01151970",
            "issue_date": "08262023",
            "expiry_date": "08262027",
            "document_discriminator": "NONE",
            "audit_info": "50764683783372324201",
            "is_real_id": "Yes",
        },
    },
    "kwale": {
        "visibleExtras": ["address2"],
        "hide": ["state", "suffix", "hair_color"],
        "order": [
            "license_number", "first_name", "last_name", "middle_name",
            "address", "city", "zip_code", "license_class", "sex", "donor",
            "birth_date", "issue_date", "expiry_date", "audit_info", "document_discriminator",
            "restrictions", "endorsement", "height", "weight", "eye_color", "address2",
        ],
        "defaults": {
            "license_number": "T403223261033",
            "first_name": "John",
            "last_name": "Doe",
            "address": "4102 Beaver Dam Rd",
            "city": "Eagan",
            "zip_code": "551222123",
            "license_class": "D",
            "birth_date": "01151970",
            "issue_date": "08262020",
            "expiry_date": "01152024",
            "audit_info": "T4032232610330124301",
            "document_discriminator": "00000006518117",
        },
    },
    "kilifi": {
        "visibleExtras": ["race"],
        "hide": ["state", "address2", "weight_range", "is_real_id"],
        "showLoginWarning": True,
        "order": [
            "license_number", "first_name", "last_name", "middle_name",
            "address", "city", "zip_code", "license_class", "sex", "donor",
            "birth_date", "issue_date", "expiry_date", "document_discriminator", "audit_info",
            "restrictions", "endorsement", "height", "weight",
            "eye_color", "hair_color", "race", "suffix",
        ],
        "defaults": {
            "license_number": "24253231",
            "first_name": "John",
            "last_name": "Doe",
            "middle_name": "Daniel",
            "address": "609 E Clare St",
            "city": "Beeville",
            "zip_code": "781024321",
            "license_class": "C",
            "birth_date": "01151970",
            "issue_date": "08262021",
            "expiry_date": "01152028",
            "document_discriminator": "92334268049701405070",
            "audit_info": "10001846127",
        },
    },
    "lamu": {
        "visibleExtras": ["is_real_id"],
        "hide": ["state", "suffix", "weight_range", "address2", "race"],
        "order": [
            "license_number", "last_name", "first_name", "middle_name",
            "address", "city", "zip_code", "license_class", "sex", "donor",
            "birth_date", "issue_date", "expiry_date",
            "audit_info", "document_discriminator", "restrictions",
            "endorsement", "height", "weight",
            "eye_color", "hair_color", "is_real_id",
        ],
        "defaults": {
            "license_number": "7476172",
            "last_name": "Doe",
            "first_name": "John",
            "address": "3201 Legacy Dr",
            "city": "Anchorage",
            "zip_code": "995162765",
            "license_class": "D",
            "birth_date": "01151970",
            "issue_date": "08262020",
            "expiry_date": "01152028",
            "audit_info": "1000728920",
            "document_discriminator": "8475992 460200826PNV-1",
            "restrictions": "NONE",
            "endorsement": "NONE",
            "height": "69",
            "weight": "169",
            "is_real_id": "Yes",
        },
    },
    "fl": {
        "visibleExtras": ["revision_date", "safe_driver"],
        "hide": ["state", "suffix", "weight_range", "address2", "race", "is_real_id", "eye_color", "hair_color"],
        "showLoginWarning": True,
        "order": [
            "license_number", "first_name", "last_name", "middle_name",
            "address", "city", "zip_code", "license_class", "sex", "donor",
            "birth_date", "issue_date", "expiry_date", "document_discriminator", "audit_info",
            "restrictions", "endorsement", "height", "weight", "revision_date", "safe_driver",
        ],
        "defaults": {
            "license_number": "H655435851100",
            "first_name": "John",
            "last_name": "Doe",
            "address": "24944 SW 109THPATH",
            "city": "Homestead",
            "state": "FL",
            "zip_code": "330325131",
            "license_class": "C",
            "sex": "M",
            "donor": "No",
            "birth_date": "01151970",
            "issue_date": "08262021",
            "expiry_date": "01152028",
            "document_discriminator": "N322108265187",
            "audit_info": "0100385619573853",
            "restrictions": "NONE",
            "endorsement": "NONE",
            "height": "69",
            "weight": "169",
            "revision_date": "",
            "safe_driver": "Yes",
        },
    },
}


def load_counties() -> list[dict]:
    if not COUNTIES_PATH.exists():
        save_counties(DEFAULT_COUNTIES)
        return DEFAULT_COUNTIES
    counties = json.loads(COUNTIES_PATH.read_text(encoding="utf-8"))
    defaults_by_name = {item["name"]: item for item in DEFAULT_COUNTIES}
    changed = False
    for county in counties:
        default = defaults_by_name.get(county.get("name"))
        if default and default.get("template") and not county.get("template"):
            county["template"] = default["template"]
            changed = True
    if changed:
        save_counties(counties)
    return counties


def save_counties(counties: list[dict]) -> None:
    COUNTIES_PATH.write_text(json.dumps(counties, indent=2), encoding="utf-8")


def load_instructions() -> dict:
    if not INSTRUCTIONS_PATH.exists():
        save_instructions(DEFAULT_INSTRUCTIONS)
        return DEFAULT_INSTRUCTIONS
    saved = json.loads(INSTRUCTIONS_PATH.read_text(encoding="utf-8"))
    changed = False
    for template, fields in DEFAULT_INSTRUCTIONS.items():
        saved.setdefault(template, {})
        for field, message in fields.items():
            if field not in saved[template]:
                saved[template][field] = message
                changed = True
    if changed:
        save_instructions(saved)
    return saved


def save_instructions(instructions: dict) -> None:
    INSTRUCTIONS_PATH.write_text(json.dumps(instructions, indent=2), encoding="utf-8")


def load_templates() -> dict:
    if not TEMPLATES_PATH.exists():
        save_templates(DEFAULT_TEMPLATES)
        return DEFAULT_TEMPLATES
    saved = json.loads(TEMPLATES_PATH.read_text(encoding="utf-8"))
    changed = False
    for template, config in DEFAULT_TEMPLATES.items():
        if template not in saved:
            saved[template] = config
            changed = True
    if changed:
        save_templates(saved)
    return saved


def save_templates(templates: dict) -> None:
    TEMPLATES_PATH.write_text(json.dumps(templates, indent=2), encoding="utf-8")


@app.get("/")
def index():
    return render_template("landing.html", counties=load_counties())


@app.get("/studio")
def studio():
    county_name = request.args.get("county", "")
    county = next((item for item in load_counties() if item["name"] == county_name), {})
    return render_template(
        "index.html",
        county=county,
        county_name=county_name,
        instructions=load_instructions(),
        templates=load_templates(),
    )


@app.get("/counties")
def county_editor():
    return render_template("counties.html", counties=load_counties())


@app.post("/api/counties")
def api_save_counties():
    payload = request.get_json(silent=True) or {}
    counties = payload.get("counties", [])
    cleaned = []
    for county in counties:
        name = str(county.get("name", "")).strip()
        if not name:
            continue
        cleaned.append(
            {
                "name": name,
                "status": str(county.get("status", "")).strip(),
                "badge": str(county.get("badge", "")).strip(),
                "template": str(county.get("template", "")).strip(),
            }
        )
    save_counties(cleaned)
    return jsonify({"ok": True, "counties": cleaned})


@app.get("/instructions")
def instruction_editor():
    return render_template("instructions.html", instructions=load_instructions())


@app.post("/api/instructions")
def api_save_instructions():
    payload = request.get_json(silent=True) or {}
    instructions = payload.get("instructions", {})
    cleaned = {}
    for template, fields in instructions.items():
        template_name = str(template).strip()
        if not template_name:
            continue
        cleaned[template_name] = {}
        for field, message in fields.items():
            field_name = str(field).strip()
            if field_name:
                cleaned[template_name][field_name] = str(message).strip()
    save_instructions(cleaned)
    return jsonify({"ok": True, "instructions": cleaned})


@app.get("/templates")
def template_editor():
    return render_template("templates.html", templates=load_templates())


@app.post("/api/templates")
def api_save_templates():
    payload = request.get_json(silent=True) or {}
    templates = payload.get("templates", {})
    cleaned = {}
    for name, config in templates.items():
        template_name = str(name).strip()
        if template_name and isinstance(config, dict):
            cleaned[template_name] = config
    save_templates(cleaned)
    return jsonify({"ok": True, "templates": cleaned})


@app.post("/api/generate")
def generate():
    payload = request.get_json(silent=True) or {}
    fields = payload.get("fields", {})
    settings_payload = payload.get("settings", {})
    template = payload.get("template") or "standard"

    errors = validate_fields(fields, enforce_public_issue_window=(template == "standard"))
    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    encoded_text = fill_template(fields)
    try:
        settings = BarcodeSettings.from_payload(settings_payload)
    except ValueError as exc:
        return jsonify({"ok": False, "errors": [str(exc)]}), 400
    image = render_pdf417(encoded_text, settings)

    output_name = payload.get("filename") or "pdf417_barcode.png"
    if not output_name.lower().endswith(".png"):
        output_name += ".png"
    output_path = OUTPUT_DIR / Path(output_name).name
    image.save(output_path, "PNG")

    icn_value = str(fields.get("audit_info") or fields.get("icn") or "").strip()
    code128_path = OUTPUT_DIR / f"{output_path.stem}_code128.png"
    code128_error = None
    try:
        code128_image = render_code128(icn_value)
        code128_image.save(code128_path, "PNG")
    except Exception as exc:
        code128_error = str(exc)

    decoded_preview = None
    structured_preview = None
    try:
        decoded_preview = decode_pdf417(output_path)
        structured_preview = parse_aamva(decoded_preview)
    except Exception as exc:  # Decode can fail if native scanner tools are unavailable.
        decoded_preview = f"Decode preview unavailable: {exc}"

    return jsonify(
        {
            "ok": True,
            "encoded_text": encoded_text,
            "structured": parse_aamva(encoded_text),
            "decoded_preview": decoded_preview,
            "decoded_structured": structured_preview,
            "png_url": f"/download/png/{output_path.name}",
            "pdf_url": f"/download/pdf/{output_path.stem}.pdf",
            "code128_text": icn_value,
            "code128_error": code128_error,
            "code128_png_url": None if code128_error else f"/download/png/{code128_path.name}",
            "code128_pdf_url": None if code128_error else f"/download/pdf/{code128_path.stem}.pdf",
        }
    )


@app.post("/api/decode")
def decode():
    if "image" not in request.files:
        return jsonify({"ok": False, "errors": ["Upload an image file named 'image'."]}), 400

    uploaded = request.files["image"]
    data = uploaded.read()
    decoded_text = decode_pdf417(io.BytesIO(data))
    return jsonify({"ok": True, "decoded_text": decoded_text, "structured": parse_aamva(decoded_text)})


@app.get("/api/random-record")
def api_random_record():
    return jsonify({"ok": True, "fields": random_record()})


@app.get("/api/random-field/<field_name>")
def api_random_field(field_name: str):
    return jsonify({"ok": True, "field": field_name, "value": random_field(field_name)})


@app.post("/api/calculate")
def api_calculate():
    payload = request.get_json(silent=True) or {}
    fields = payload.get("fields", {})
    template = payload.get("template") or "standard"
    issue = fields.get("issue_date", "")
    expiry_instruction = load_instructions().get(template, {}).get("expiry_date", "")
    expiry = fields.get("expiry_date", "") or expiry_from_instruction(
        fields.get("birth_date", ""),
        issue,
        expiry_instruction,
    ) or expiry_from_issue(issue)
    license_number = fields.get("license_number", "")
    document_number = document_number_from_license(license_number)
    return jsonify(
        {
            "ok": True,
            "fields": {
                "expiry_date": expiry,
                "document_discriminator": calculate_dd(issue, expiry, document_number),
                "audit_info": calculate_icn(issue, license_number),
            },
        }
    )


@app.get("/download/png/<filename>")
def download_png(filename: str):
    path = OUTPUT_DIR / Path(filename).name
    return send_file(path, mimetype="image/png", as_attachment=True)


@app.get("/download/pdf/<filename>")
def download_pdf(filename: str):
    from barcode_studio.export import png_to_pdf

    stem = Path(filename).stem
    png_path = OUTPUT_DIR / f"{stem}.png"
    pdf_path = OUTPUT_DIR / f"{stem}.pdf"
    png_to_pdf(png_path, pdf_path)
    return send_file(pdf_path, mimetype="application/pdf", as_attachment=True)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
