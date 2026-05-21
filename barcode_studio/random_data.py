from __future__ import annotations

import random
import string
from datetime import date, timedelta

from barcode_studio.calculations import calculate_dd, calculate_icn, expiry_from_issue


FIRST_NAMES = ["JOHN", "JAMES", "DAVID", "MICHAEL", "ROBERT", "MARIA", "LINDA", "SARAH", "EMILY", "ANNA"]
MIDDLE_NAMES = ["MARK", "LEE", "RAY", "ANN", "ROSE", "PAUL", "LYNN", "KAY"]
LAST_NAMES = ["DOE", "SMITH", "JOHNSON", "BROWN", "MILLER", "DAVIS", "WILSON", "MOORE"]
STREETS = ["516 ANSON CT", "123 MAIN STREET", "44 MARKET AVE", "908 CEDAR ROAD", "71 WASHINGTON ST"]
CITIES = ["DENVER", "RONHERT PARK", "AURORA", "LAKEWOOD", "BOULDER"]
EYES = ["BRO", "BLK", "BLU", "GRN", "HAZ", "GRY"]


def random_license_number() -> str:
    return random.choice(string.ascii_uppercase) + "".join(random.choice(string.digits) for _ in range(7))


def mmddyyyy(value: date) -> str:
    return value.strftime("%m%d%Y")


def random_issue_date() -> str:
    start = date(2025, 10, 20)
    today = date.today()
    if today < start:
        return mmddyyyy(start)
    span = (today - start).days
    return mmddyyyy(start + timedelta(days=random.randint(0, span)))


def random_birth_date() -> str:
    today = date.today()
    age_days = random.randint(18 * 365, 70 * 365)
    return mmddyyyy(today - timedelta(days=age_days))


def random_field(field_name: str) -> str:
    key = field_name.lower().strip()
    issue = random_issue_date()
    expiry = expiry_from_issue(issue)
    license_number = random_license_number()
    document_number = f"{random.randint(10000, 99999)}"
    values = {
        "license_number": random_license_number,
        "first_name": lambda: random.choice(FIRST_NAMES),
        "middle_name": lambda: random.choice(MIDDLE_NAMES),
        "last_name": lambda: random.choice(LAST_NAMES),
        "address": lambda: random.choice(STREETS),
        "city": lambda: random.choice(CITIES),
        "state": lambda: "CO",
        "zip_code": lambda: f"{random.randint(80000, 81699)}0000",
        "license_class": lambda: random.choice(["C", "D", "M"]),
        "sex": lambda: random.choice(["M", "F"]),
        "donor": lambda: random.choice(["YES", "NO"]),
        "birth_date": random_birth_date,
        "issue_date": lambda: issue,
        "expiry_date": lambda: expiry,
        "height": lambda: str(random.randint(58, 78)),
        "weight": lambda: str(random.randint(105, 240)),
        "eye_color": lambda: random.choice(EYES),
        "hair_color": lambda: random.choice(EYES),
        "document_discriminator": lambda: calculate_dd(issue, expiry, document_number),
        "audit_info": lambda: calculate_icn(issue, license_number, document_number),
        "restrictions": lambda: "NONE",
        "endorsement": lambda: "NONE",
        "suffix": lambda: "NONE",
        "country": lambda: "USA",
    }
    generator = values.get(key, lambda: "")
    return generator()


def random_record() -> dict[str, str]:
    issue = random_issue_date()
    expiry = expiry_from_issue(issue)
    license_number = random_license_number()
    document_number = f"{random.randint(10000, 99999)}"
    return {
        "license_number": license_number,
        "first_name": random.choice(FIRST_NAMES),
        "middle_name": random.choice(MIDDLE_NAMES),
        "last_name": random.choice(LAST_NAMES),
        "address": random.choice(STREETS),
        "city": random.choice(CITIES),
        "state": "CO",
        "zip_code": f"{random.randint(80000, 81699)}0000",
        "license_class": "C",
        "sex": random.choice(["M", "F"]),
        "donor": random.choice(["YES", "NO"]),
        "birth_date": random_birth_date(),
        "issue_date": issue,
        "expiry_date": expiry,
        "height": str(random.randint(58, 78)),
        "weight": str(random.randint(105, 240)),
        "eye_color": random.choice(EYES),
        "hair_color": "BRO",
        "document_discriminator": calculate_dd(issue, expiry, document_number),
        "audit_info": calculate_icn(issue, license_number, document_number),
        "restrictions": "NONE",
        "endorsement": "NONE",
        "suffix": "NONE",
        "country": "USA",
    }
