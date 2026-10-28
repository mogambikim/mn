from __future__ import annotations

import random
from datetime import datetime


def compact_date(value: str) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def parse_mmddyyyy(value: str) -> datetime | None:
    digits = compact_date(value)
    if len(digits) != 8:
        return None
    try:
        return datetime.strptime(digits, "%m%d%Y")
    except ValueError:
        return None


def expiry_from_issue(issue: str, years: int = 5) -> str:
    parsed = parse_mmddyyyy(issue)
    if not parsed:
        return ""
    return f"{parsed.month:02d}{parsed.day:02d}{parsed.year + years:04d}"


def calculate_dd(issue: str, expiry: str, document_number: str | None = None) -> str:
    issue_date = parse_mmddyyyy(issue)
    expiry_date = parse_mmddyyyy(expiry)
    if not issue_date or not expiry_date:
        return ""
    doc = document_number or f"{random.randint(10000, 99999)}"
    return f"{issue_date:%m/%d/%Y}{doc}/AAFD/{expiry_date:%y}"


def calculate_icn(issue: str, license_number: str, document_number: str | None = None) -> str:
    issue_date = parse_mmddyyyy(issue)
    if not issue_date:
        return ""
    doc = document_number or license_number or f"{random.randint(10000000, 99999999)}"
    return f"{issue_date:%y}{issue_date.timetuple().tm_yday:03d}{doc.upper()}0401"


def document_number_from_license(license_number: str) -> str:
    digits = "".join(ch for ch in str(license_number or "") if ch.isdigit())
    if not digits:
        return ""
    return digits[-5:].rjust(5, "0")
