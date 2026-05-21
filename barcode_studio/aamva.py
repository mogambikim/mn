from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import re
from typing import Any


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
    "DBC": "sex",
    "DAY": "eye_color",
    "DAG": "address",
    "DAI": "city",
    "DAJ": "state",
    "DAK": "zip_code",
    "DCG": "country",
    "DCA": "license_class",
    "DDB": "donor",
    "DDE": "last_name_truncation",
    "DDF": "first_name_truncation",
    "DDG": "middle_name_truncation",
    "DCJ": "audit_info",
    "DCL": "race_ethnicity",
    "DCU": "suffix",
    "DCB": "restrictions",
    "DCD": "endorsement",
    "DDH": "limited_term",
    "DAW": "weight",
    "DAZ": "hair_color",
}


@dataclass(frozen=True)
class AamvaTemplate:
    jurisdiction: str = "636020"
    version: str = "09"
    jurisdiction_version: str = "00"
    entries: str = "01"
    subfile_type: str = "DL"
    offset: str = "0031"
    length: str = "0242"

    def header(self) -> str:
        return (
            f"@\nANSI {self.jurisdiction}{self.version}"
            f"{self.jurisdiction_version}{self.entries}"
            f"{self.subfile_type}{self.offset}{self.length}DL"
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
    return raw or "1"


def normalize_text(value: Any) -> str:
    return str(value or "").strip().upper()


def validate_fields(fields: dict[str, Any], enforce_public_issue_window: bool = True) -> list[str]:
    errors: list[str] = []
    for name in sorted(REQUIRED_FIELDS):
        if not str(fields.get(name, "")).strip():
            errors.append(f"{FIELD_LABELS.get(name, name)} is required.")

    license_number = str(fields.get("license_number", "")).strip()
    license_patterns = (
        r"[A-Za-z][0-9]{7}",
        r"[0-9]{7}",
        r"[A-Za-z][0-9]{12}",
        r"[0-9]{8}",
    )
    if license_number and not any(re.fullmatch(pattern, license_number) for pattern in license_patterns):
        errors.append("DL number must match the selected county format.")

    for name in DATE_FIELDS:
        value = normalize_date(fields.get(name))
        if len(value) != 8 or not value.isdigit():
            errors.append(f"{FIELD_LABELS[name]} must be in MMDDYYYY format.")

    if enforce_public_issue_window:
        issue_value = normalize_date(fields.get("issue_date"))
        try:
            issue_date = datetime.strptime(issue_value, "%m%d%Y").date()
            if issue_date < date(2025, 10, 20) or issue_date > date.today():
                errors.append("Issue date must be from 10/20/2025 through today.")
        except ValueError:
            pass
    return errors


def fill_template(fields: dict[str, Any], template: AamvaTemplate | None = None) -> str:
    tpl = template or AamvaTemplate()
    middle_name = normalize_text(fields.get("middle_name"))
    suffix = normalize_text(fields.get("suffix") or "NONE")

    lines = [
        tpl.header(),
        f"DAQ{normalize_text(fields.get('license_number'))}",
        f"DCF{normalize_text(fields.get('document_discriminator') or fields.get('dd') or '1234567')}",
        f"DBD{normalize_date(fields.get('issue_date'))}",
        f"DBB{normalize_date(fields.get('birth_date'))}",
        f"DBA{normalize_date(fields.get('expiry_date'))}",
        f"DAC{normalize_text(fields.get('first_name'))}",
        "DDFN",
        f"DAD{middle_name}" if middle_name else "DAD",
        "DDGN",
        f"DCS{normalize_text(fields.get('last_name'))}",
        "DDEN",
        f"DAU{normalize_height(fields.get('height'))}",
        f"DBC{normalize_sex(fields.get('sex'))}",
        f"DAY{normalize_text(fields.get('eye_color'))[:3] or 'BRO'}",
        f"DAG{normalize_text(fields.get('address'))}",
        f"DAI{normalize_text(fields.get('city'))}",
        f"DAJ{normalize_text(fields.get('state'))}",
        f"DAK{normalize_text(fields.get('zip_code'))}",
        f"DCG{normalize_text(fields.get('country') or 'USA')}",
        f"DCA{normalize_text(fields.get('license_class') or 'C')}",
        f"DCB{normalize_text(fields.get('restrictions') or 'NONE')}",
        f"DCD{normalize_text(fields.get('endorsement') or 'NONE')}",
        f"DDB{normalize_text(fields.get('donor') or 'NO')}",
        f"DCJ{normalize_text(fields.get('audit_info') or 'CODL_0_082418_04105')}",
        f"DCU{'' if suffix == 'NONE' else suffix}",
    ]
    return "\n".join(lines)


def parse_aamva(text: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if len(line) < 3:
            continue
        tag = line[:3]
        if tag in TAG_TO_FIELD:
            parsed[TAG_TO_FIELD[tag]] = line[3:]
    return parsed
