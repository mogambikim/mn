from __future__ import annotations

import random
import re
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


def instruction_years(message: str) -> int | None:
    lower = str(message or "").lower()
    numeric_match = re.search(r"(\d+)\s+years?", lower)
    if numeric_match:
        return int(numeric_match.group(1))
    number_words = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
    }
    word_match = re.search(r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+years?\b", lower)
    return number_words[word_match.group(1)] if word_match else None


def expiry_from_instruction(birth: str, issue: str, instruction: str) -> str:
    lower = str(instruction or "").lower()
    years = instruction_years(lower)
    if years is None:
        return ""

    birth_digits = compact_date(birth)
    issue_digits = compact_date(issue)
    mentions_birth = bool(re.search(r"\bbirth\s*date\b|\bbirthdate\b|\bbirthday\b", lower))
    mentions_issue = bool(re.search(r"\bissue(d)?\b", lower))
    month_day_source = birth_digits if mentions_birth and len(birth_digits) == 8 else issue_digits
    year_source = issue_digits if mentions_issue and len(issue_digits) == 8 else month_day_source

    if len(month_day_source) != 8 or len(year_source) != 8:
        return ""
    return f"{month_day_source[:4]}{int(year_source[4:8]) + years:04d}"


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
