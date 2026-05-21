from barcode_studio.aamva import fill_template, parse_aamva, validate_fields


def sample_fields():
    return {
        "license_number": "A1234567",
        "first_name": "John",
        "middle_name": "Mark",
        "last_name": "Doe",
        "address": "123 Main Street",
        "city": "Denver",
        "state": "CO",
        "zip_code": "800120000",
        "license_class": "C",
        "sex": "M",
        "birth_date": "01011970",
        "issue_date": "10202025",
        "expiry_date": "10202030",
        "height": "69",
        "eye_color": "BRO",
        "country": "USA",
    }


def test_fill_template_replaces_name_fields():
    text = fill_template(sample_fields())

    assert "DACJOHN" in text
    assert "DADMARK" in text
    assert "DCSDOE" in text


def test_parse_aamva_reads_known_tags():
    parsed = parse_aamva(fill_template(sample_fields()))

    assert parsed["first_name"] == "JOHN"
    assert parsed["last_name"] == "DOE"
    assert parsed["license_number"] == "A1234567"


def test_validation_requires_letter_plus_seven_digit_license_number():
    fields = sample_fields()
    fields["license_number"] = "123"

    assert "DL number must match the selected county format." in validate_fields(fields)
