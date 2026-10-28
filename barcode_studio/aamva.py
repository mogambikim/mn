from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import re
from typing import Any
from xml.etree import ElementTree


SUPPORTED_AAMVA_VERSION = "09"
DATE_FIELDS = {"birth_date", "issue_date", "expiry_date"}

FIELD_LABELS = {
    "license_number": "DL number",
    "first_name": "First name",
    "last_name": "Last name",
    "address": "Address",
    "city": "City",
    "state": "State",
    "zip_code": "Zip code",
    "license_class": "DL class",
    "sex": "Sex",
    "birth_date": "Birth date",
    "issue_date": "Issue date",
    "expiry_date": "Expiry date",
    "height": "Height",
    "eye_color": "Eye color",
    "country": "Country",
}

REQUIRED_FIELDS = {
    "license_number",
    "first_name",
    "last_name",
    "address",
    "city",
    "state",
    "zip_code",
    "license_class",
    "sex",
    "birth_date",
    "issue_date",
    "expiry_date",
    "height",
    "eye_color",
    "country",
}

TAG_TO_FIELD = {
    "DAQ": "license_number",
    "DCF": "document_discriminator",
    "DBD": "issue_date",
    "DBB": "birth_date",
    "DBA": "expiry_date",
    "DAC": "first_name",
    "DAD": "middle_name",
    "DCS": "last_name",
    "DAU": "height",
    "DAW": "weight",
    "DBC": "sex",
    "DAY": "eye_color",
    "DAG": "address",
    "DAI": "city",
    "DAJ": "state",
    "DAK": "zip_code",
    "DCG": "country",
    "DCA": "license_class",
    "DDA": "compliance_type",
    "DDB": "card_revision_date",
    "DDK": "organ_donor",
    "DDE": "last_name_truncation",
    "DDF": "first_name_truncation",
    "DDG": "middle_name_truncation",
    "DCJ": "audit_info",
    "DCL": "race_ethnicity",
    "DCU": "suffix",
    "DCB": "restrictions",
    "DCD": "endorsement",
    "DDH": "limited_term",
    "DAZ": "hair_color",
    "DCK": "inventory_control_number",
}

FIELD_TO_TAG = {value: key for key, value in TAG_TO_FIELD.items()}
REQUIRED_TAGS = {"DAQ", "DCS", "DAC", "DBB", "DBA", "DBC", "DAU", "DAG", "DAI", "DAJ", "DAK"}
XML_USER_FIELDS = (
    ("last", "DCS", "last_name"),
    ("first", "DAC", "first_name"),
    ("middle", "DAD", "middle_name"),
    ("dob", "DBB", "birth_date"),
    ("eyes", "DAY", "eye_color"),
    ("sex", "DBC", "sex"),
    ("height", "DAU", "height"),
    ("weight", "DAW", "weight"),
    ("street", "DAG", "address"),
    ("city", "DAI", "city"),
    ("state", "DAJ", "state"),
    ("postal", "DAK", "zip_code"),
    ("country", "DCG", "country"),
    ("id", "DAQ", "license_number"),
    ("issued", "DBD", "issue_date"),
    ("expires", "DBA", "expiry_date"),
)


@dataclass(frozen=True)
class AamvaTemplate:
    jurisdiction: str = "636020"
    version: str = SUPPORTED_AAMVA_VERSION
    jurisdiction_version: str = "00"
    entries: str = "01"
    subfile_type: str = "DL"
    offset: str = "0031"
    length: str = "0242"

    def header(self) -> str:
        return (
            f"@\nANSI {self.jurisdiction}{self.version}"
            f"{self.jurisdiction_version}{self.entries}"
            f"{self.subfile_type}{self.offset}{self.length}"
        )


def normalize_date(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    compact = "".join(ch for ch in raw if ch.isdigit())
    if len(compact) == 8:
        return compact
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%m%d%Y")
        except ValueError:
            continue
    return raw


def normalize_height(value: Any) -> str:
    raw = str(value or "").strip().upper()
    if not raw:
        return ""
    feet_inches = re.fullmatch(
        r"(\d{1,2})\s*(?:FT|FEET|')\s*(\d{1,2})\s*(?:IN|INCH(?:ES)?|\")?",
        raw,
    )
    if feet_inches:
        feet, inches = (int(part) for part in feet_inches.groups())
        if inches < 12:
            return f"{feet * 12 + inches:03d} IN"
    digits = "".join(ch for ch in raw if ch.isdigit())
    if digits:
        return f"{int(digits):03d} IN"
    return raw


def normalize_sex(value: Any) -> str:
    raw = str(value or "").strip().upper()
    if raw in {"M", "MALE", "1"}:
        return "1"
    if raw in {"F", "FEMALE", "2"}:
        return "2"
    return raw


def normalize_text(value: Any) -> str:
    return str(value or "").strip().upper()


def validate_fields(
    fields: dict[str, Any],
    record_source: str = "test",
    required_fields: set[str] | list[str] | None = None,
    synthetic_id_prefix: str | None = None,
) -> list[str]:
    errors: list[str] = []
    for name, value in fields.items():
        if not isinstance(value, str):
            errors.append(f"{FIELD_LABELS.get(name, name)} must be provided as text.")
    for name in sorted(REQUIRED_FIELDS if required_fields is None else required_fields):
        if not str(fields.get(name, "")).strip():
            errors.append(f"{FIELD_LABELS.get(name, name)} is required.")

    license_number = str(fields.get("license_number", "")).strip()
    license_patterns = (
        r"[A-Za-z][0-9]{7}",
        r"[0-9]{7}",
        r"[A-Za-z][0-9]{12}",
        r"[0-9]{8}",
    )
    if record_source == "test" and license_number:
        if synthetic_id_prefix:
            if not re.fullmatch(re.escape(synthetic_id_prefix) + r"[A-F0-9]{8}", license_number):
                errors.append(f"Test DL number must use the {synthetic_id_prefix} synthetic prefix and 8 hex digits.")
        elif not any(re.fullmatch(pattern, license_number) for pattern in license_patterns):
            errors.append("DL number must match the selected county format.")

    for name in DATE_FIELDS:
        value = normalize_date(fields.get(name))
        if len(value) != 8 or not value.isdigit():
            errors.append(f"{FIELD_LABELS[name]} must be in MMDDYYYY format.")
        else:
            try:
                datetime.strptime(value, "%m%d%Y")
            except ValueError:
                errors.append(f"{FIELD_LABELS[name]} must be a valid calendar date.")

    issue_value = normalize_date(fields.get("issue_date"))
    try:
        issue_date = datetime.strptime(issue_value, "%m%d%Y").date()
        if record_source == "test" and (issue_date < date(2025, 10, 20) or issue_date > date.today()):
            errors.append("Issue date must be from 10/20/2025 through today.")
    except ValueError:
        pass
    return errors


def _record_values(fields: dict[str, Any]) -> dict[str, str]:
    values = {
        "DAQ": normalize_text(fields.get("license_number")),
        "DCF": normalize_text(fields.get("document_discriminator") or fields.get("dd") or ""),
        "DBD": normalize_date(fields.get("issue_date")),
        "DBB": normalize_date(fields.get("birth_date")),
        "DBA": normalize_date(fields.get("expiry_date")),
        "DAC": normalize_text(fields.get("first_name")),
        "DDF": normalize_text(fields.get("first_name_truncation")),
        "DAD": normalize_text(fields.get("middle_name")),
        "DDG": normalize_text(fields.get("middle_name_truncation")),
        "DCS": normalize_text(fields.get("last_name")),
        "DDE": normalize_text(fields.get("last_name_truncation")),
        "DAU": normalize_height(fields.get("height")),
        "DBC": normalize_sex(fields.get("sex")),
        "DAY": normalize_text(fields.get("eye_color")),
        "DAG": normalize_text(fields.get("address")),
        "DAI": normalize_text(fields.get("city")),
        "DAJ": normalize_text(fields.get("state")),
        "DAK": normalize_text(fields.get("zip_code")),
        "DCG": normalize_text(fields.get("country")),
        "DCA": normalize_text(fields.get("license_class")),
        "DCB": normalize_text(fields.get("restrictions")),
        "DCD": normalize_text(fields.get("endorsement")),
        "DCJ": normalize_text(fields.get("audit_info")),
        "DCU": normalize_text(fields.get("suffix")),
        "DAW": normalize_text(fields.get("weight")),
        "DCK": normalize_text(fields.get("inventory_control_number")),
        "DDA": normalize_text(fields.get("compliance_type")),
        "DDB": normalize_date(fields.get("card_revision_date")),
        "DDK": normalize_text(fields.get("organ_donor") or fields.get("donor")),
        "DAZ": normalize_text(fields.get("hair_color")),
    }

    for key, value in fields.items():
        tag = str(key)
        if re.fullmatch(r"[A-Z0-9]{3}", tag) and tag not in values:
            values[tag] = normalize_text(value)
    return {tag: value for tag, value in values.items() if value or tag in {"DAD", "DCB", "DCD"}}


def fill_template(fields: dict[str, Any], template: AamvaTemplate | None = None) -> str:
    tpl = template or AamvaTemplate()
    if tpl.version != SUPPORTED_AAMVA_VERSION:
        raise ValueError(f"Only AAMVA version {SUPPORTED_AAMVA_VERSION} is supported for generation.")
    if not re.fullmatch(r"\d{6}", tpl.jurisdiction):
        raise ValueError("Issuer identification number must contain six digits.")
    if not re.fullmatch(r"\d{2}", tpl.jurisdiction_version):
        raise ValueError("Jurisdiction version must contain two digits.")

    values = _record_values(fields)
    if not values:
        raise ValueError("At least one AAMVA field is required.")
    if any(any(char in value for char in "\r\n\x1c\x1d\x1e") for value in values.values()):
        raise ValueError("AAMVA field values cannot contain record or line delimiters.")
    try:
        content = ("\r\n".join(f"{tag}{value}" for tag, value in values.items()) + "\r\n").encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("AAMVA field values must contain ASCII characters only.") from exc

    offset = len(f"@\nANSI {tpl.jurisdiction}{tpl.version}{tpl.jurisdiction_version}01DL00000000".encode("ascii")) + 2
    if offset > 9999 or len(content) > 9999:
        raise ValueError("The AAMVA record exceeds the supported subfile length.")
    header = (
        f"@\nANSI {tpl.jurisdiction}{tpl.version}{tpl.jurisdiction_version}01"
        f"DL{offset:04d}{len(content):04d}"
    )
    return header + "\r\n" + content.decode("ascii")


def _extract_tag_values(data: bytes, designator: str) -> dict[str, str]:
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError("AAMVA fields must be ASCII text.") from exc
    result: dict[str, str] = {}
    for line in re.split(r"[\r\n\x1c\x1d\x1e]+", text):
        if not line:
            continue
        if designator == "ZW":
            result[line[:1]] = line[1:].lstrip()
            continue
        if len(line) < 3 or not re.fullmatch(r"[A-Z0-9]{3}", line[:3]):
            raise ValueError(f"Malformed AAMVA field line: {line[:20]!r}.")
        result[line[:3]] = line[3:]
    return result


def parse_aamva_record(text: str) -> dict[str, Any]:
    """Validate and parse the supported AAMVA DL/ID version 09 record structure."""
    raw = text.encode("utf-8")
    try:
        return _parse_aamva_record_bytes(raw)
    except ValueError as original_error:
        header = re.match(rb"@\r?\nANSI [0-9]{6}[0-9]{2}[0-9]{2}([0-9]{2})", raw)
        if not header:
            raise
        directory_length = int(header.group(1)) * 10
        directory_end = header.end() + directory_length
        body = raw[directory_end:]
        if b"\r" not in body and b"\n" in body:
            normalized = raw[:directory_end] + body.replace(b"\n", b"\r\n")
            try:
                record = _parse_aamva_record_bytes(normalized)
                record["transport_normalized"] = True
                return record
            except ValueError:
                pass
        raise original_error


def _parse_aamva_record_bytes(raw: bytes) -> dict[str, Any]:
    """Parse bytes after scanner transport normalization has been considered."""
    if not raw.startswith((b"@\nANSI ", b"@\r\nANSI ")):
        raise ValueError("PDF417 data was decoded, but it does not contain a supported AAMVA file header.")

    match = re.match(rb"@\r?\nANSI ([0-9]{6})([0-9]{2})([0-9]{2})([0-9]{2})", raw)
    if not match:
        raise ValueError("Malformed AAMVA ANSI header.")
    issuer, version, jurisdiction_version, entry_count = (
        part.decode("ascii") for part in match.groups()
    )
    if version != SUPPORTED_AAMVA_VERSION:
        raise ValueError(f"AAMVA version {version} is not supported; supported version is {SUPPORTED_AAMVA_VERSION}.")

    directory = raw[match.end():]
    directory_entries = re.match(rb"((?:[A-Z0-9]{2}[0-9]{8})+)", directory)
    if not directory_entries:
        raise ValueError("AAMVA header is missing its subfile directory.")
    directory_bytes = directory_entries.group(1)
    if len(directory_bytes) != int(entry_count) * 10:
        raise ValueError("AAMVA subfile entry count does not match the directory.")

    header_end = match.end() + len(directory_bytes)
    subfiles: list[dict[str, Any]] = []
    all_fields: dict[str, str] = {}
    seen_designators: set[str] = set()
    for index in range(int(entry_count)):
        entry = directory_bytes[index * 10:(index + 1) * 10]
        designator = entry[:2].decode("ascii")
        offset, length = int(entry[2:6]), int(entry[6:10])
        if (
            offset < header_end + 1
            or length <= 0
            or offset + length > len(raw)
            or designator in seen_designators
        ):
            raise ValueError(f"AAMVA {designator} subfile has an invalid offset or length.")
        seen_designators.add(designator)
        subfile_data = raw[offset:offset + length]
        fields = _extract_tag_values(subfile_data, designator)
        subfiles.append(
            {"designator": designator, "offset": offset, "length": length, "fields": fields}
        )
        all_fields.update(fields)
    ranges = sorted((item["offset"], item["offset"] + item["length"]) for item in subfiles)
    if any(current[0] < previous[1] for previous, current in zip(ranges, ranges[1:])):
        raise ValueError("AAMVA subfile offsets overlap.")

    missing_tags = sorted(
        tag for tag in REQUIRED_TAGS if not all_fields.get(tag, "").strip()
    )
    validation_errors = []
    if missing_tags:
        validation_errors.append(f"Required AAMVA elements are missing: {', '.join(missing_tags)}.")
    for tag in ("DBA", "DBB", "DBD", "DDB"):
        value = all_fields.get(tag, "")
        if not value:
            continue
        try:
            if not re.fullmatch(r"\d{8}", value):
                raise ValueError
            datetime.strptime(value, "%m%d%Y")
        except ValueError:
            validation_errors.append(f"{tag} must be a valid MMDDYYYY date.")
    return {
        "issuer_id": issuer,
        "version": version,
        "jurisdiction_version": jurisdiction_version,
        "entry_count": int(entry_count),
        "subfiles": subfiles,
        "raw_fields": all_fields,
        "fields": _map_field_values(all_fields),
        "is_aamva": True,
        "aamva_valid": not validation_errors,
        "validation_errors": validation_errors,
        "unsupported_fields": {
            tag: value for tag, value in all_fields.items() if tag not in TAG_TO_FIELD
        },
    }


def _map_field_values(raw_fields: dict[str, str]) -> dict[str, str]:
    parsed = {TAG_TO_FIELD.get(tag, tag): value.strip() for tag, value in raw_fields.items()}
    for field in DATE_FIELDS | {"card_revision_date"}:
        raw = parsed.get(field, "")
        if len(raw) == 8 and raw.isdigit():
            try:
                parsed[field] = datetime.strptime(raw, "%m%d%Y").strftime("%Y-%m-%d")
            except ValueError:
                pass
    if parsed.get("sex") in {"1", "2"}:
        parsed["sex"] = "M" if parsed["sex"] == "1" else "F"
    height = parsed.get("height", "")
    height_match = re.fullmatch(r"0*(\d{1,3})(?:\s*IN)?", height, re.IGNORECASE)
    if height_match:
        parsed["height"] = height_match.group(1)
    return parsed


def parse_aamva(text: str) -> dict[str, str]:
    if text.startswith("@\nANSI ") or text.startswith("@\r\nANSI "):
        record = parse_aamva_record(text)
        return record["fields"]
    parsed: dict[str, str] = {}
    for line in re.split(r"[\r\n\x1c\x1d\x1e]+", text):
        if len(line) < 3:
            continue
        tag = line[:3]
        if tag in TAG_TO_FIELD:
            parsed[TAG_TO_FIELD[tag]] = line[3:].strip()
    return parsed


def generate_xml(record: dict[str, Any], schema: list[dict[str, str]] | None = None) -> str:
    """Render decoded values in the application's AAMVA XML document shape."""
    root = ElementTree.Element("AAMVA")
    user = ElementTree.SubElement(root, "user")
    fields = record.get("fields", {})
    if schema is not None and (
        not isinstance(schema, list) or any(not isinstance(item, dict) for item in schema)
    ):
        raise ValueError("XML schema must be a JSON array of field mapping objects.")
    field_schema = schema if schema is not None else [
        {"element": element, "id": tag, "field": field}
        for element, tag, field in XML_USER_FIELDS
    ]
    for item in field_schema:
        element_name = item.get("element", "")
        tag = item.get("id", "")
        if not isinstance(element_name, str) or not isinstance(tag, str):
            raise ValueError("XML schema element names and field IDs must be strings.")
        field_name = item.get("field") or TAG_TO_FIELD.get(tag, tag)
        if not isinstance(field_name, str):
            raise ValueError("XML schema field keys must be strings.")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", element_name):
            raise ValueError(f"Invalid XML element name: {element_name!r}.")
        if not tag:
            raise ValueError("XML schema field IDs cannot be empty.")
        attributes = {"e": tag}
        label = item.get("name")
        if label is not None:
            if not isinstance(label, str):
                raise ValueError("XML schema field names must be strings.")
            attributes["name"] = label
        node = ElementTree.SubElement(user, element_name, attributes)
        value = fields.get(field_name, "")
        if value:
            node.text = _xml_user_value(field_name, str(value))
        else:
            node.set("missing", "true")

    head = ElementTree.SubElement(root, "head")
    header_values = (
        ("filetype", "File Type", "ANSI"),
        ("format", "Data Format", record.get("data_format", "11")),
        ("issuer", "Issuer Identification Number", record.get("issuer_id", "")),
        ("state", "Issuer Name", record.get("issuer_name", "")),
        ("st", "Issuer Name Abbreviated", record.get("issuer_abbreviation", "")),
        ("version", "AAMVA Version Number", record.get("version", "")),
        ("jurver", "Jurisdiction Version Number", record.get("jurisdiction_version", "")),
        ("entries", "Number of Entries", f"{record.get('entry_count', 0):02d}"),
    )
    for name, label, value in header_values:
        attributes = {"name": label}
        if not value:
            attributes["missing"] = "true"
        ElementTree.SubElement(head, name, attributes).text = str(value)

    for subfile in record.get("subfiles", []):
        node = ElementTree.SubElement(
            root,
            "subfile",
            {
                "designator": subfile["designator"],
                "offset": str(subfile["offset"]),
                "length": str(subfile["length"]),
            },
        )
        for tag, value in subfile["fields"].items():
            element = ElementTree.SubElement(
                node, "element", {"id": tag, "name": _field_label(tag)}
            )
            element.text = value
    ElementTree.indent(root, space="  ")
    return ElementTree.tostring(root, encoding="unicode", xml_declaration=False)


def _xml_user_value(field_name: str, value: str) -> str:
    if field_name in {"last_name", "first_name", "middle_name", "address", "city"}:
        return value.title()
    if field_name == "height":
        match = re.fullmatch(r"(\d{1,3})(?:\s*(?:IN|in|inches))?", value)
        if match:
            inches = int(match.group(1))
            feet, remaining_inches = divmod(inches, 12)
            return f"{feet}'{remaining_inches}\""
    return value


def _field_label(tag: str) -> str:
    labels = {
        "DAQ": "Customer ID Number",
        "DCS": "Customer Family Name",
        "DAC": "Driver First Name",
        "DAD": "Driver Middle Name or Initial",
        "DBB": "Date of Birth",
        "DBD": "Document Issue Date",
        "DBA": "Document Expiration Date",
        "DBC": "Physical Description - Sex",
        "DAU": "Physical Description - Height",
        "DAW": "Physical Description - Weight",
        "DAY": "Physical Description - Eye Color",
        "DAG": "Address - Street 1",
        "DAI": "Address - City",
        "DAJ": "Address - Jurisdiction Code",
        "DAK": "Address - Postal Code",
        "DCG": "Country Identification",
        "DCA": "Jurisdiction-specific vehicle class",
        "DCB": "Jurisdiction-specific restriction codes",
        "DCD": "Jurisdiction-specific endorsement codes",
        "DCF": "Document Discriminator",
        "DCK": "Inventory control number",
        "DDA": "Compliance Type",
        "DDB": "Card Revision Date",
        "DDE": "Family name truncation",
        "DDF": "First name truncation",
        "DDG": "Middle name truncation",
        "A": "Optional field A",
        "B": "Optional field B",
        "C": "Optional field C",
        "D": "Optional field D",
        "E": "Optional field E",
    }
    return labels.get(tag, "Unsupported field")
